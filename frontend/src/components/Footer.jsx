import React from 'react';

const Footer = () => {
  return (
    <footer style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary-light)', marginTop: 'auto' }}>
      <p>&copy; {new Date().getFullYear()} AI Health Assist. All rights reserved.</p>
    </footer>
  );
};

export default Footer;
