import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, 'symptoms_dataset.csv')
backup_path = os.path.join(BASE_DIR, 'symptoms_dataset_backup.csv')

# Load the current dataset
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
elif os.path.exists(backup_path):
    df = pd.read_csv(backup_path)
else:
    print("Error: symptoms_dataset.csv not found.")
    exit(1)

custom_rows = [
    {
        'Disease': 'Orthopedic Pain',
        'Symptom': 'leg pain hand pain arm pain back pain neck pain knee pain shoulder pain foot pain joint ache muscle pain cramp cramps muscle cramp muscle cramps muscle ache limb stiffness',
        'Description': 'Orthopedic pain covers joint, muscle, and bone issues which cause aching, muscle cramps, stiffness, or sharp pain in limbs and joints.',
        'Precautions': 'rest the affected area, apply ice or heat, take over the counter pain relievers, consult doctor',
        'Specialist': 'Orthopedist',
        'Is_Emergency': False
    },
    {
        'Disease': 'Localized Skin Infection',
        'Symptom': 'reddish color hand elbow arm leg foot middle finger toe redness swelling irritation',
        'Description': 'A localized skin infection or dermatitis can cause redness, swelling, and a reddish color on the affected area.',
        'Precautions': 'keep area clean, apply topical cream if prescribed, monitor for swelling, consult doctor',
        'Specialist': 'Dermatologist',
        'Is_Emergency': False
    },
    {
        'Disease': 'Dental Issue',
        'Symptom': 'toothache jaw pain gums bleeding sensitive teeth tooth pain gum swelling',
        'Description': 'Dental issues involve problems with the teeth, gums, or jaw.',
        'Precautions': 'rinse with salt water, use cold compress, brush gently, consult dentist',
        'Specialist': 'Dentist',
        'Is_Emergency': False
    },
    {
        'Disease': 'Stress & Anxiety',
        'Symptom': 'stressed stress anxious panic attacks worry heart racing restlessness nervous feeling sweat shaking breathlessness',
        'Description': 'Stress and anxiety are mental health responses to challenging or threatening situations, causing emotional tension, rapid heart rate, and constant worry.',
        'Precautions': 'practice deep breathing, engage in regular exercise, limit caffeine intake, consult psychologist or therapist',
        'Specialist': 'Psychologist or Psychiatrist',
        'Is_Emergency': False
    },
    {
        'Disease': 'Depression',
        'Symptom': 'depressed sadness hoplessness loss of interest fatigue mood swings sleep issues crying spells suicidal thoughts low energy',
        'Description': 'Depression is a common and serious medical illness that negatively affects how you feel, the way you think, and how you act, causing persistent sadness and loss of interest in activities.',
        'Precautions': 'reach out to trusted friends, maintain a regular sleep schedule, stay physically active, consult psychologist or psychiatrist',
        'Specialist': 'Psychiatrist or Therapist',
        'Is_Emergency': False
    },
    {
        'Disease': 'Tension Headache',
        'Symptom': 'headache head pain forehead pressure neck stiffness mild headache',
        'Description': 'A tension headache is the most common type of headache. It can cause mild, moderate, or intense pain behind your eyes and in your head and neck.',
        'Precautions': 'take rest, stay hydrated, apply warm compress, avoid stress',
        'Specialist': 'General Physician',
        'Is_Emergency': False
    }
]

# Update if already exists, otherwise append
for row in custom_rows:
    disease = row['Disease']
    if disease in df['Disease'].values:
        print(f"Updating existing custom disease: {disease}")
        # Overwrite the row's values
        idx = df[df['Disease'] == disease].index[0]
        df.at[idx, 'Symptom'] = row['Symptom']
        df.at[idx, 'Description'] = row['Description']
        df.at[idx, 'Precautions'] = row['Precautions']
        df.at[idx, 'Specialist'] = row['Specialist']
        df.at[idx, 'Is_Emergency'] = row['Is_Emergency']
    else:
        print(f"Adding new custom disease: {disease}")
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

# Save both to keep dataset synced
df.to_csv(csv_path, index=False)
df.to_csv(backup_path, index=False)
print("Dataset updated and synced with backup successfully.")
