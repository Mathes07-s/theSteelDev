from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
import certifi  # <--- NEW IMPORT

app = Flask(__name__)
CORS(app)

# Connection String
connection_string = "mongodb+srv://admin:steeldev2026@msj.ooyv80e.mongodb.net/?retryWrites=true&w=majority&appName=MSJ"

try:
    # <--- NEW: We added tlsCAFile=certifi.where() to fix the SSL error
    client = MongoClient(connection_string, tlsCAFile=certifi.where())

    db = client.MSJ
    entries_collection = db.journal_entries
    print("✅ Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")


@app.route('/')
def home():
    return "Journal API is Running!"


@app.route('/add', methods=['POST'])
def add_entry():
    try:
        data = request.json
        entry = {
            "content": data.get("content"),
            "project": data.get("project", "General"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device": data.get("device", "Unknown")
        }
        result = entries_collection.insert_one(entry)
        return jsonify({"message": "Saved successfully!", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get', methods=['GET'])
def get_entries():
    try:
        all_entries = []
        cursor = entries_collection.find().sort("timestamp", -1).limit(50)
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            all_entries.append(doc)
        return jsonify(all_entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)