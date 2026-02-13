from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- DATABASE CONNECTION ---
# 1. Replace <db_password> with your ACTUAL password.
# 2. If your password has special characters like @ or :, you might need to URL encode them.
# 3. We are connecting to the "MSJ" database.
connection_string = "mongodb+srv://admin:steel2007@msj.ooyv80e.mongodb.net/?retryWrites=true&w=majority&appName=MSJ"

try:
    client = MongoClient(connection_string)
    # This will create a database named 'MSJ' if it doesn't exist
    db = client.MSJ
    entries_collection = db.journal_entries
    print("✅ Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")


@app.route('/')
def home():
    return "Journal API is Running!"


# --- ADD ENTRY (POST) ---
@app.route('/add', methods=['POST'])
def add_entry():
    try:
        data = request.json

        # Create the journal document
        entry = {
            "content": data.get("content"),
            "project": data.get("project", "General"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device": data.get("device", "Unknown")  # Optional: Track which device sent it
        }

        # Insert into MongoDB
        result = entries_collection.insert_one(entry)

        return jsonify({
            "message": "Saved successfully!",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- GET ENTRIES (GET) ---
@app.route('/get', methods=['GET'])
def get_entries():
    try:
        all_entries = []
        # Find all entries and sort by newest first (-1)
        # Limiting to 50 to keep it fast for now
        cursor = entries_collection.find().sort("timestamp", -1).limit(50)

        for doc in cursor:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string for JSON
            all_entries.append(doc)

        return jsonify(all_entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)