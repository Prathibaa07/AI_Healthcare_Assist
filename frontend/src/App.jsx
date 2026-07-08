import React, { Suspense } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Chatbot from './pages/Chatbot';
import Hospitals from './pages/Hospitals';
import HealthAwareness from './pages/HealthAwareness';
import './i18n';

function App() {
  return (
    <Router>
      <Suspense fallback={<div className="loading-container">Loading...</div>}>
        <div className="app-container">
          <Navbar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/chatbot" element={<Chatbot />} />
              <Route path="/hospitals" element={<Hospitals />} />
              <Route path="/awareness" element={<HealthAwareness />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Suspense>
    </Router>
  );
}

export default App;
