from flask import Flask, request, jsonify
from flask_cors import CORS
from db import alumni_collection, jobs_collection, events_collection # Ensure db.py has these
from bson.objectid import ObjectId 

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import wraps 
import jwt 
from flask_bcrypt import Bcrypt 

load_dotenv()

app = Flask(__name__)
CORS(app) 

# --- CRITICAL FIX FOR SECRET_KEY ---
# Yeh code SECRET_KEY ko load karta hai. Agar .env se nahi mili, toh fallback key use karega.
secret_key = os.getenv('SECRET_KEY') 
if not secret_key:
    print("WARNING: SECRET_KEY not found in .env! Using a fallback development key. FIX YOUR .ENV FILE.")
    # Agar key nahi milti hai, toh yeh string use hogi aur login chal jaayega.
    secret_key = 'temporary_development_fallback_key_use_env_instead_898'
    
app.config['SECRET_KEY'] = secret_key
# --- END CRITICAL FIX ---

bcrypt = Bcrypt(app)


# --- 1. UTILITY: JWT Token Required Decorator (Protected Routes Ke Liye) ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Headers mein Authorization: Bearer <token> dhoondhein
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'msg': 'Token is missing!'}), 401

        try:
            # Token ko decode karein
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_alumni = alumni_collection.find_one({'_id': ObjectId(data['user_id'])})
            
        except Exception as e:
            return jsonify({'msg': 'Token is invalid or expired!'}), 401

        return f(current_alumni, *args, **kwargs)

    return decorated
# --------------------------------------------------------------------------


# --- 2. AUTHENTICATION & PROFILE ROUTES ---

@app.route('/', methods=['GET'])
def home():
    """Server status check ke liye basic route."""
    return "Alumni Sathi Flask Backend (COMPLETE) is Running!", 200

@app.route('/api/alumni/register', methods=['POST'])
def register_alumni():
    data = request.json
    
    required_fields = ['fullName', 'email', 'graduationYear', 'password'] 
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required fields (Full Name, Email, Year, Password)"}), 400

    email = data.get('email')
    password = data.get('password')

    try:
        if alumni_collection.find_one({"email": email}):
            return jsonify({"msg": "Alumni with this email is already registered."}), 409

        # Password ko hash karein
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_alumni = {
            "fullName": data.get('fullName'),
            "email": email,
            "graduationYear": data.get('graduationYear'),
            "password": hashed_password, 
            "message": data.get('message', ''),
            "registrationDate": datetime.now()
        }

        alumni_collection.insert_one(new_alumni)
        
        return jsonify({"msg": "Registration successful! You can now log in."}), 201

    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"msg": "Server Error. Could not process registration."}), 500


@app.route('/api/alumni/login', methods=['POST'])
def login_alumni():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    alumni = alumni_collection.find_one({"email": email})

    if not alumni or not bcrypt.check_password_hash(alumni['password'], password):
        return jsonify({"msg": "Invalid credentials"}), 401

    try:
        token_payload = {
            'user_id': str(alumni['_id']),
            'email': alumni['email'],
            'exp': datetime.utcnow() + timedelta(days=1) 
        }
        
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            "msg": "Login successful",
            "token": token
        }), 200

    except Exception as e:
        print(f"Error creating JWT token: {e}")
        return jsonify({"msg": "Login failed due to server error"}), 500


@app.route('/api/user/profile', methods=['GET'])
@token_required 
def get_user_profile(current_alumni):
    """Authenticated user ka profile data return karta hai."""
    
    profile_data = {
        "id": str(current_alumni['_id']),
        "fullName": current_alumni['fullName'],
        "email": current_alumni['email'],
        "graduationYear": current_alumni['graduationYear'],
        "registrationDate": current_alumni['registrationDate'].strftime("%Y-%m-%d")
    }

    return jsonify(profile_data), 200


# --- 3. STATS ROUTE ---
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Database se real-time statistics fetch karta hai."""
    try:
        active_alumni_count = alumni_collection.count_documents({})

        stats_data = {
            "activeAlumni": active_alumni_count, 
            "companiesConnected": jobs_collection.count_documents({}), 
            "jobPlacements": 850, 
            "eventsHosted": events_collection.count_documents({}) 
        }
        
        return jsonify(stats_data), 200

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"msg": "Could not retrieve statistics."}), 500


# --- 4. JOBS ROUTES (Career Hub) ---
@app.route('/api/jobs', methods=['POST'])
@token_required
def create_job(current_alumni):
    data = request.json
    required_fields = ['title', 'company', 'location', 'description']
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required job details."}), 400

    new_job = {
        "title": data.get('title'),
        "company": data.get('company'),
        "location": data.get('location'),
        "description": data.get('description'),
        "postedBy": str(current_alumni['_id']),
        "postDate": datetime.now()
    }
    jobs_collection.insert_one(new_job)
    return jsonify({"msg": "Job posted successfully to Career Hub."}), 201


@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    jobs_list = []
    for job in jobs_collection.find().sort("postDate", -1):
        job['_id'] = str(job['_id'])
        jobs_list.append(job)
    return jsonify(jobs_list), 200


# --- 5. EVENTS ROUTES (Events & Reunions) ---
@app.route('/api/events', methods=['POST'])
@token_required
def create_event(current_alumni):
    data = request.json
    required_fields = ['title', 'date', 'location']
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required event details (Title, Date, Location)."}), 400
    
    try:
        event_date = datetime.strptime(data.get('date'), '%Y-%m-%dT%H:%M:%S.%fZ')
    except:
        return jsonify({"msg": "Invalid date format. Use ISO 8601 (e.g., 2025-12-31T10:00:00.000Z)."}), 400

    new_event = {
        "title": data.get('title'),
        "date": event_date,
        "location": data.get('location'),
        "description": data.get('description', 'No description provided.'),
        "postedBy": str(current_alumni['_id']), 
        "postDate": datetime.now()
    }
    events_collection.insert_one(new_event)
    return jsonify({"msg": "Event posted successfully."}), 201


@app.route('/api/events', methods=['GET'])
def get_all_events():
    events_list = []
    for event in events_collection.find({"date": {"$gte": datetime.now()}}).sort("date", 1):
        event['_id'] = str(event['_id'])
        event['date'] = event['date'].isoformat() 
        events_list.append(event)
    return jsonify(events_list), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)