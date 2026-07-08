import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Activity } from 'lucide-react';
import './Home.css';

const Home = () => {
  const { t } = useTranslation();

  return (
    <div className="home-container animate-fade-in">
      <section className="hero-section">
        <div className="hero-content">
          <Activity className="hero-icon" size={64} />
          <h1>{t('Welcome to AI Health Assist')}</h1>
          <p className="hero-subtitle">{t('Your intelligent healthcare companion.')}</p>
          
          <div className="hero-actions">
            <Link to="/chatbot" className="btn btn-primary btn-large">
              {t('Get Started')}
            </Link>
          </div>
        </div>
      </section>
      
      <section className="features-section container">
        <div className="feature-card glass-panel">
          <h3>AI Chatbot</h3>
          <p>Describe your symptoms and receive instant medical specialist recommendations to guide you on the right path.</p>
        </div>
        <div className="feature-card glass-panel">
          <h3>Voice & Speech Support</h3>
          <p>Interact hands-free using voice commands and listen to spoken advice, making healthcare accessible for everyone.</p>
        </div>
        <div className="feature-card glass-panel">
          <h3>Emergency Detection</h3>
          <p>Our system actively monitors for critical symptoms like chest pain or breathing issues and alerts you immediately.</p>
        </div>
      </section>
    </div>
  );
};

export default Home;
