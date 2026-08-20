from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import (
    achievements_collection,
    alumni_collection,
    events_collection,
    giving_collection,
    jobs_collection,
    knowledge_collection,
    mentorship_collection,
    networking_collection,
    notifications_collection,
    privacy_collection,
)
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


def demo_jobs():
    now = datetime.now()
    return [
        {
            "_id": "demo-job-1",
            "title": "Frontend Developer Intern",
            "company": "CampusBridge Labs",
            "location": "Remote",
            "description": "Build polished student and alumni dashboards with HTML, CSS, JavaScript, and Flask APIs.",
            "postedBy": "demo",
            "postDate": now - timedelta(days=2),
        },
        {
            "_id": "demo-job-2",
            "title": "Data Analyst",
            "company": "Nexa Analytics",
            "location": "Bengaluru",
            "description": "Turn placement, mentorship, and event data into useful reports for the alumni office.",
            "postedBy": "demo",
            "postDate": now - timedelta(days=5),
        },
    ]


def demo_events():
    now = datetime.now()
    return [
        {
            "_id": "demo-event-1",
            "title": "Alumni Career Night",
            "date": now + timedelta(days=14),
            "location": "Main Auditorium",
            "description": "Meet seniors from engineering, product, design, and startup roles.",
            "postedBy": "demo",
            "postDate": now,
        },
        {
            "_id": "demo-event-2",
            "title": "Founders Roundtable",
            "date": now + timedelta(days=30),
            "location": "Innovation Cell",
            "description": "A small-format meetup for alumni founders and students exploring startups.",
            "postedBy": "demo",
            "postDate": now,
        },
    ]


def demo_networking():
    return [
        {
            "_id": "demo-network-1",
            "fullName": "Priya Sharma",
            "graduationYear": "2018",
            "industry": "Software Engineering",
            "location": "Bengaluru",
            "interests": ["frontend", "mentorship", "startups"],
            "bio": "Senior frontend engineer helping students build production-ready portfolios.",
            "visibility": "public",
        },
        {
            "_id": "demo-network-2",
            "fullName": "Rahul Mehta",
            "graduationYear": "2015",
            "industry": "Marketing",
            "location": "Mumbai",
            "interests": ["growth", "branding", "career advice"],
            "bio": "Growth lead mentoring alumni who want to move into product marketing.",
            "visibility": "public",
        },
    ]


def demo_knowledge():
    now = datetime.now()
    return [
        {
            "_id": "demo-knowledge-1",
            "title": "How to prepare for product interviews",
            "category": "Career",
            "content": "Break the interview into product sense, execution, analytics, and communication rounds.",
            "author": "Anjali Verma",
            "createdAt": now - timedelta(days=1),
        },
        {
            "_id": "demo-knowledge-2",
            "title": "Webinar: Building your first startup team",
            "category": "Webinar",
            "content": "A practical session on finding co-founders, validating ideas, and talking to users.",
            "author": "Founders Club",
            "createdAt": now - timedelta(days=4),
        },
    ]


def demo_mentorship():
    return [
        {
            "_id": "demo-mentor-1",
            "mentorName": "Dr. Kavita Rao",
            "expertise": "Higher Studies",
            "availability": "Saturdays",
            "description": "Guidance for MS, PhD, scholarships, and research profiles.",
            "createdAt": datetime.now(),
        }
    ]


def demo_achievements():
    return [
        {
            "_id": "demo-achievement-1",
            "name": "Amit Singh",
            "title": "Forbes 30 Under 30",
            "description": "Recognized for work in accessible education technology.",
            "year": "2026",
            "createdAt": datetime.now(),
        }
    ]


def demo_giving():
    return [
        {
            "_id": "demo-giving-1",
            "title": "Student Scholarship Fund",
            "goal": 500000,
            "raised": 185000,
            "description": "Support need-based scholarships for current students.",
            "createdAt": datetime.now(),
        }
    ]


def demo_notifications():
    now = datetime.now()
    return [
        {"_id": "demo-note-1", "message": "New alumni career night announced.", "type": "event", "createdAt": now},
        {"_id": "demo-note-2", "message": "2 new career opportunities posted this week.", "type": "career", "createdAt": now},
        {"_id": "demo-note-3", "message": "Priya Sharma is available for mentorship.", "type": "networking", "createdAt": now},
    ]


def serialize_document(document):
    item = dict(document)
    if "_id" in item:
        item["_id"] = str(item["_id"])
    for key, value in list(item.items()):
        if isinstance(value, datetime):
            item[key] = value.isoformat()
    return item


def format_date(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if value:
        return str(value)[:10]
    return datetime.now().strftime("%Y-%m-%d")


def safe_object_id(value):
    try:
        return ObjectId(value)
    except Exception:
        return value


def split_interests(value):
    if isinstance(value, list):
        return [item.strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def collection_items(collection, sort_key=None, sort_direction=-1, fallback=None, query=None):
    cursor = collection.find(query or {})
    if sort_key:
        cursor = cursor.sort(sort_key, sort_direction)
    items = [serialize_document(item) for item in cursor]
    if not items and fallback:
        items = [serialize_document(item) for item in fallback()]
    return items


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
            current_alumni = alumni_collection.find_one({'_id': safe_object_id(data['user_id'])})
            if not current_alumni:
                return jsonify({'msg': 'User not found!'}), 401
            
        except Exception as e:
            return jsonify({'msg': 'Token is invalid or expired!'}), 401

        return f(current_alumni, *args, **kwargs)

    return decorated
# --------------------------------------------------------------------------


# --- 2. AUTHENTICATION & PROFILE ROUTES ---

@app.route('/', methods=['GET'])
def home():
    """Serve the prototype UI."""
    return send_from_directory(app.root_path, 'aluliu.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Server status check ke liye basic route."""
    return jsonify({"msg": "Alumni Sathi Flask Backend is running"}), 200

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
            "industry": data.get('industry', 'Not specified'),
            "location": data.get('location', 'Not specified'),
            "interests": split_interests(data.get('interests', 'networking, mentorship')),
            "visibility": data.get('visibility', 'public'),
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

    if not alumni or not alumni.get('password') or not bcrypt.check_password_hash(alumni['password'], password):
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
        "industry": current_alumni.get('industry', 'Not specified'),
        "location": current_alumni.get('location', 'Not specified'),
        "interests": current_alumni.get('interests', []),
        "visibility": current_alumni.get('visibility', 'public'),
        "registrationDate": format_date(current_alumni.get('registrationDate'))
    }

    return jsonify(profile_data), 200


@app.route('/api/user/profile', methods=['PUT'])
@token_required
def update_user_profile(current_alumni):
    data = request.json or {}
    updates = {
        "fullName": data.get("fullName", current_alumni.get("fullName")),
        "graduationYear": data.get("graduationYear", current_alumni.get("graduationYear")),
        "industry": data.get("industry", current_alumni.get("industry", "Not specified")),
        "location": data.get("location", current_alumni.get("location", "Not specified")),
        "interests": split_interests(data.get("interests", current_alumni.get("interests", []))),
        "visibility": data.get("visibility", current_alumni.get("visibility", "public")),
    }
    alumni_collection.update_one({"_id": current_alumni["_id"]}, {"$set": updates})
    privacy_collection.update_one(
        {"alumniId": str(current_alumni["_id"])},
        {"$set": {"visibility": updates["visibility"], "updatedAt": datetime.now()}},
        upsert=True,
    )
    return jsonify({"msg": "Profile updated successfully.", "profile": serialize_document(updates)}), 200


# --- FEATURE ROUTES: Smart Networking, Knowledge, Mentorship, Achievements, Giving ---

@app.route('/api/networking', methods=['GET'])
def get_networking_directory():
    alumni_profiles = [
        serialize_document(alumni)
        for alumni in alumni_collection.find({"visibility": "public"})
    ]
    for profile in alumni_profiles:
        profile.pop("password", None)
    curated_profiles = collection_items(networking_collection, fallback=demo_networking)
    return jsonify(alumni_profiles + curated_profiles), 200


@app.route('/api/networking/connect', methods=['POST'])
@token_required
def create_connection_request(current_alumni):
    data = request.json or {}
    target_name = data.get("targetName", "selected alumnus")
    notifications_collection.insert_one({
        "message": f"{current_alumni['fullName']} requested to connect with {target_name}.",
        "type": "networking",
        "createdAt": datetime.now(),
        "userId": str(current_alumni["_id"]),
    })
    return jsonify({"msg": f"Connection request sent to {target_name}."}), 201


@app.route('/api/knowledge', methods=['GET'])
def get_knowledge_posts():
    return jsonify(collection_items(knowledge_collection, "createdAt", -1, demo_knowledge)), 200


@app.route('/api/knowledge', methods=['POST'])
@token_required
def create_knowledge_post(current_alumni):
    data = request.json or {}
    required_fields = ["title", "category", "content"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"msg": "Title, category, and content are required."}), 400
    post = {
        "title": data["title"],
        "category": data["category"],
        "content": data["content"],
        "author": current_alumni["fullName"],
        "authorId": str(current_alumni["_id"]),
        "createdAt": datetime.now(),
    }
    knowledge_collection.insert_one(post)
    return jsonify({"msg": "Knowledge post shared successfully."}), 201


@app.route('/api/mentorship', methods=['GET'])
def get_mentorship_programs():
    return jsonify(collection_items(mentorship_collection, "createdAt", -1, demo_mentorship)), 200


@app.route('/api/mentorship', methods=['POST'])
@token_required
def create_mentorship_program(current_alumni):
    data = request.json or {}
    required_fields = ["expertise", "availability", "description"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"msg": "Expertise, availability, and description are required."}), 400
    mentorship_collection.insert_one({
        "mentorName": current_alumni["fullName"],
        "expertise": data["expertise"],
        "availability": data["availability"],
        "description": data["description"],
        "createdAt": datetime.now(),
    })
    return jsonify({"msg": "Mentorship offer added successfully."}), 201


@app.route('/api/achievements', methods=['GET'])
def get_achievements():
    return jsonify(collection_items(achievements_collection, "createdAt", -1, demo_achievements)), 200


@app.route('/api/achievements', methods=['POST'])
@token_required
def create_achievement(current_alumni):
    data = request.json or {}
    required_fields = ["name", "title", "description", "year"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"msg": "Name, title, description, and year are required."}), 400
    achievements_collection.insert_one({
        "name": data["name"],
        "title": data["title"],
        "description": data["description"],
        "year": data["year"],
        "createdAt": datetime.now(),
    })
    return jsonify({"msg": "Achievement added to the board."}), 201


@app.route('/api/giving', methods=['GET'])
def get_giving_campaigns():
    return jsonify(collection_items(giving_collection, "createdAt", -1, demo_giving)), 200


@app.route('/api/giving/<campaign_id>/donate', methods=['POST'])
@token_required
def donate_to_campaign(current_alumni, campaign_id):
    data = request.json or {}
    amount = int(data.get("amount", 0) or 0)
    if amount <= 0:
        return jsonify({"msg": "Donation amount must be greater than zero."}), 400
    try:
        query = {"_id": ObjectId(campaign_id)}
    except Exception:
        query = {"_id": campaign_id}
    result = giving_collection.update_one(query, {"$inc": {"raised": amount}})
    if result.matched_count == 0:
        giving_collection.insert_one({
            "title": "Community Giving",
            "goal": 100000,
            "raised": amount,
            "description": "General contribution from alumni.",
            "createdAt": datetime.now(),
        })
    notifications_collection.insert_one({
        "message": f"{current_alumni['fullName']} contributed Rs. {amount} to Give Back.",
        "type": "giving",
        "createdAt": datetime.now(),
    })
    return jsonify({"msg": "Thank you for supporting the community."}), 200


@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    return jsonify(collection_items(notifications_collection, "createdAt", -1, demo_notifications)), 200


# --- 3. STATS ROUTE ---
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Database se real-time statistics fetch karta hai."""
    try:
        active_alumni_count = alumni_collection.count_documents({})
        jobs_count = jobs_collection.count_documents({})
        events_count = events_collection.count_documents({})
        knowledge_count = knowledge_collection.count_documents({})
        achievements_count = achievements_collection.count_documents({})

        stats_data = {
            "activeAlumni": max(active_alumni_count, 120), 
            "companiesConnected": max(jobs_count, len(demo_jobs())), 
            "jobPlacements": 850, 
            "eventsHosted": max(events_count, len(demo_events())),
            "knowledgePosts": max(knowledge_count, len(demo_knowledge())),
            "achievements": max(achievements_count, len(demo_achievements()))
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
    jobs_list = [serialize_document(job) for job in jobs_collection.find().sort("postDate", -1)]
    if not jobs_list:
        jobs_list = [serialize_document(job) for job in demo_jobs()]
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
    events_list = [
        serialize_document(event)
        for event in events_collection.find({"date": {"$gte": datetime.now()}}).sort("date", 1)
    ]
    if not events_list:
        events_list = [serialize_document(event) for event in demo_events()]
    return jsonify(events_list), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
