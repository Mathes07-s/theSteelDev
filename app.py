import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import certifi

app = Flask(__name__)
CORS(app)

# 1. Define the variable GLOBALLY first (so everyone can see it)
# Global variables
entries_collection = None
connect_error = "Unknown Error"  # <--- NEW VARIABLE

try:
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        mongo_uri = "mongodb+srv://admin:steeldev2026@msj.ooyv80e.mongodb.net/?retryWrites=true&w=majority&appName=MSJ"

    client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    client.admin.command('ping')

    db = client.MSJ
    entries_collection = db.journal_entries
    print("✅ Successfully connected to MongoDB Atlas!")

except Exception as e:
    connect_error = str(e)  # <--- SAVE THE ERROR
    print(f"❌ Error connecting to MongoDB: {e}")

@app.route('/')
def home():
    return "Journal API is Running!"


@app.route('/add', methods=['POST'])
def add_entry():
    # Safety Check: Did the database connect?
    if entries_collection is None:
        return jsonify({"error": f"Database Connection Failed. Reason: {str(connect_error)}"}), 500

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
    # Safety Check: Did the database connect?
    if entries_collection is None:
        return jsonify({"error": "Database not connected"}), 500

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
    # Use the PORT environment variable for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)