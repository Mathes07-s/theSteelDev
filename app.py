import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import certifi
from bson.objectid import ObjectId
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# 1. MongoDB Connection
MONGO_URI = "mongodb+srv://admin:steeldev2026@msj.ooyv80e.mongodb.net/?retryWrites=true&w=majority&appName=MSJ"
# 2. Gemini AI Configuration (Using your provided key)
GEMINI_API_KEY = "AIzaSyBcgTlSXNvDNs6U8jwAr_KBOd7uxS0mKO4"

# Setup DB
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.MSJ
    projects_collection = db.projects
    print("✅ Database Connected!")
except Exception as e:
    print(f"❌ Database Error: {e}")

# Setup AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ AI System Ready!")
except Exception as e:
    print(f"❌ AI Error: {e}")


# --- ROUTES ---

@app.route('/')
def home():
    return "TheSteelDev AI Server is Running! 🚀"


# 1. AI ROADMAP GENERATOR (The Magic Feature)
@app.route('/generate_roadmap', methods=['POST'])
def generate_roadmap():
    try:
        data = request.json
        title = data.get("title")

        # Ask AI to create a plan
        prompt = f"Create a checklist of 5 to 7 short, actionable steps to complete the project: '{title}'. Return ONLY a valid JSON array of strings (e.g., ['Step 1', 'Step 2']). Do not use Markdown."

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean up AI response to ensure it's valid JSON
        if text.startswith("```json"): text = text.replace("```json", "").replace("```", "")
        tasks = json.loads(text)

        return jsonify({"tasks": tasks})
    except Exception as e:
        return jsonify({"error": str(e), "tasks": ["Plan manually (AI Error)"]})


# 2. CREATE PROJECT (Save to DB)
@app.route('/create_project', methods=['POST'])
def create_project():
    try:
        data = request.json
        new_project = {
            "user_email": data.get("user"),
            "title": data.get("title"),
            "color": data.get("color", "#bb86fc"),
            "tasks": [{"text": t, "done": False} for t in data.get("tasks", [])],  # Store tasks with status
            "progress": 0,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        result = projects_collection.insert_one(new_project)
        return jsonify({"message": "Project Created!", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 3. GET PROJECTS (Load Dashboard)
@app.route('/get_projects', methods=['GET'])
def get_projects():
    try:
        user_email = request.args.get('user')
        projects = []
        cursor = projects_collection.find({"user_email": user_email}).sort("created_at", -1)
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            projects.append(doc)
        return jsonify(projects), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 4. UPDATE TASK STATUS (Check/Uncheck)
@app.route('/update_task', methods=['POST'])
def update_task():
    try:
        data = request.json
        project_id = data.get("project_id")
        task_index = data.get("task_index")
        is_done = data.get("is_done")

        # 1. Get the project
        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project: return jsonify({"error": "Project not found"}), 404

        # 2. Update the specific task
        tasks = project.get("tasks", [])
        if 0 <= task_index < len(tasks):
            tasks[task_index]["done"] = is_done

        # 3. Recalculate Progress %
        total = len(tasks)
        completed = sum(1 for t in tasks if t["done"])
        new_progress = int((completed / total) * 100) if total > 0 else 0

        # 4. Save back to DB
        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"tasks": tasks, "progress": new_progress}}
        )

        return jsonify({"progress": new_progress, "message": "Updated!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)