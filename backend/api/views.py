from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from deep_translator import GoogleTranslator
import speech_recognition as sr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, 'symptoms_dataset.csv')


# Medical body-part / location words that sklearn's stop-word list would remove.
# We MUST keep these so "back pain", "leg pain" etc. retain their body-part token.
MEDICAL_KEEP_WORDS = {
    'back', 'leg', 'arm', 'eye', 'ear', 'lip', 'jaw', 'hip', 'rib',
    'skin', 'bone', 'neck', 'face', 'head', 'hand', 'foot', 'feet', 'heel',
    'toe', 'nose', 'gum', 'gut', 'chest', 'cold', 'hot', 'dry', 'red',
    'low', 'high', 'few', 'old', 'new', 'wet'
}

# Custom stop words — exclude medical keep words so they survive TF-IDF
custom_stop_words = [
    w for w in list(ENGLISH_STOP_WORDS) + [
        'sensation', 'feeling', 'severe', 'mild', 'sudden', 'chronic', 'acute',
        'feel', 'have', 'like', 'experiencing', 'experience', 'having', 'got'
    ]
    if w not in MEDICAL_KEEP_WORDS
]

# Load the dataset with auto-backup/recovery logic to prevent deletion or loss of custom training data
try:
    backup_path = os.path.join(BASE_DIR, 'symptoms_dataset_backup.csv')
    df = None
    
    # Load from whichever file exists and is larger/most complete
    if os.path.exists(csv_path) and os.path.exists(backup_path):
        df_primary = pd.read_csv(csv_path)
        df_backup = pd.read_csv(backup_path)
        
        if len(df_primary) >= len(df_backup):
            df = df_primary
            # Sync backup
            df.to_csv(backup_path, index=False)
        else:
            df = df_backup
            # Restore primary
            df.to_csv(csv_path, index=False)
            
    elif os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df.to_csv(backup_path, index=False)
    elif os.path.exists(backup_path):
        df = pd.read_csv(backup_path)
        df.to_csv(csv_path, index=False)
    else:
        # If both are missing, write a basic placeholder or raise
        raise FileNotFoundError("Both primary dataset and backup dataset are missing.")

    df['Description'] = df['Description'].fillna("No description available.")
    df['Precautions'] = df['Precautions'].fillna("No specific precautions.")
    df['Symptom'] = df['Symptom'].fillna("")
    df['Disease'] = df['Disease'].fillna("")

    # --- Symptom-only TF-IDF (primary matching — no description pollution) ---
    symptom_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=custom_stop_words)
    symptom_tfidf_matrix = symptom_vectorizer.fit_transform(df['Symptom'])

    # --- Combined TF-IDF (secondary context signal) ---
    df['CombinedText'] = df['Symptom'] + " " + df['Disease'] + " " + df['Description']
    combined_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words=custom_stop_words)
    combined_tfidf_matrix = combined_vectorizer.fit_transform(df['CombinedText'])
except Exception as e:
    print("Error loading dataset:", e)
    df = None


EMERGENCY_KEYWORDS = [
    'chest pain', 'heart attack', 'breathing', 'breath', 'unconscious',
    'bleeding', 'severe', 'urgent', 'emergency', 'stroke', 'choking'
]

# Broad set of health-related keywords used to classify user input
HEALTH_KEYWORDS = [
    'pain', 'ache', 'aching', 'sore', 'hurt', 'fever', 'temperature', 'cough',
    'cold', 'flu', 'sick', 'ill', 'symptom', 'disease', 'infection', 'virus',
    'bacteria', 'rash', 'itch', 'itching', 'swelling', 'swollen', 'nausea',
    'vomit', 'vomiting', 'diarrhea', 'headache', 'dizzy', 'dizziness',
    'fatigue', 'tired', 'weakness', 'breathe', 'breathing', 'chest', 'heart',
    'blood', 'pressure', 'sugar', 'diabetes', 'cancer', 'tumor', 'doctor',
    'hospital', 'medicine', 'drug', 'treatment', 'diagnosis', 'surgery',
    'allergy', 'asthma', 'stroke', 'injury', 'wound', 'burn', 'fracture',
    'bone', 'joint', 'muscle', 'skin', 'eye', 'ear', 'nose', 'throat',
    'stomach', 'abdomen', 'liver', 'kidney', 'lung', 'brain', 'nerve',
    'anxiety', 'depression', 'mental', 'sleep', 'insomnia', 'appetite',
    'thirst', 'urine', 'constipation', 'cramps', 'bloating', 'acid',
    'reflux', 'migraine', 'seizure', 'paralysis', 'numbness', 'tingling',
    'tremor', 'bleeding', 'bruise', 'dental', 'tooth', 'gum', 'vision',
    'hearing', 'immune', 'inflammation', 'back', 'neck', 'shoulder', 'knee',
    'leg', 'arm', 'hand', 'foot', 'finger', 'nail', 'hair', 'tongue',
    'mouth', 'lip', 'face', 'body', 'weight', 'obesity', 'cholesterol',
    'thyroid', 'hormone', 'period', 'menstrual', 'pregnant', 'pregnancy',
    'palpitation', 'sweat', 'chills', 'shiver', 'discharge', 'lump', 'bump',
    'stress', 'stressed', 'anxious', 'panic', 'depression', 'depressed', 'sadness',
    'hopelessness', 'mood', 'mental health', 'emotional', 'crying', 'suicidal'
]

def is_health_related(text):
    """Return True if the text contains at least one recognised health keyword."""
    text_lower = text.lower()
    return any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in HEALTH_KEYWORDS)

def check_emergency(text):
    text_lower = text.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            return True
    return False

@api_view(['POST'])
def analyze_symptom(request):
    original_symptom_text = request.data.get('symptom', '').strip()
    lang = request.data.get('lang', 'en')
    
    if not original_symptom_text:
        return Response({'error': 'Symptom text is required'}, status=400)
        
    symptom_text = original_symptom_text
    # Translate non-English input to English for NLP processing
    if lang != 'en':
        try:
            symptom_text = GoogleTranslator(source='auto', target='en').translate(original_symptom_text)
        except Exception as e:
            print(f"Translation error (to en): {e}")
            
    # Handle basic greetings gracefully
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'hi there']
    if symptom_text.lower() in greetings:
        msg = "Hello! What seems to be the problem today? Please describe your symptoms."
        if lang != 'en':
            try:
                msg = GoogleTranslator(source='en', target=lang).translate(msg)
            except Exception:
                pass
        return Response({
            'symptom': original_symptom_text,
            'specialist_recommended': '',
            'is_emergency': False,
            'message': msg
        })
    
    # --- Unrelated-query guard ---
    if not is_health_related(symptom_text):
        msg = "🩺 Please ask questions related to healthcare. I can only help with medical symptoms and health concerns."
        if lang != 'en':
            try:
                msg = GoogleTranslator(source='en', target=lang).translate(msg)
            except Exception:
                pass
        return Response({
            'symptom': original_symptom_text,
            'specialist_recommended': '',
            'is_emergency': False,
            'is_unrelated': True,
            'message': msg
        })

    is_emergency = check_emergency(symptom_text)
    primary_specialist = "General Physician"
    
    if df is not None:
        # Use symptom-ONLY TF-IDF as primary signal (no description pollution)
        sym_vec  = symptom_vectorizer.transform([symptom_text])
        sym_tfidf = cosine_similarity(sym_vec, symptom_tfidf_matrix).flatten()

        # Use combined TF-IDF as a light secondary context signal
        comb_vec  = combined_vectorizer.transform([symptom_text])
        comb_tfidf = cosine_similarity(comb_vec, combined_tfidf_matrix).flatten()

        symptom_lower = symptom_text.lower()

        # --- Generic words that must NOT drive matching by themselves ---
        GENERIC_SYMPTOM_WORDS = {
            'pain', 'ache', 'aching', 'hurt', 'hurts', 'sore', 'discomfort',
            'problem', 'issue', 'bad', 'worse', 'very', 'really', 'bit', 'lot'
        }

        # Include 2-char body-part words (leg, arm, ear, eye …) from MEDICAL_KEEP_WORDS
        raw_tokens = set(re.findall(r'\b[a-z]{2,}\b', symptom_lower))
        # Remove standard stop words, but keep MEDICAL_KEEP_WORDS
        all_user_tokens = (raw_tokens - set(custom_stop_words)) | (raw_tokens & MEDICAL_KEEP_WORDS)
        specific_user_tokens = all_user_tokens - GENERIC_SYMPTOM_WORDS
        generic_user_tokens  = all_user_tokens & GENERIC_SYMPTOM_WORDS

        combined_scores     = np.zeros(len(df))
        specific_hit_counts = np.zeros(len(df), dtype=int)

        for idx in range(len(df)):
            disease_symptom_text = str(df.iloc[idx]['Symptom']).lower()
            # Include short words (ear, leg, arm, eye …) from disease symptoms too
            disease_tokens = set(re.findall(r'\b[a-z]{2,}\b', disease_symptom_text)) - \
                             (set(custom_stop_words) - MEDICAL_KEEP_WORDS)

            if not disease_tokens:
                continue

            # --- Specific token matching ---
            specific_matched = specific_user_tokens & disease_tokens
            n_specific = len(specific_matched)
            specific_hit_counts[idx] = n_specific

            if specific_user_tokens:
                specific_overlap  = n_specific / len(disease_tokens)
                specific_coverage = n_specific / len(specific_user_tokens)
                specific_score = specific_overlap * 0.5 + specific_coverage * 0.5
            else:
                specific_score = 0.0

            # --- Generic token matching (tiny tie-breaker only) ---
            generic_matched = generic_user_tokens & disease_tokens
            generic_score = (len(generic_matched) / len(disease_tokens)) * 0.03

            symptom_score = specific_score + generic_score

            # Blend: 70% symptom-TF-IDF + 20% symptom-overlap + 10% combined-TF-IDF
            combined_scores[idx] = (sym_tfidf[idx] * 0.70
                                    + symptom_score   * 0.20
                                    + comb_tfidf[idx] * 0.10)

        top_indices = np.argsort(combined_scores)[::-1]

        matches = []
        best_score = combined_scores[top_indices[0]] if len(top_indices) > 0 else 0
        best_specific_hits = specific_hit_counts[top_indices[0]] if len(top_indices) > 0 else 0

        for idx in top_indices:
            score      = combined_scores[idx]
            n_specific = specific_hit_counts[idx]

            # Hard minimum threshold
            if score < 0.05:
                break

            if len(matches) >= 1:
                # Tighter secondary threshold
                if score < best_score * 0.88:
                    continue
                # If no disease at all has a specific hit, never show a second result
                # (prevents Dengue appearing alongside Osteoarthritis for "leg pain")
                if best_specific_hits == 0:
                    continue
                # Secondary must also have a specific hit when primary does
                if n_specific == 0 and best_specific_hits > 0:
                    continue

            disease_name = df.iloc[idx]['Disease']
            if not any(m['Disease'] == disease_name for m in matches):
                matches.append(df.iloc[idx])
            
            # Suppress secondary matches for single-symptom queries to avoid confusion and false predictions
            if len(specific_user_tokens) <= 1 and len(matches) >= 1:
                break
                
            if len(matches) == 2:
                break

        # Localization template definitions
        templates = {
            'en': {
                'multiple_phys': "We detected multiple potential conditions based on your symptoms:\n\n",
                'single_phys': "Based on your symptoms, you may be experiencing {disease}.\n\n",
                'desc_label': "Description",
                'prec_label': "Precautions",
                'rec_label': "Recommendation: We recommend consulting a {specialist}.\n\n",
                'emergency_msg': "🚨 WARNING: YOUR SYMPTOMS INDICATE A POTENTIAL MEDICAL EMERGENCY! 🚨\nPlease seek immediate medical attention, visit the nearest emergency room (ER), or call an ambulance right away.\n\n",
                'unknown_msg': "Based on your symptoms, you may be experiencing an unknown condition.\n\nDescription: We couldn't accurately determine the exact cause based on your input.\nPrecautions: Rest and monitor your symptoms.\n\nRecommendation: We recommend consulting a General Physician.",
                'dataset_err': "Dataset unavailable.",
                'mental_multiple': "📋 DIAGNOSIS SUMMARY:\nWe detected multiple potential conditions matching your symptom profile. Please review the details below:\n\n",
                'mental_single': "📋 DIAGNOSIS SUMMARY:\nBased on the analysis of your symptoms, you may be experiencing {disease}.\n\n",
                'mental_cond': "🔍 CONDITION",
                'mental_desc_title': "💬 Description of Condition",
                'mental_prec_title': "🛡️ Actionable Precautions & Self-Care Steps",
                'mental_rec_title': "👨‍⚕️ Specialist Recommendation",
                'mental_rec_detail': "We highly recommend consulting {specialist} for a personalized clinical evaluation.\n\n",
                'mental_guidance': "💡 GENERAL HEALTH GUIDANCE:\n- Monitor your vital signs: Keep track of your body temperature, heart rate, and any new symptom developments.\n- Avoid self-medication: Do not take antibiotics or strong pain relievers without a doctor's explicit prescription.\n- Prepare for your appointment: Write down when symptoms started, their severity, and any questions you have for your doctor.\n\n",
                'mental_disclaimer': "⚠️ MEDICAL DISCLAIMER:\nThis diagnostic recommendation is powered by AI algorithms and is intended solely for informational and educational purposes. It does not constitute formal medical advice, clinical diagnosis, or treatment plans. Always seek the advice of your physician or other qualified health providers with any questions you may have regarding a medical condition."
            },
            'ta': {
                'multiple_phys': "உங்கள் அறிகுறிகளின் அடிப்படையில் பல சாத்தியமான நிலைகளை நாங்கள் கண்டறிந்தோம்:\n\n",
                'single_phys': "உங்கள் அறிகுறிகளின் அடிப்படையில், உங்களுக்கு {disease} இருக்கலாம்.\n\n",
                'desc_label': "விளக்கம்",
                'prec_label': "முன்னெச்சரிக்கைகள்",
                'rec_label': "பரிந்துரை: {specialist} அவர்களிடம் ஆலோசனை பெற பரிந்துரைக்கிறோம்.\n\n",
                'emergency_msg': "🚨 எச்சரிக்கை: உங்கள் அறிகுறிகள் அவசர மருத்துவத் தேவையை உணர்த்துகின்றன! 🚨\nஉடனடியாக மருத்துவ உதவியை நாடவும், அருகில் உள்ள அவசர சிகிச்சை பிரிவுக்குச் செல்லவும் அல்லது ஆம்புலன்ஸை அழைக்கவும்.\n\n",
                'unknown_msg': "உங்கள் அறிகுறிகளின் அடிப்படையில், உங்களுக்கு அறியப்படாத பாதிப்பு இருக்கலாம்.\n\nவிளக்கம்: உங்கள் உள்ளீட்டின் அடிப்படையில் எங்களால் துல்லியமான காரணத்தை தீர்மானிக்க முடியவில்லை.\nமுன்னெச்சரிக்கைகள்: ஓய்வெடுத்து உங்கள் அறிகுறிகளைக் கண்காணிக்கவும்.\n\nபரிந்துரை: பொது மருத்துவரை அணுகி ஆலோசனை பெற பரிந்துரைக்கிறோம்.",
                'dataset_err': "தரவுத்தளம் கிடைக்கவில்லை.",
                'mental_multiple': "📋 நோய் கண்டறிதல் சுருக்கம்:\nஉங்கள் அறிகுறிக்கு பொருந்தக்கூடிய பல சாத்தியமான பாதிப்புகளை நாங்கள் கண்டறிந்துள்ளோம். விவரங்களை கீழே பார்க்கவும்:\n\n",
                'mental_single': "📋 நோய் கண்டறிதல் சுருக்கம்:\nஉங்கள் அறிகுறிகளின் பகுப்பாய்வின் அடிப்படையில், உங்களுக்கு {disease} இருக்கலாம்.\n\n",
                'mental_cond': "🔍 பாதிப்பு",
                'mental_desc_title': "💬 பாதிப்பின் விளக்கம்",
                'mental_prec_title': "🛡️ முன்னெச்சரிக்கை மற்றும் சுய-கவனிப்பு படிகள்",
                'mental_rec_title': "👨‍⚕️ மருத்துவ நிபுணரின் பரிந்துரை",
                'mental_rec_detail': "தனிப்பட்ட மருத்துவ பரிசோதனைக்கு {specialist} அணுகி ஆலோசனை பெற பரிந்துரைக்கிறோம்.\n\n",
                'mental_guidance': "💡 பொதுவான சுகாதார வழிகாட்டுதல்:\n- உங்கள் உடல்நிலை மாற்றங்களைக் கண்காணிக்கவும்: உங்கள் உடல் வெப்பநிலை, இதயத் துடிப்பு மற்றும் ஏதேனும் புதிய அறிகுறிகளின் முன்னேற்றத்தைக் கண்காணிக்கவும்.\n- சுய மருத்துவம் தவிர்க்கவும்: மருத்துவரின் பரிந்துரை இல்லாமல் எந்த மருந்துகளையும் எடுத்துக்கொள்ள வேண்டாம்.\n- மருத்துவரை சந்திக்கத் தயாராகுங்கள்: அறிகுறிகள் எப்போது தொடங்கின, அவற்றின் தீவிரம் மற்றும் மருத்துவரிடம் கேட்க வேண்டிய கேள்விகளை எழுதி வைத்துக் கொள்ளுங்கள்.\n\n",
                'mental_disclaimer': "⚠️ மருத்துவ மறுப்பு:\nஇந்த கண்டறிதல் பரிந்துரை தகவல் மற்றும் கல்வி நோக்கங்களுக்காக மட்டுமே. இது முறையான மருத்துவ ஆலோசனை, கண்டறிதல் அல்லது சிகிச்சை திட்டங்களை உருவாக்காது. மருத்துவ நிலை குறித்து உங்களுக்கு ஏதேனும் கேள்விகள் இருந்தால் எப்போதும் உங்கள் மருத்துவர் அல்லது தகுதி வாய்ந்த பிற சுகாதார வழங்குநர்களின் ஆலோசனையைப் பெறவும்."
            },
            'hi': {
                'multiple_phys': "आपके लक्षणों के आधार पर हमें कई संभावित स्थितियों का पता चला है:\n\n",
                'single_phys': "आपके लक्षणों के आधार पर, आपको {disease} हो सकता है।\n\n",
                'desc_label': "विवरण",
                'prec_label': "सावधानियां",
                'rec_label': "सिफारिश: हम {specialist} से परामर्श करने की सलाह देते हैं।\n\n",
                'emergency_msg': "🚨 चेतावनी: आपके लक्षण संभावित आपातकालीन चिकित्सा स्थिति का संकेत देते हैं! 🚨\nकृपया तुरंत आपातकालीन चिकित्सा सहायता लें या एम्बुलेंस को कॉल करें।\n\n",
                'unknown_msg': "आपके लक्षणों के आधार पर, आपको किसी अज्ञात स्थिति का अनुभव हो सकता है।\n\nविवरण: हम आपके इनपुट के आधार पर सटीक कारण का निर्धारण नहीं कर सके।\nसावधानियां: आराम करें और अपने लक्षणों की निगरानी करें।\n\nसिफारिश: हम एक सामान्य चिकित्सक से परामर्श करने की सलाह देते हैं।",
                'dataset_err': "डेटासेट अनुपलब्ध है।",
                'mental_multiple': "📋 निदान सारांश:\nहमें आपके लक्षण प्रोफ़ाइल से मेल खाने वाली कई संभावित स्थितियों का पता चला है। कृपया नीचे विवरण की समीक्षा करें:\n\n",
                'mental_single': "📋 निदान सारांश:\nआपके लक्षणों के विश्लेषण के आधार पर, आपको {disease} हो सकता है।\n\n",
                'mental_cond': "🔍 स्थिति",
                'mental_desc_title': "💬 स्थिति का विवरण",
                'mental_prec_title': "🛡️ सावधानियां और स्व-देखभाल के उपाय",
                'mental_rec_title': "👨‍⚕️ विशेषज्ञ की सिफारिश",
                'mental_rec_detail': "हम व्यक्तिगत नैदानिक मूल्यांकन के लिए {specialist} से परामर्श करने की सलाह देते हैं।\n\n",
                'mental_guidance': "💡 सामान्य स्वास्थ्य मार्गदर्शन:\n- अपने महत्वपूर्ण लक्षणों की निगरानी करें: अपने शरीर के तापमान, हृदय गति और किसी भी नए लक्षण के विकास पर नज़र रखें।\n- स्व-दवा से बचें: डॉक्टर के पर्चे के बिना कोई भी दवा न लें।\n- अपनी नियुक्ति की तैयारी करें: लिखें कि लक्षण कब शुरू हुए, उनकी गंभीरता और आपके डॉक्टर के लिए कोई भी प्रश्न।\n\n",
                'mental_disclaimer': "⚠️ चिकित्सा अस्वीकरण:\nयह निदान सिफारिश केवल सूचनात्मक और शैक्षिक उद्देश्यों के लिए है। यह औपचारिक चिकित्सा सलाह या उपचार का विकल्प नहीं है। हमेशा अपने चिकित्सक की सलाह लें।"
            }
        }
        
        t_lang = lang if lang in templates else 'en'
        t_active = templates[t_lang]

        if len(matches) > 0:
            # Check if there is any mental health match (Stress & Anxiety or Depression)
            has_mental_health_match = any(m['Disease'] in ['Stress & Anxiety', 'Depression'] for m in matches)
            
            primary_match = matches[0]
            primary_specialist = primary_match['Specialist']
            
            # Check for emergency override in any match
            # To prevent single-symptom false alarms (e.g., just a headache matching brain hemorrhage),
            # we only trigger emergency warnings if the user entered explicit emergency keywords
            # OR if we matched 2 or more specific symptoms for that emergency condition.
            is_emergency = check_emergency(symptom_text)
            
            for m in matches:
                if str(m['Is_Emergency']).lower() == 'true':
                    # Find specific hits count for this matched disease
                    disease_name = m['Disease']
                    idx = df[df['Disease'] == disease_name].index[0]
                    n_specific = specific_hit_counts[idx]
                    
                    if n_specific >= 2 or is_emergency:
                        is_emergency = True
            
            # Translate core database text fields dynamically if language is non-English
            processed_matches = []
            for m in matches:
                disease_raw = m['Disease']
                desc_raw = m['Description']
                prec_raw = m['Precautions']
                spec_raw = m['Specialist']
                
                if lang != 'en':
                    try:
                        disease_raw = GoogleTranslator(source='en', target=lang).translate(disease_raw)
                        desc_raw = GoogleTranslator(source='en', target=lang).translate(desc_raw)
                        # We keep precautions in English for formatting triggers, translate them line by line below
                        spec_raw = GoogleTranslator(source='en', target=lang).translate(spec_raw)
                    except Exception as e:
                        print(f"Translation dynamic text error: {e}")
                        
                processed_matches.append({
                    'Disease': disease_raw,
                    'Description': desc_raw,
                    'Precautions_English': m['Precautions'],
                    'Specialist': spec_raw,
                    'Is_Emergency': m['Is_Emergency']
                })
            
            if is_emergency:
                primary_specialist = "Emergency / Urgent Care"
                message = t_active['emergency_msg']
                
            elif has_mental_health_match:
                # --- Mental Health Layout: Detailed Summary ---
                if len(processed_matches) > 1:
                    message = t_active['mental_multiple']
                else:
                    message = t_active['mental_single'].format(disease=processed_matches[0]['Disease'])
                
                # Append comprehensive information blocks for each matched condition
                for m in processed_matches:
                    disease = m['Disease']
                    description = m['Description']
                    precautions_english = [p.strip() for p in m['Precautions_English'].split(',') if p.strip()]
                    specialist = m['Specialist']
                    
                    if len(processed_matches) > 1:
                        message += f"{t_active['mental_cond']}: {disease.upper()}\n"
                        message += f"============================\n"
                    
                    message += f"{t_active['mental_desc_title']}:\n{description}\n\n"
                    message += f"{t_active['mental_prec_title']}:\n"
                    
                    if precautions_english:
                        for i, step in enumerate(precautions_english, 1):
                            capitalized_step = step.capitalize()
                            # Build and translate detailed context steps
                            if "water" in step.lower() or "hydrate" in step.lower() or "juice" in step.lower():
                                detailed_step = f"{capitalized_step} — Drink fluids consistently throughout the day to support recovery, flush out toxins, and prevent dehydration."
                            elif "rest" in step.lower() or "sleep" in step.lower() or "lying down" in step.lower():
                                detailed_step = f"{capitalized_step} — Get plenty of bed rest to allow your body's immune system to focus its energy on recovery."
                            elif "doctor" in step.lower() or "consult" in step.lower() or "hospital" in step.lower():
                                detailed_step = f"{capitalized_step} — Schedule a visit with a medical professional if symptoms persist, worsen, or do not improve."
                            elif "medication" in step.lower() or "pill" in step.lower() or "tablet" in step.lower() or "cream" in step.lower() or "ointment" in step.lower():
                                detailed_step = f"{capitalized_step} — Use any medications or topical treatments strictly as directed by a healthcare provider."
                            else:
                                detailed_step = f"{capitalized_step} — Follow this precaution carefully to reduce discomfort and prevent further complications."
                            
                            # Translate the built detailed precaution step
                            if lang != 'en':
                                try:
                                    detailed_step = GoogleTranslator(source='en', target=lang).translate(detailed_step)
                                except Exception:
                                    pass
                            message += f"  {i}. {detailed_step}\n"
                    else:
                        # Fallback localized bullet point list
                        fb1 = "Rest and monitor your symptoms closely."
                        fb2 = "Stay hydrated and avoid strenuous activities."
                        if lang != 'en':
                            try:
                                fb1 = GoogleTranslator(source='en', target=lang).translate(fb1)
                                fb2 = GoogleTranslator(source='en', target=lang).translate(fb2)
                            except Exception:
                                pass
                        message += f"  1. {fb1}\n  2. {fb2}\n"
                    
                    message += "\n"
                    
                    # Add custom explanation for recommended specialists
                    spec_explanation = f"a Psychiatrist or Psychologist (a mental health specialist who provides diagnostic assessment and treatment for emotional, cognitive, and behavioral concerns)"
                    if "Therapist" in specialist or "Counselor" in specialist:
                        spec_explanation = f"a Licensed Therapist or Counselor (a certified mental health practitioner trained to offer counseling and therapy for stress, anxiety, or depression)"
                    
                    if lang != 'en':
                        try:
                            spec_explanation = GoogleTranslator(source='en', target=lang).translate(spec_explanation)
                        except Exception:
                            pass
                    
                    message += f"{t_active['mental_rec_title']}:\n" + t_active['mental_rec_detail'].format(specialist=spec_explanation)
                
                # Append general guidance and disclaimer blocks directly from templates
                message += t_active['mental_guidance']
                message += t_active['mental_disclaimer']
            
            else:
                # --- Physical Disease Layout: Classic/Original Formatting ---
                if len(processed_matches) > 1:
                    message = t_active['multiple_phys']
                else:
                    message = t_active['single_phys'].format(disease=processed_matches[0]['Disease'])
                
                # Append blocks for each match
                for m in processed_matches:
                    disease = m['Disease']
                    description = m['Description']
                    precautions_english = [p.strip() for p in m['Precautions_English'].split(',') if p.strip()]
                    specialist = m['Specialist']
                    
                    # Translate comma-separated precautions
                    prec_translated_list = []
                    for p in precautions_english:
                        p_t = p
                        if lang != 'en':
                            try:
                                p_t = GoogleTranslator(source='en', target=lang).translate(p)
                            except Exception:
                                pass
                        prec_translated_list.append(p_t)
                    precautions_str = ", ".join(prec_translated_list)

                    if len(processed_matches) > 1:
                        message += f"--- {disease} ---\n"
                    message += f"{t_active['desc_label']}: {description}\n"
                    message += f"{t_active['prec_label']}: {precautions_str}\n"
                    message += t_active['rec_label'].format(specialist=specialist)
        
        else:
            # Fallback when no match is found
            if is_emergency:
                primary_specialist = "Emergency / Urgent Care"
                message = t_active['emergency_msg']
            else:
                message = t_active['unknown_msg']
    else:
        message = t_active['dataset_err']

    response_data = {
        'symptom': original_symptom_text,
        'specialist_recommended': primary_specialist,
        'is_emergency': is_emergency,
        'message': message.strip()
    }
    
    return Response(response_data)

@api_view(['POST'])
def transcribe_audio(request):
    audio_file = request.FILES.get('audio')
    lang = request.data.get('lang', 'en-US')
    
    if not audio_file:
        return Response({'error': 'No audio file provided'}, status=400)
        
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            
        # Select appropriate language code for Google Speech Recognition
        lang_map = {'en': 'en-US', 'ta': 'ta-IN', 'hi': 'hi-IN'}
        target_lang = lang_map.get(lang, 'en-US')
        
        text = recognizer.recognize_google(audio, language=target_lang)
        return Response({'text': text})
    except sr.UnknownValueError:
        return Response({'error': 'Could not understand audio'}, status=400)
    except sr.RequestError as e:
        return Response({'error': f'Could not request results; {e}'}, status=500)
    except ValueError as e:
        # Happens if file format is unsupported
        return Response({'error': f'Audio format not supported: {e}'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
