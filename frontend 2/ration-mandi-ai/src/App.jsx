import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Shops from './pages/Shops';
import ShopDetails from './pages/ShopDetails';
import Predictions from './pages/Predictions';
import About from './pages/About';
import Shopkeeper from './pages/Shopkeeper';
import Analytics from './pages/Analytics';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-slate-50">
        <Navbar />
        <main className="flex-1 pb-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/shops" element={<Shops />} />
            <Route path="/shop/:shopId" element={<ShopDetails />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/about" element={<About />} />
            <Route path="/shopkeeper" element={<Shopkeeper />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
          Ration Mandi AI · Civic Tech Prototype · Demo Data
        </footer>
      </div>
    </BrowserRouter>
  );
}
