import pymongo
from django.conf import settings

# Initialize MongoDB Client
# Default connection to local MongoDB instance
client = pymongo.MongoClient('mongodb://localhost:27017/')

# Select the database
db = client['ai_healthcare_assist']

# We can access collections like this:
# users_collection = db['users']
# hospitals_collection = db['hospitals']
# symptoms_collection = db['symptoms']
