# api/temp.py
import os
import certifi
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# load dotenv only for local dev
if os.getenv("VERCEL") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

# Use normal.my_information if present, otherwise build a temporary client
def _get_collection():
    try:
        # try to import the shared connector
        from . import normal
        if getattr(normal, "my_information", None):
            return normal.my_information
    except Exception:
        pass

    # fallback: build client from env (used rarely)
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASS")
    host = os.getenv("MONGO_HOST")
    dbname = os.getenv("DB_NAME", "test")
    if not (user and password and host):
        return None

    user_enc = quote_plus(user)
    pass_enc = quote_plus(password)
    uri = f"mongodb+srv://{user_enc}:{pass_enc}@{host}/{dbname}?retryWrites=true&w=majority"
    client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = client[dbname]
    return db.get_collection("My information")

def admin_credentials():
    """Create/update admin credentials (idempotent). Safe to call many times."""
    try:
        coll = _get_collection()
        if coll is None:
            print("admin_credentials: no MongoDB collection available (env not configured).")
            return

        ADMIN_USER = os.getenv("ADMIN_USER", "admin")
        ADMIN_PASS = os.getenv("ADMIN_PASS", "changeme")

        admin_doc = {"username": ADMIN_USER, "password_hash": str(hash(ADMIN_PASS))}
        coll.update_one({"username": ADMIN_USER}, {"$set": admin_doc}, upsert=True)
        print("admin_credentials: upsert completed.")
    except PyMongoError as e:
        print("admin_credentials: pymongo error:", e)
    except Exception as e:
        print("admin_credentials: unexpected error:", e)
