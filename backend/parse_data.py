import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'dataset')

# 1. Read symptoms dataset
# First row might be empty headers, so we read it and just take all cols
try:
    df_symptoms = pd.read_csv(os.path.join(DATA_DIR, 'dataset.csv'))
    # rename first col to Disease
    df_symptoms.rename(columns={df_symptoms.columns[0]: 'Disease'}, inplace=True)
except Exception as e:
    print("Error reading dataset.csv:", e)

# Clean up symptom strings and combine them for each disease
def clean_symptom(x):
    if pd.isna(x):
        return ""
    return str(x).replace('_', ' ').strip()

disease_symptoms = {}
for idx, row in df_symptoms.iterrows():
    disease = row['Disease']
    if pd.isna(disease):
        continue
    disease = disease.strip()
    symptoms = []
    for col in df_symptoms.columns[1:]:
        symp = clean_symptom(row[col])
        if symp:
            symptoms.append(symp)
    if disease not in disease_symptoms:
        disease_symptoms[disease] = set(symptoms)
    else:
        disease_symptoms[disease].update(symptoms)

# Convert sets back to strings
master_data = []
for disease, sym_set in disease_symptoms.items():
    master_data.append({
        'Disease': disease,
        'Symptom': " ".join(sym_set)
    })

df_master = pd.DataFrame(master_data)

# 2. Read Descriptions
df_desc = pd.read_csv(os.path.join(DATA_DIR, 'symptom_Description.csv'), header=None, names=['Disease', 'Description'])
df_desc['Disease'] = df_desc['Disease'].str.strip()
df_desc['Description'] = df_desc['Description'].str.strip()

# 3. Read Precautions
df_prec = pd.read_csv(os.path.join(DATA_DIR, 'symptom_precaution.csv'), header=None, names=['Disease', 'P1', 'P2', 'P3', 'P4'])
df_prec['Disease'] = df_prec['Disease'].str.strip()
def combine_precautions(row):
    precs = [str(x).strip() for x in [row['P1'], row['P2'], row['P3'], row['P4']] if not pd.isna(x) and str(x).strip()]
    return ", ".join(precs)

df_prec['Precautions'] = df_prec.apply(combine_precautions, axis=1)

# Merge
df_master = df_master.merge(df_desc, on='Disease', how='left')
df_master = df_master.merge(df_prec[['Disease', 'Precautions']], on='Disease', how='left')

# Mapping for Specialists based on common diseases in the dataset
specialist_map = {
    'Fungal infection': 'Dermatologist',
    'Allergy': 'Allergist',
    'GERD': 'Gastroenterologist',
    'Chronic cholestasis': 'Gastroenterologist',
    'Drug Reaction': 'Allergist or General Physician',
    'Peptic ulcer diseae': 'Gastroenterologist',
    'AIDS': 'Infectious Disease Specialist',
    'Diabetes ': 'Endocrinologist',
    'Gastroenteritis': 'Gastroenterologist',
    'Bronchial Asthma': 'Pulmonologist',
    'Hypertension ': 'Cardiologist',
    'Migraine': 'Neurologist',
    'Cervical spondylosis': 'Orthopedist',
    'Paralysis (brain hemorrhage)': 'Neurologist',
    'Jaundice': 'Gastroenterologist',
    'Malaria': 'Infectious Disease Specialist',
    'Chicken pox': 'General Physician',
    'Dengue': 'Infectious Disease Specialist',
    'Typhoid': 'General Physician',
    'hepatitis A': 'Gastroenterologist',
    'Hepatitis B': 'Gastroenterologist',
    'Hepatitis C': 'Gastroenterologist',
    'Hepatitis D': 'Gastroenterologist',
    'Hepatitis E': 'Gastroenterologist',
    'Alcoholic hepatitis': 'Gastroenterologist',
    'Tuberculosis': 'Pulmonologist',
    'Common Cold': 'General Physician',
    'Pneumonia': 'Pulmonologist',
    'Dimorphic hemmorhoids(piles)': 'Proctologist',
    'Heart attack': 'Cardiologist',
    'Varicose veins': 'Vascular Surgeon',
    'Hypothyroidism': 'Endocrinologist',
    'Hyperthyroidism': 'Endocrinologist',
    'Hypoglycemia': 'Endocrinologist',
    'Osteoarthristis': 'Rheumatologist or Orthopedist',
    'Arthritis': 'Rheumatologist or Orthopedist',
    '(vertigo) Paroymsal  Positional Vertigo': 'ENT Specialist',
    'Acne': 'Dermatologist',
    'Urinary tract infection': 'Urologist',
    'Psoriasis': 'Dermatologist',
    'Impetigo': 'Dermatologist'
}

df_master['Disease'] = df_master['Disease'].str.strip()

def get_specialist(dis):
    return specialist_map.get(dis.strip(), 'General Physician')

df_master['Specialist'] = df_master['Disease'].apply(get_specialist)
df_master['Is_Emergency'] = df_master['Disease'].apply(lambda x: 'Heart attack' in str(x) or 'Paralysis' in str(x))

df_master.to_csv(os.path.join(BASE_DIR, 'symptoms_dataset.csv'), index=False)
print("Successfully generated master dataset.")
