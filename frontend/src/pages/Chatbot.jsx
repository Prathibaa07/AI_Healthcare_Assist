import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, Send, Volume2, VolumeX, Loader, AlertTriangle, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import RecordRTC from 'recordrtc';
import './Chatbot.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://ai-healthcare-assist-2mzh.onrender.com';

const Chatbot = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Error parsing chat history", e);
      }
    }
    return [
      { id: 1, text: t("Hello! Please describe your symptoms, and I will recommend the right medical specialist for you."), sender: 'bot', isEmergency: false, specialist: null }
    ];
  });

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, [messages]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(true);
  
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const initialInputValueRef = useRef('');
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Stop currently playing audio immediately if muted
  useEffect(() => {
    if (!speechEnabled && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }, [speechEnabled]);

  // Pre-load speech synthesis voices on mount for instant access
  useEffect(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
    }
  }, []);

  const processAudioFallback = async (audioBlob) => {
    setIsLoading(true);
    const formData = new FormData();
    formData.append('audio', audioBlob, 'speech.wav');
    formData.append('lang', i18n.language);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/transcribe/`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.text) {
            setInputValue(prev => (prev ? prev + " " + data.text : data.text));
        } else {
            console.error("Transcription error:", data.error);
        }
    } catch (err) {
        console.error("Failed to transcribe audio", err);
    } finally {
        setIsLoading(false);
    }
  };

  // Speech Recognition Setup
  const toggleRecording = async () => {
    if (isRecording && recognitionRef.current) {
      if (recognitionRef.current.stop) {
        // Native stop
        recognitionRef.current.stop();
      } else if (recognitionRef.current.stopRecording) {
        // Fallback RecordRTC stop
        recognitionRef.current.stopRecording(() => {
          const blob = recognitionRef.current.getBlob();
          setIsRecording(false);
          processAudioFallback(blob);
          if (recognitionRef.current.microphone) {
            recognitionRef.current.microphone.getTracks().forEach(track => track.stop());
          }
        });
      }
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        initialInputValueRef.current = inputValue;
        const recognition = new SpeechRecognition();
        const langMap = { en: 'en-US', ta: 'ta-IN', hi: 'hi-IN' };
        recognition.lang = langMap[i18n.language] || 'en-US';
        recognition.continuous = true; // Enables continuous listening without early cutoff
        recognition.interimResults = true; // Displays transcript in real-time as user speaks
        recognition.maxAlternatives = 1;

        recognition.onstart = () => setIsRecording(true);
        
        recognition.onresult = (event) => {
          let interimTranscript = '';
          let finalTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }
          const currentSpeech = finalTranscript || interimTranscript;
          if (currentSpeech) {
            setInputValue(() => {
              const prefix = initialInputValueRef.current;
              return prefix ? prefix + " " + currentSpeech : currentSpeech;
            });
          }
        };

        recognition.onerror = (event) => {
          console.error("Speech recognition error", event.error);
          setIsRecording(false);
        };

        recognition.onend = () => setIsRecording(false);

        recognitionRef.current = recognition;
        recognition.start();
      } catch (e) {
        console.error("Microphone start error:", e);
        setIsRecording(false);
      }
    } else {
      // Fallback for Firefox and others
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recordRTC = new RecordRTC(stream, {
            type: 'audio',
            mimeType: 'audio/wav',
            recorderType: RecordRTC.StereoAudioRecorder,
            desiredSampRate: 16000
        });
        recordRTC.startRecording();
        recordRTC.microphone = stream;
        recognitionRef.current = recordRTC;
        setIsRecording(true);
      } catch (err) {
        console.error("Mic access denied", err);
        alert("Microphone access denied.");
      }
    }
  };

  const speakText = (text, langCode) => {
    if (!speechEnabled || !('speechSynthesis' in window)) return;
    
    // Stop any ongoing speech
    window.speechSynthesis.cancel();
    
    // Clean up punctuation symbols that text-to-speech engines read out loud (like "dash dash dash")
    let cleanText = text
      .replace(/[-=_]{2,}/g, ' ') // Remove multiple dashes, equals, or underscores
      .replace(/[🚨📋🔍💬🛡️👨‍⚕️💡⚠️✨]/g, '') // Remove visual emojis
      .replace(/\s+/g, ' ')
      .trim();

    if (!cleanText) return;

    // Normalize input language code to base two characters (e.g. "ta-IN" -> "ta")
    const baseLang = (langCode || 'en').split('-')[0].toLowerCase();

    const langMap = { en: 'en-US', ta: 'ta-IN', hi: 'hi-IN' };
    const targetLang = langMap[baseLang] || 'en-US';
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = targetLang;
    
    // Find and assign the matching voice, then speak immediately
    const voices = window.speechSynthesis.getVoices();
    const matchingVoice = voices.find(voice => 
      voice.lang.toLowerCase() === targetLang.toLowerCase() || 
      voice.lang.toLowerCase().replace('_', '-').startsWith(baseLang)
    );
    
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }
    window.speechSynthesis.speak(utterance);
  };

  // Optional Translation function (if we want to translate text before sending/after receiving)
  // For now, we will send text as is. If Google Translate API is integrated, it would wrap the fetch call.
  // We simulate translation or assume the user types in English for the NLP backend to work properly.
  // Actually, since NLP model is trained in English, we should translate non-English inputs to English,
  // and responses back to the selected language. 
  // We will use a mock translation logic for now, until actual API is wired.

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userText = inputValue;
    const newMessage = { id: Date.now(), text: userText, sender: 'user' };
    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Direct call to Django Backend
      const response = await fetch(`${API_BASE_URL}/api/analyze/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symptom: userText, lang: i18n.language })
      });
      
      const data = await response.json();
      
      if (data.specialist_recommended) {
        localStorage.setItem('recommendedSpecialist', data.specialist_recommended);
      }
      
      // The API returns message and is_emergency
      const botResponseText = data.message || "Sorry, I could not understand the symptom.";
      
      const botMessage = {
        id: Date.now() + 1,
        text: botResponseText,
        sender: 'bot',
        isEmergency: data.is_emergency,
        isUnrelated: data.is_unrelated || false,
        specialist: data.specialist_recommended
      };
      
      setMessages(prev => [...prev, botMessage]);
      if (!data.is_unrelated) {
        speakText(botResponseText, i18n.language);
      }

    } catch (error) {
      console.error('Error fetching analysis:', error);
      const errorMsg = t("There was an error connecting to the health service. Please try again later.");
      setMessages(prev => [...prev, { id: Date.now() + 1, text: errorMsg, sender: 'bot', isEmergency: false, specialist: null }]);
      speakText(errorMsg, i18n.language);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const handleLocationSearch = (specialist) => {
    navigate('/hospitals');
  };

  return (
    <div className="page-container container animate-fade-in">
      <div className="chat-header">
        <h2>{t('Chatbot')}</h2>
        <button 
          className="speech-toggle-btn"
          onClick={() => setSpeechEnabled(!speechEnabled)}
          title={speechEnabled ? "Disable Voice Output" : "Enable Voice Output"}
        >
          {speechEnabled ? <Volume2 size={24} /> : <VolumeX size={24} />}
        </button>
      </div>
      
      <div className="chatbot-wrapper glass-panel">
        <div className="chat-window">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-message ${msg.sender} ${msg.isEmergency ? 'emergency-alert' : ''} ${msg.isUnrelated ? 'unrelated-alert' : ''}`}>
              {msg.isEmergency && msg.sender === 'bot' && (
                <div className="emergency-icon">
                  <AlertTriangle size={20} />
                </div>
              )}
              {msg.isUnrelated && msg.sender === 'bot' && (
                <div className="unrelated-icon">
                  <AlertTriangle size={20} />
                </div>
              )}
              <div className="message-content">
                <div className="message-text">
                  <span>{msg.text}</span>
                  {!msg.isUnrelated && (
                    <button 
                      className="inline-speak-btn" 
                      onClick={() => speakText(msg.text, i18n.language)}
                      title="Read out loud"
                    >
                      <Volume2 size={18} />
                    </button>
                  )}
                </div>
                
                {msg.specialist && msg.sender === 'bot' && !msg.isUnrelated && (
                  <div className="location-action-container">
                    <button 
                      className="location-btn" 
                      onClick={() => handleLocationSearch(msg.specialist)}
                      title={`Find ${msg.specialist} locations near you`}
                    >
                      <MapPin size={16} />
                      <span>Find {msg.specialist} Near Me</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-message bot">
              <div className="message-content typing-indicator">
                <Loader className="spin" size={20} />
                <span>{t('Analyzing...')}</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="chat-input-area">
          <button 
            className={`mic-btn ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
            title={isRecording ? "Stop Recording" : "Speak"}
          >
            <Mic size={24} />
          </button>
          <input 
            type="text" 
            placeholder={t('Describe your symptoms here...')}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button className="send-btn" onClick={handleSend} disabled={!inputValue.trim()}>
            <Send size={24} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
