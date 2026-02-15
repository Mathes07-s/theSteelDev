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
# Render Environment Variable-ல் இருந்து Key-ஐ எடுக்கும்
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MONGO_URI = "mongodb+srv://admin:ms2007@msj.ooyv80e.mongodb.net/MSJ?retryWrites=true&w=majority&appName=MSJ"

# Setup DB
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database("MSJ")
    projects_collection = db["projects"]
    print("✅ Database Connected!")
except Exception as e:
    print(f"❌ Database Error: {e}")

# Setup AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # நாம் பயன்படுத்தப் போவது Gemini 2.0 Flash
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("✅ AI System Ready (Using gemini-2.0-flash)!")
except Exception as e:
    print(f"❌ AI Setup Failed: {e}")


# --- ROUTES ---

@app.route('/')
def home():
    return "SteelDev AI Server is Running! 🚀"


@app.route('/generate_roadmap', methods=['POST'])
def generate_roadmap():
    try:
        data = request.json
        title = data.get("title")

        # Prompt
        prompt = f"Create a checklist of 5 short steps for: '{title}'. Return ONLY a JSON list of strings. Example: [\"Step 1\", \"Step 2\"]"

        # AI-ஐ அழைப்பது
        response = model.generate_content(prompt)

        text = response.text.strip()
        # Clean JSON formatting
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "")
        elif text.startswith("```"):
            text = text.replace("```", "")

        tasks = json.loads(text)
        return jsonify({"tasks": tasks}), 200

    except Exception as e:  # <--- நீங்க மிஸ் பண்ணது இதுதான்!
        print(f"🔥 AI Route Error: {e}")
        # AI எரர் வந்தாலும் ஆப் நிற்காது
        return jsonify({"tasks": [f"Error: {str(e)}", "Plan Manually"]}), 200


@app.route('/create_project', methods=['POST'])
def create_project():
    try:
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
        return jsonify({"error": str(e)}), 500


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


@app.route('/update_task', methods=['POST'])
def update_task():
    try:
        data = request.json
        project_id = data.get("project_id")
        task_index = data.get("task_index")
        is_done = data.get("is_done")

        project = projects_collection.find_one({"_id": ObjectId(project_id)})
        if project:
            tasks = project.get("tasks", [])
            if 0 <= task_index < len(tasks):
                tasks[task_index]["done"] = is_done

            total = len(tasks)
            completed = sum(1 for t in tasks if t["done"])
            progress = int((completed / total) * 100) if total > 0 else 0

            projects_collection.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"tasks": tasks, "progress": progress}}
            )
            return jsonify({"progress": progress}), 200
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)