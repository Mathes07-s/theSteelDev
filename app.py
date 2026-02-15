import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import certifi

app = Flask(__name__)
CORS(app)

# --- DATABASE CONNECTION ---
# உங்களுடைய சரியான Connection String
MONGO_URI = "mongodb+srv://admin:steeldev2026@msj.ooyv80e.mongodb.net/MSJ?retryWrites=true&w=majority&appName=MSJ"

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database("MSJ")
    entries_collection = db["journal_entries"] # பழைய கலெக்ஷன்
    print("✅ Connected to Simple Journal DB!")
except Exception as e:
    print(f"❌ Database Error: {e}")

# --- ROUTES ---

@app.route('/')
def home():
    return "Simple Journal Server is Running! 🚀"

# 1. Add Entry (எழுதுவதை சேவ் செய்ய)
@app.route('/add_entry', methods=['POST'])
def add_entry():
    try:
        data = request.json
        entry = {
            "user": data.get("user"),
            "content": data.get("content"), # நீங்கள் டைப் பண்ணது
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
            "timestamp": datetime.now()
        }
        entries_collection.insert_one(entry)
        return jsonify({"message": "Saved successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Get Entries (பழையதை எடுத்து காட்ட)
@app.route('/get_entries', methods=['GET'])
def get_entries():
    try:
        user_email = request.args.get('user')
        entries = []
        # புதுசு மேல வரணும் (Sort by timestamp descending)
        cursor = entries_collection.find({"user": user_email}).sort("timestamp", -1)
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            entries.append(doc)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)