import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, 'symptoms_dataset.csv')

df = pd.read_csv(csv_path)

custom_rows = [
    {
        'Disease': 'Work Pressure / Tension',
        'Symptom': 'headache shoulder pain neck pain back pain eye strain stress',
        'Description': 'Prolonged sitting, screen time, and work pressure (common in IT workers) often lead to tension headaches and musculoskeletal pain in the shoulders and neck.',
        'Precautions': 'take frequent screen breaks, improve ergonomic posture, do neck and shoulder stretches, stay hydrated',
        'Specialist': 'General Physician or Physiotherapist',
        'Is_Emergency': False
    }
]

df_custom = pd.DataFrame(custom_rows)
df = pd.concat([df, df_custom], ignore_index=True)
df.to_csv(csv_path, index=False)
print("Successfully appended Work Pressure dataset row.")
