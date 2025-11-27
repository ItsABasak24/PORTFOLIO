# api/normal.py
import os
from urllib.parse import quote_plus
from pymongo import MongoClient
import certifi

# Only load .env for local dev (Vercel uses env vars)
if os.getenv("VERCEL") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

# Prefer a single environment variable MONGO_URI (easier for Vercel)
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASS")
    host = os.getenv("MONGO_HOST")
    dbname = os.getenv("DB_NAME")

    if not (user and password and host and dbname):
        # Do not raise at import: that would crash app import on some environments.
        # Instead set placeholders so app can handle missing config gracefully.
        client = None
        db = None
        my_information = None
    else:
        user_enc = quote_plus(user)
        pass_enc = quote_plus(password)
        MONGO_URI = f"mongodb+srv://{user_enc}:{pass_enc}@{host}/{dbname}?retryWrites=true&w=majority"
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        db = client[dbname]
        my_information = db.get_collection("My information")  # choose a simple name (no spaces)
else:
    # If MONGO_URI provided, use it
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        dbname = os.getenv("DB_NAME")
        db = client[dbname] if dbname else client.get_default_database()
        my_information = db.get_collection("My information")
    except Exception:
        client = None
        db = None
        my_information = None

def fix_doc_ids(doc):
    if not doc:
        return doc
    newdoc = dict(doc)
    if "_id" in newdoc:
        newdoc["_id"] = str(newdoc["_id"])
    return newdoc

def ping():
    if client is None:
        raise RuntimeError("Mongo client not configured")
    return client.admin.command("ping")
