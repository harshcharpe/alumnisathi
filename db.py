# db.py (UPDATED)

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# .env file se MONGO_URI load karein
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

try:
    # Client banaayein aur database se connect karein
    client = MongoClient(MONGO_URI)
    db = client.get_database() # Ya client.alumni_sathi bhi kar sakte hain

    # Connection check
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB (Local)!")

    # --- COLLECTIONS ---
    # 1. Alumni collection (Registration, Login, Profile data)
    alumni_collection = db.alumni 
    
    # 2. Jobs collection (Job Postings ke liye)
    jobs_collection = db.jobs 
    
    # 3. Events collection (Reunions aur Workshops ke liye)
    events_collection = db.events 
    # --- END COLLECTIONS ---

except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    # Agar connection fail ho toh, yahan error dega
    import sys
    sys.exit(1)