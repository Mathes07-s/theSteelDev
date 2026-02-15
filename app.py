import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import certifi

app = Flask(__name__)
CORS(app)

# --- GLOBAL VARIABLES ---
entries_collection = None
connect_error = None

# --- FORCE CONNECTION (Hardcoded) ---
# We are putting the password directly here to bypass the error
MONGO_URI = "mongodb+srv://admin:steel2007@msj.ooyv80e.mongodb.net/?retryWrites=true&w=majority&appName=MSJ"

try:
    print("⏳ Attempting to connect to MongoDB...")

    # Connect using the hardcoded string and the certificate fix
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

    # Test the connection immediately
    client.admin.command('ping')

    db = client.MSJ
    entries_collection = db.journal_entries
    print("✅ Successfully connected to MongoDB Atlas!")

except Exception as e:
    connect_error = str(e)
    print(f"❌ Error connecting to MongoDB: {e}")


# --- ROUTES ---
@app.route('/')
def home():
    if entries_collection is not None:
        return "Journal API is LIVE and Connected! 🚀"
    else:
        return f"Journal API is Running, but Database Failed: {connect_error}"


@app.route('/add', methods=['POST'])
def add_entry():
    if entries_collection is None:
        return jsonify({"error": f"Database Connection Failed. Reason: {connect_error}"}), 500

    try:
        data = request.json
        entry = {
            "content": data.get("content"),
            "user_email": data.get("user"),  # <--- NEW: Stores your Google Email
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        result = entries_collection.insert_one(entry)
        return jsonify({"message": "Saved successfully!", "id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get', methods=['GET'])
def get_entries():
    if entries_collection is None:
        return jsonify({"error": f"Database Connection Failed. Reason: {connect_error}"}), 500

    try:
        # Get the email from the URL (e.g., /get?user=example@gmail.com)
        user_email = request.args.get('user')

        # Filter: Only find notes that belong to THIS user
        query = {"user_email": user_email} if user_email else {}

        all_entries = []
        cursor = entries_collection.find(query).sort("timestamp", -1).limit(50)
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            all_entries.append(doc)
        return jsonify(all_entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)