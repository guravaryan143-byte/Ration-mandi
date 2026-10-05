/**
 * API Service Layer for Ration Mandi AI
 * -------------------------------------
 * All frontend data access goes through this module.
 * Currently uses in-memory mock data so the app works offline.
 * Replace the implementations with real fetch() calls to a
 * Python FastAPI/Flask backend when ready.
 *
 * Planned backend endpoints:
 *   GET  /api/shops
 *   GET  /api/shops/{shopId}
 *   POST /api/shop/update-status
 *   POST /api/predict/queue
 *   POST /api/predict/stock
 *   POST /api/recommend/time
 */

import { initialShops, analyticsData } from '../data/mockData';

// In-memory store (simulates a live backend)
let shops = JSON.parse(JSON.stringify(initialShops));
let lastUpdateTimestamps = {};

// Helper: human-readable relative time
function relativeTime(minutesAgo = 0) {
  if (minutesAgo < 1) return 'Just now';
  if (minutesAgo === 1) return '1 minute ago';
  return `${minutesAgo} minutes ago`;
}

// Simulate network latency
const delay = (ms = 300) => new Promise((r) => setTimeout(r, ms));

/**
 * GET /api/shops
 * Optional filters: area, maxDistance
 */
export async function getShops({ area = 'All Areas', maxDistance = 10 } = {}) {
  await delay(250);
  let result = [...shops];
  if (area && area !== 'All Areas') {
    result = result.filter((s) => s.area === area);
  }
  result = result.filter((s) => s.distanceKm <= maxDistance);
  // Sort by distance
  result.sort((a, b) => a.distanceKm - b.distanceKm);
  return { success: true, data: result };
}

/**
 * GET /api/shops/{shopId}
 */
export async function getShopById(shopId) {
  await delay(200);
  const shop = shops.find((s) => s.shopId === Number(shopId));
  if (!shop) {
    return { success: false, error: 'Shop not found' };
  }
  return { success: true, data: shop };
}

/**
 * POST /api/shop/update-status
 * Body: { shopId, stock, queue, queueLevel }
 */
export async function updateShopStatus({ shopId, stock, queue, queueLevel }) {
  await delay(400);
  const idx = shops.findIndex((s) => s.shopId === Number(shopId));
  if (idx === -1) {
    return { success: false, error: 'Shop not found' };
  }
  const shop = shops[idx];
  if (stock) {
    shop.stock = { ...shop.stock, ...stock };
  }
  if (typeof queue === 'number') {
    shop.queue = queue;
  }
  if (queueLevel) {
    shop.queueLevel = queueLevel;
  }
  shop.lastUpdated = relativeTime(0);
  lastUpdateTimestamps[shopId] = Date.now();

  // Simple AI re-calc based on new numbers (mock)
  shop.aiPrediction = generateMockPrediction(shop);

  shops[idx] = { ...shop };
  return { success: true, data: shop, message: 'Status updated successfully.' };
}

/**
 * POST /api/predict/queue
 * Body: { shopId, targetTime? }
 */
export async function predictQueue({ shopId, targetTime }) {
  await delay(350);
  const shop = shops.find((s) => s.shopId === Number(shopId));
  if (!shop) return { success: false, error: 'Shop not found' };

  // Mock response shaped like a real ML service would return
  return {
    success: true,
    data: {
      shopId,
      predictedQueue: shop.aiPrediction.nextHourQueue,
      range: `${shop.aiPrediction.nextHourQueue - 4}–${shop.aiPrediction.nextHourQueue + 5}`,
      atTime: targetTime || 'next hour',
      confidence: 0.78,
    },
  };
}

/**
 * POST /api/predict/stock
 * Body: { shopId }
 */
export async function predictStock({ shopId }) {
  await delay(350);
  const shop = shops.find((s) => s.shopId === Number(shopId));
  if (!shop) return { success: false, error: 'Shop not found' };

  return {
    success: true,
    data: {
      shopId,
      risk: shop.aiPrediction.stockOutRisk,
      item: shop.aiPrediction.stockOutItem,
      hoursRemaining: shop.aiPrediction.stockOutHours,
      message: shop.aiPrediction.stockOutItem
        ? `${capitalize(shop.aiPrediction.stockOutItem)} may run low within approximately ${shop.aiPrediction.stockOutHours} hours.`
        : 'No significant stock-out risk in the next few hours.',
    },
  };
}

/**
 * POST /api/recommend/time
 * Body: { shopId }
 */
export async function recommendVisitTime({ shopId }) {
  await delay(300);
  const shop = shops.find((s) => s.shopId === Number(shopId));
  if (!shop) return { success: false, error: 'Shop not found' };

  return {
    success: true,
    data: {
      shopId,
      recommendedTime: shop.aiPrediction.recommendedTime,
      expectedQueue: shop.aiPrediction.recommendedQueue,
      expectedWait: shop.aiPrediction.recommendedWait,
      expectedStock: 'Available',
      reason: 'Based on historical demand patterns and current stock levels.',
    },
  };
}

/**
 * GET /api/analytics (admin)
 */
export async function getAnalytics() {
  await delay(300);
  return { success: true, data: analyticsData };
}

/**
 * Demo helper: simulate live changes (queue up / stock down)
 */
export async function simulateLiveChange(shopId) {
  const idx = shops.findIndex((s) => s.shopId === Number(shopId));
  if (idx === -1) return { success: false };

  const shop = { ...shops[idx] };
  // Randomly increase queue a bit
  const delta = Math.floor(Math.random() * 5) + 1;
  shop.queue = Math.min(shop.queue + delta, 60);
  shop.queueLevel =
    shop.queue <= 12 ? 'low' : shop.queue <= 30 ? 'medium' : 'high';
  shop.lastUpdated = relativeTime(0);

  // Occasionally lower stock
  const items = Object.keys(shop.stock);
  if (Math.random() > 0.6) {
    const item = items[Math.floor(Math.random() * items.length)];
    if (shop.stock[item] === 'available') shop.stock[item] = 'low';
    else if (shop.stock[item] === 'low') shop.stock[item] = 'out_of_stock';
  }

  shop.aiPrediction = generateMockPrediction(shop);
  shops[idx] = shop;
  return { success: true, data: shop };
}

/** Reset all shops to original mock state */
export function resetDemoData() {
  shops = JSON.parse(JSON.stringify(initialShops));
  return { success: true };
}

// ── Internal helpers ──────────────────────────────────────────

function generateMockPrediction(shop) {
  const base = shop.queue;
  const nextHour = Math.min(base + Math.floor(Math.random() * 12) + 2, 55);
  const risk =
    Object.values(shop.stock).includes('out_of_stock') ||
    Object.values(shop.stock).filter((v) => v === 'low').length >= 2
      ? 'high'
      : Object.values(shop.stock).includes('low')
        ? 'medium'
        : 'low';

  const lowItem = Object.entries(shop.stock).find(([, v]) => v === 'low' || v === 'out_of_stock');

  return {
    nextHourQueue: nextHour,
    expectedQueueAt5PM: `${nextHour - 3}–${nextHour + 6}`,
    stockOutRisk: risk,
    stockOutItem: lowItem ? lowItem[0] : null,
    stockOutHours: risk === 'high' ? 1.5 : risk === 'medium' ? 3 : null,
    recommendedTime: shop.queueLevel === 'high' ? '7:00 PM – 7:30 PM' : 'Now – next 30 min',
    recommendedQueue: shop.queueLevel === 'high' ? 'low' : 'low',
    recommendedWait: shop.queueLevel === 'high' ? '10–15 minutes' : '5–12 minutes',
  };
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}
