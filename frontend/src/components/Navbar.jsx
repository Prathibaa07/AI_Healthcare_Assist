import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Stethoscope, Menu, X, Globe } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const [isOpen, setIsOpen] = React.useState(false);

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'en' ? 'ta' : i18n.language === 'ta' ? 'hi' : 'en';
    i18n.changeLanguage(nextLang);
  };

  const navLinks = [
    { path: '/', label: t('Home') },
    { path: '/chatbot', label: t('Chatbot') },
    { path: '/hospitals', label: t('Hospitals') },
    { path: '/awareness', label: t('Health Awareness') },
  ];

  return (
    <nav className="navbar glass-panel">
      <div className="container nav-container">
        <Link to="/" className="nav-logo">
          <Stethoscope className="logo-icon" />
          <span>AI Health Assist</span>
        </Link>
        
        <div className="nav-links desktop-only">
          {navLinks.map((link) => (
            <Link 
              key={link.path} 
              to={link.path} 
              className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
          <button onClick={toggleLanguage} className="lang-btn" title="Change Language">
            <Globe size={20} />
            <span className="lang-text">{i18n.language.toUpperCase()}</span>
          </button>
        </div>

        <button className="mobile-menu-btn mobile-only" onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <X /> : <Menu />}
        </button>
      </div>

      {isOpen && (
        <div className="mobile-menu animate-fade-in">
          {navLinks.map((link) => (
            <Link 
              key={link.path} 
              to={link.path} 
              className="mobile-nav-link"
              onClick={() => setIsOpen(false)}
            >
              {link.label}
            </Link>
          ))}
           <button onClick={toggleLanguage} className="lang-btn-mobile">
            <Globe size={20} /> {i18n.language.toUpperCase()}
          </button>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
