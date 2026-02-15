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
# MongoDB URI-ல் /MSJ என்பதைச் சேர்த்துள்ளேன் (இது மிக முக்கியம்)
MONGO_URI = "mongodb+srv://admin:ms2007@msj.ooyv80e.mongodb.net/?appName=MSJ"
GEMINI_API_KEY = "AIzaSyBcgTlSXNvDNs6U8jwAr_KBOd7uxS0mKO4"

# Setup DB
db = None
projects_collection = None

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database("MSJ")  # Database-ஐ நேரடியாக எடுக்கிறோம்
    projects_collection = db["projects"]  # Collection-ஐ ஒரு அகராதி போல (Dictionary) எடுக்கிறோம்
    # ஒரு முறை பிங் (Ping) செய்து கனெக்ஷனை உறுதி செய்கிறோம்
    client.admin.command('ping')
    print("✅ Database Connected & Verified!")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")

# Setup AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ AI System Ready!")
except Exception as e:
    print(f"❌ AI Setup Failed: {e}")


# --- ROUTES ---

@app.route('/generate_roadmap', methods=['POST'])
def generate_roadmap():
    try:
        data = request.json
        title = data.get("title")
        prompt = f"Create a checklist of 5 to 7 short, actionable steps to complete the project: '{title}'. Return ONLY a valid JSON array of strings (e.g., ['Step 1', 'Step 2']). Do not use Markdown."
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text.replace("```json", "").replace("```", "")
        tasks = json.loads(text)
        return jsonify({"tasks": tasks}), 200
    except Exception as e:
        print(f"🔥 AI Route Error: {e}")  # Render Logs-ல் எரர் தெரியும்
        return jsonify({"error": str(e), "tasks": ["Plan manually"]}), 500


@app.route('/create_project', methods=['POST'])
def create_project():
    try:
        if projects_collection is None:
            raise Exception("Database collection not initialized")

        data = request.json
        new_project = {
            "user_email": data.get("user"),
            "title": data.get("title"),
            "color": data.get("color", "#bb86fc"),
            "tasks": [{"text": t, "done": False} for t in data.get("tasks", [])],
            "progress": 0,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        result = projects_collection.insert_one(new_project)
        return jsonify({"message": "Project Created!", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print(f"🔥 Create Project Error: {e}")  # இதுதான் 500 எரருக்கான காரணம்
        return jsonify({"error": str(e)}), 500


@app.route('/get_projects', methods=['GET'])
def get_projects():
    try:
        if projects_collection is None:
            return jsonify([]), 200  # DB இல்லை என்றால் வெற்று லிஸ்ட் அனுப்பு

        user_email = request.args.get('user')
        projects = []
        cursor = projects_collection.find({"user_email": user_email}).sort("created_at", -1)
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            projects.append(doc)
        return jsonify(projects), 200
    except Exception as e:
        print(f"🔥 Get Projects Error: {e}")
        return jsonify({"error": str(e)}), 500


# Task Update Route (ObjectId கையாளுதல்)
@app.route('/update_task', methods=['POST'])
def update_task():
    try:
        data = request.json
        project_id = data.get("project_id")
        task_index = data.get("task_index")
        is_done = data.get("is_done")

        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if not project: return jsonify({"error": "Not found"}), 404

        tasks = project.get("tasks", [])
        if 0 <= task_index < len(tasks):
            tasks[task_index]["done"] = is_done

        total = len(tasks)
        completed = sum(1 for t in tasks if t["done"])
        new_progress = int((completed / total) * 100) if total > 0 else 0

        projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"tasks": tasks, "progress": new_progress}}
        )
        return jsonify({"progress": new_progress}), 200
    except Exception as e:
        print(f"🔥 Update Task Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)