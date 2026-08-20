# Alumni Sathi

Alumni Sathi is a Flask and MongoDB based alumni engagement prototype. It provides a single-page frontend for alumni registration, login, networking, career opportunities, knowledge sharing, mentorship, events, achievements, giving campaigns, notifications, and privacy controls.

## Features

- Alumni registration and login with JWT authentication
- Smart Networking alumni directory with profile visibility controls
- Career Hub with job listing and authenticated job posting
- Knowledge Sharing posts for webinars, guides, and discussions
- Mentorship offers from alumni
- Events and reunions listing
- Achievement Board for alumni milestones
- Give Back campaigns with donation tracking
- Smart Notifications panel
- Responsive single-page frontend
- MongoDB support with in-memory demo fallback

## Tech Stack

- Python Flask
- MongoDB with PyMongo
- JWT authentication
- Flask-Bcrypt password hashing
- HTML, CSS, and JavaScript frontend

## Project Structure

```text
.
├── app.py          # Flask app, API routes, auth, and feature logic
├── db.py           # MongoDB connection and in-memory fallback database
├── aluliu.html     # Single-page frontend
├── .env            # Local environment variables
└── venv/           # Local Python virtual environment
```

## Setup

1. Activate the virtual environment:

```powershell
.\venv\Scripts\activate
```

2. Make sure `.env` contains:

```env
MONGO_URI="mongodb://localhost:27017/alumni_sathi"
SECRET_KEY=your_secret_key_here
```

3. Start MongoDB locally if you want persistent database storage.

The project also works without MongoDB by using in-memory demo data, but data will reset when the server restarts.

## Run

```powershell
.\venv\Scripts\python.exe app.py
```

Open:

```text
http://127.0.0.1:5000
```

## API Overview

### Auth

- `POST /api/alumni/register`
- `POST /api/alumni/login`
- `GET /api/user/profile`
- `PUT /api/user/profile`

### Features

- `GET /api/networking`
- `POST /api/networking/connect`
- `GET /api/jobs`
- `POST /api/jobs`
- `GET /api/knowledge`
- `POST /api/knowledge`
- `GET /api/mentorship`
- `POST /api/mentorship`
- `GET /api/events`
- `POST /api/events`
- `GET /api/achievements`
- `POST /api/achievements`
- `GET /api/giving`
- `POST /api/giving/<campaign_id>/donate`
- `GET /api/notifications`
- `GET /api/stats`
- `GET /api/health`

Protected `POST` and `PUT` routes require:

```text
Authorization: Bearer <jwt_token>
```

## Usage Notes

- Register a new alumni account from the frontend modal.
- Log in to unlock posting jobs, sharing knowledge, offering mentorship, adding achievements, donating, and updating privacy settings.
- Click feature cards such as Smart Networking, Career Hub, Knowledge Sharing, Give Back, and Privacy First to open the working feature workspace.

## Troubleshooting

If Flask dependencies are missing, use the project virtual environment:

```powershell
.\venv\Scripts\python.exe app.py
```

If MongoDB is not running, the app will print a warning and use demo data automatically.

If port `5000` is already busy, stop the other process or change the port in `app.py`.
