import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// In a real application, you might load these asynchronously or use a translation service API
const resources = {
  en: {
    translation: {
      "Welcome to AI Health Assist": "Welcome to AI Health Assist",
      "Your intelligent healthcare companion.": "Your intelligent healthcare companion.",
      "Get Started": "Get Started",
      "Home": "Home",
      "Chatbot": "Chatbot",
      "Hospitals": "Hospitals",
      "Health Awareness": "Health Awareness",
    }
  },
  ta: {
    translation: {
      "Welcome to AI Health Assist": "AI சுகாதார உதவிக்கு வருக",
      "Your intelligent healthcare companion.": "உங்கள் அறிவார்ந்த சுகாதார துணை.",
      "Get Started": "தொடங்குங்கள்",
      "Home": "முகப்பு",
      "Chatbot": "சாட்போட்",
      "Hospitals": "மருத்துவமனைகள்",
      "Health Awareness": "சுகாதார விழிப்புணர்வு",
      "Describe your symptoms here...": "உங்கள் அறிகுறிகளை இங்கே விவரிக்கவும்...",
      "Analyzing...": "பகுப்பாய்வு செய்யப்படுகிறது...",
      "There was an error connecting to the health service. Please try again later.": "சுகாதார சேவையுடன் இணைப்பதில் பிழை ஏற்பட்டது. பின்னர் மீண்டும் முயற்சிக்கவும்.",
      "Hello! Please describe your symptoms, and I will recommend the right medical specialist for you.": "வணக்கம்! உங்கள் அறிகுறிகளை விவரிக்கவும், சரியான மருத்துவ நிபுணரை நான் பரிந்துரைக்கிறேன்."
    }
  },
  hi: {
    translation: {
      "Welcome to AI Health Assist": "AI हेल्थ असिस्ट में आपका स्वागत है",
      "Your intelligent healthcare companion.": "आपका बुद्धिमान स्वास्थ्य साथी।",
      "Get Started": "शुरू करें",
      "Home": "होम",
      "Chatbot": "चैटबॉट",
      "Hospitals": "अस्पताल",
      "Health Awareness": "स्वास्थ्य जागरूकता",
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "en", // default language
    fallbackLng: "en",
    interpolation: {
      escapeValue: false // react already safes from xss
    }
  });

export default i18n;
