from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['rental_platform']
users_collection = db['users']
properties_collection = db['properties']