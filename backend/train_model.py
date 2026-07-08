import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
import os

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, 'symptoms_dataset.csv')

# Load the dataset
data = pd.read_csv(csv_path)

# Prepare training data
X = data['Symptom']
# We'll predict both Specialist and Is_Emergency combined, or build two models.
# Let's build a model for Specialist, and handle emergencies via rule-based keyword matching or a second model.
y_specialist = data['Specialist']

# Create a pipeline that vectorizes the text and then trains a Naive Bayes classifier
model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), MultinomialNB())

# Train the model
model.fit(X, y_specialist)

# Save the model
model_path = os.path.join(BASE_DIR, 'nlp_model.pkl')
joblib.dump(model, model_path)

print("Model trained and saved successfully at", model_path)
