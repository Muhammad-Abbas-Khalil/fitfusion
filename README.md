# FitFusion 🏋️ — AI-Powered Fitness Dashboard

A full-stack web application for personalized health tracking with an AI Coach.

## Features
- 📊 Dashboard with daily calories in/out tracking
- 🏃 Log workouts with sets, reps, and intensity
- 🥗 Log meals with nutritional breakdown
- 📅 Daily summary with deficit/surplus analysis
- 🤖 AI Fitness Coach powered by Hugging Face API

## Tech Stack
- **Backend:** Python, Flask, SQLAlchemy, Flask-Login
- **Database:** PostgreSQL
- **Frontend:** Tailwind CSS, Jinja2
- **AI:** Hugging Face API

## Setup
1. Clone the repo
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with `DATABASE_URL` and `HF_API_KEY`
6. Run: `python3 app.py`
