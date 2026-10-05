# Ration Mandi AI

**Know before you go.** — A modern, mobile-first civic-tech web application for government ration-shop monitoring and citizen assistance.

## Features

### Citizen Dashboard
- Find nearby ration shops with distance filters
- Live stock status (Rice, Wheat, Dal, Sugar)
- Current queue length and estimated wait time
- AI predictions: expected queue, stock-out risk, recommended visit time
- Best-time recommendation card with directions link
- Fully mobile-first, large touch targets, readable status indicators

### Shopkeeper / Admin Dashboard
- Simple login by Shop ID (demo)
- Update stock levels (Available / Low / Out of Stock)
- Update queue level and approximate headcount
- Instant reflection on citizen views (in-memory mock store)
- AI Admin Analytics with charts (peak hours, consumption, predictions)

### Architecture
- React + Vite + Tailwind CSS v4
- React Router for navigation
- Recharts for analytics charts
- Lucide React icons
- **Clean API service layer** (`src/services/api.js`) ready for Python FastAPI/Flask ML backend

### Mock API Endpoints (replace with real backend)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/shops` | List / filter shops |
| GET | `/api/shops/:id` | Shop details |
| POST | `/api/shop/update-status` | Shopkeeper update |
| POST | `/api/predict/queue` | Queue prediction |
| POST | `/api/predict/stock` | Stock-out prediction |
| POST | `/api/recommend/time` | Best visit time |
| GET | `/api/analytics` | Admin analytics |

## Getting Started

```bash
cd ration-mandi-ai
npm install
npm run dev
```

Open http://localhost:5173

## Demo Mode
- Sample shops with realistic stock & queue data
- "Simulate live change" button on shop details
- Shopkeeper updates mutate the in-memory store so citizen screens update immediately
- Labelled "Demo Data" throughout

## Future AI Integration
Citizen → Frontend → REST API → Python FastAPI → ML models (queue, stock, demand, best-time) → JSON → Frontend

Do not train models in the browser. All prediction calls go through the API service layer.

## Design
- Clean white background, green primary actions
- Subtle saffron / government-blue accents
- Rounded cards, high contrast, large text
- Trustworthy civic-tech aesthetic for rural & low-income users
