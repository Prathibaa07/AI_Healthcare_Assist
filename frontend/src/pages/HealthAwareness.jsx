import React from 'react';
import { useTranslation } from 'react-i18next';
import { Heart, Droplets, Apple, Sun, Activity, ShieldCheck } from 'lucide-react';
import './HealthAwareness.css';

const HealthAwareness = () => {
  const { t } = useTranslation();

  const articles = [
    {
      id: 1,
      title: 'The Importance of Hydration',
      icon: <Droplets size={32} color="#3B82F6" />,
      content: 'Drinking enough water every day is crucial for many reasons: to regulate body temperature, keep joints lubricated, prevent infections, deliver nutrients to cells, and keep organs functioning properly.',
      category: 'Nutrition'
    },
    {
      id: 2,
      title: 'Heart Health Essentials',
      icon: <Heart size={32} color="#EF4444" />,
      content: 'Maintain a healthy heart by managing your blood pressure, controlling cholesterol levels, engaging in regular physical activity, and eating a heart-healthy diet low in saturated fats.',
      category: 'Cardiology'
    },
    {
      id: 3,
      title: 'Benefits of a Balanced Diet',
      icon: <Apple size={32} color="#10B981" />,
      content: 'A balanced diet supplies the nutrients your body needs to work effectively. Without balanced nutrition, your body is more prone to disease, infection, fatigue, and low performance.',
      category: 'Diet'
    },
    {
      id: 4,
      title: 'Vitamin D and Sunlight',
      icon: <Sun size={32} color="#F59E0B" />,
      content: 'Vitamin D is vital for bone health and immune function. Safe sun exposure for 10-30 minutes several times a week can help your body produce adequate levels naturally.',
      category: 'Wellness'
    },
    {
      id: 5,
      title: 'Daily Physical Activity',
      icon: <Activity size={32} color="#8B5CF6" />,
      content: 'Engaging in at least 30 minutes of moderate physical activity every day can significantly improve your cardiovascular health and boost your overall mood.',
      category: 'Fitness'
    },
    {
      id: 6,
      title: 'Boost Your Immune System',
      icon: <ShieldCheck size={32} color="#14B8A6" />,
      content: 'Adequate sleep, a diet rich in fruits and vegetables, regular exercise, and minimizing stress are key factors in maintaining a robust immune system.',
      category: 'Immunity'
    }
  ];

  return (
    <div className="page-container container animate-fade-in">
      <div className="page-header">
        <h2>{t('Health Awareness')}</h2>
        <p>Essential tips and articles for a healthier lifestyle</p>
      </div>

      <div className="awareness-grid">
        {articles.map((article) => (
          <div key={article.id} className="article-card glass-panel">
            <div className="article-header">
              <div className="icon-wrapper">
                {article.icon}
              </div>
              <span className="category-badge">{article.category}</span>
            </div>
            <h3>{article.title}</h3>
            <p>{article.content}</p>
            <button className="read-more-btn">Read More</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HealthAwareness;
