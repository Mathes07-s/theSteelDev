from pymongo import MongoClient

# REPLACE with your real password
uri = "mongodb+srv://admin:steel2007@msj.ooyv80e.mongodb.net/?retryWrites=true&w=majority&appName=MSJ"

print("⏳ Attempting to connect...")

try:
    client = MongoClient(uri)
    # This command forces a connection check immediately
    client.admin.command('ping')
    print("✅ SUCCESS! Your password is correct.")
except Exception as e:
    print("\n❌ FAILED. Here is the exact error:")
    print(e)