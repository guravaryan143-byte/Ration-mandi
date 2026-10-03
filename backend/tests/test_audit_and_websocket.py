def test_audit_history_records_old_and_new_values(client, owner, create_location):
    shop = create_location(owner)
    client.put(f"/api/ration-shops/{shop['id']}/stock", json={"dal": "OUT_OF_STOCK", "queue_level": "HIGH", "note": "rush"}, headers=owner)
    client.post(f"/api/owner/locations/{shop['id']}/update-status", json={"status": "CLOSED"}, headers=owner)

    res = client.get(f"/api/owner/locations/{shop['id']}/updates", headers=owner)
    assert res.status_code == 200
    rows = res.json()["data"]
    me = client.get("/api/auth/me", headers=owner).json()["data"]
    by_field = {r["field_name"]: r for r in rows}
    assert by_field["stock.dal"]["previous_value"] == "AVAILABLE" and by_field["stock.dal"]["new_value"] == "OUT_OF_STOCK"
    assert by_field["queue_level"]["previous_value"] == "NOT_APPLICABLE" and by_field["queue_level"]["new_value"] == "HIGH"
    assert by_field["status"]["new_value"] == "CLOSED"
    assert all(r["location_id"] == shop["id"] and r["created_at"] for r in rows)
    owner_rows = [r for r in rows if r["update_type"] != "MODERATION"]  # admin approval is logged too
    assert owner_rows and all(r["updated_by"] == me["id"] for r in owner_rows)
    assert by_field["approval_status"]["previous_value"] == "PENDING" and by_field["approval_status"]["new_value"] == "APPROVED"
    assert by_field["queue_level"]["note"] == "rush"
    assert rows[0]["id"] > rows[-1]["id"]  # newest first
    assert rows[-1]["update_type"] == "CREATED"  # oldest entry


def test_unchanged_values_are_not_audited(client, owner, create_location):
    shop = create_location(owner)
    before = client.get(f"/api/owner/locations/{shop['id']}/updates", headers=owner).json()["meta"]["total"]
    client.put(f"/api/ration-shops/{shop['id']}/stock", json={"rice": "AVAILABLE"}, headers=owner)
    after = client.get(f"/api/owner/locations/{shop['id']}/updates", headers=owner).json()["meta"]["total"]
    assert before == after


def test_websocket_receives_snapshot_and_updates(client, owner, create_location):
    shop = create_location(owner)
    with client.websocket_connect(f"/ws/locations/{shop['id']}") as ws:
        snapshot = ws.receive_json()
        assert snapshot["event"] == "snapshot" and snapshot["data"]["queue_level"] == "NOT_APPLICABLE"

        assert client.put(f"/api/ration-shops/{shop['id']}/status", json={"queue_level": "HIGH", "status": "BUSY"}, headers=owner).status_code == 200
        msg = ws.receive_json()
        assert msg["event"] == "location_update" and msg["location_id"] == shop["id"]
        assert msg["data"]["queue_level"] == "HIGH" and msg["data"]["status"] == "BUSY"

        client.put(f"/api/ration-shops/{shop['id']}/stock", json={"rice": "OUT_OF_STOCK"}, headers=owner)
        assert ws.receive_json()["data"]["ration_stock"]["rice"] == "OUT_OF_STOCK"
        ws.send_text("ping")
        assert ws.receive_json() == {"event": "pong"}


def test_websocket_ev_and_pharmacy_updates_and_isolation(client, owner, create_location):
    ev = create_location(owner, category="EV_CHARGING", ev_station={"total_plugs": 3})
    other = create_location(owner, name="Other")
    with client.websocket_connect(f"/ws/locations/{ev['id']}") as ws, client.websocket_connect(f"/ws/locations/{other['id']}") as ws_other:
        ws.receive_json()
        ws_other.receive_json()
        client.put(f"/api/ev-stations/{ev['id']}/availability", json={"occupied_plugs": 3}, headers=owner)
        msg = ws.receive_json()
        assert msg["data"]["ev_station"]["available_plugs"] == 0
        # the other location's channel got nothing: its next message is the reply to our ping
        ws_other.send_text("ping")
        assert ws_other.receive_json() == {"event": "pong"}


def test_websocket_unknown_or_unapproved_location_rejected(client, owner, create_location):
    import pytest
    from starlette.websockets import WebSocketDisconnect

    pending = create_location(owner, approve=False)
    for location_id in (9999, pending["id"]):
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(f"/ws/locations/{location_id}"):
                pass
        assert exc.value.code == 4404
