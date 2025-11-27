# # api/normal.py
# import os
# from urllib.parse import quote_plus
# from pymongo import MongoClient
# import certifi

# # Only load .env for local dev (Vercel uses env vars)
# if os.getenv("VERCEL") is None:
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#     except Exception:
#         pass

# # Prefer a single environment variable MONGO_URI (easier for Vercel)
# MONGO_URI = os.getenv("MONGO_URI")
# if not MONGO_URI:
#     user = os.getenv("MONGO_USER")
#     password = os.getenv("MONGO_PASS")
#     host = os.getenv("MONGO_HOST")
#     dbname = os.getenv("DB_NAME")

#     if not (user and password and host and dbname):
#         # Do not raise at import: that would crash app import on some environments.
#         # Instead set placeholders so app can handle missing config gracefully.
#         client = None
#         db = None
#         my_information = None
#     else:
#         user_enc = quote_plus(user)
#         pass_enc = quote_plus(password)
#         MONGO_URI = f"mongodb+srv://{user_enc}:{pass_enc}@{host}/{dbname}?retryWrites=true&w=majority"
#         client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
#         db = client[dbname]
#         my_information = db.get_collection("My information")  # choose a simple name (no spaces)
# else:
#     # If MONGO_URI provided, use it
#     try:
#         client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
#         dbname = os.getenv("DB_NAME")
#         db = client[dbname] if dbname else client.get_default_database()
#         my_information = db.get_collection("My information")
#     except Exception:
#         client = None
#         db = None
#         my_information = None

# def fix_doc_ids(doc):
#     if not doc:
#         return doc
#     newdoc = dict(doc)
#     if "_id" in newdoc:
#         newdoc["_id"] = str(newdoc["_id"])
#     return newdoc

# def ping():
#     if client is None:
#         raise RuntimeError("Mongo client not configured")
#     return client.admin.command("ping")

# api/normal.py
"""
Central DB module for the app.

- Exposes `client`, `db`, and `my_information` at module level so other modules can do:
    from . import normal
    normal.my_information.insert_one(...)
- Provides `fix_doc_ids()` for template-friendly documents.
- Provides a safe `admin_credentials()` helper that will upsert admin credentials
  only when called (not on import).
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

# Load .env from project root (do this once here)
load_dotenv()

# Read required values from environment
user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
host = os.getenv("MONGO_HOST")
dbname = os.getenv("DB_NAME")

if not (user and password and host and dbname):
    # Fail early with a clear message for local testing.
    # In production (Vercel) set these as environment variables in project settings.
    raise RuntimeError(
        "Missing env vars. Set MONGO_USER, MONGO_PASS, MONGO_HOST, DB_NAME in .env or Vercel env."
    )

# URL encode the username/password
user_enc = quote_plus(user)
pass_enc = quote_plus(password)

MONGO_URI = (
    f"mongodb+srv://{user_enc}:{pass_enc}@{host}/"
    f"?retryWrites=true&w=majority&appName=Cluster0"
)

# Create Mongo client once (module import)
client = MongoClient(
    MONGO_URI,
    server_api=ServerApi("1"),
    tlsCAFile=certifi.where(),
)

# Database and collection exported for other modules
db = client[dbname]
my_information = db["My information"]  # keep the name your app expects

def fix_doc_ids(doc):
    """Return a shallow copy with _id converted to string (safe for templates)."""
    if not doc:
        return doc
    newdoc = dict(doc)
    if "_id" in newdoc:
        newdoc["_id"] = str(newdoc["_id"])
    return newdoc

def ping():
    """Simple ping to check the DB connection."""
    return client.admin.command("ping")

def admin_credentials(admin_user: str | None = None, admin_pass: str | None = None):
    """
    Upsert hashed admin credentials into the same collection.
    Call this manually (don't call on import).
    This uses a single document with type='admin' to avoid duplicates.
    """
    # Use provided args or fall back to env
    ADMIN_USER = admin_user or os.getenv("ADMIN_USER")
    ADMIN_PASS = admin_pass or os.getenv("ADMIN_PASS")

    if not (ADMIN_USER and ADMIN_PASS):
        raise RuntimeError("Admin username/password not provided (env or args).")

    admin_doc = {
        "type": "admin_credentials",
        "ADMIN_USER_HASH": hash(ADMIN_USER),
        "ADMIN_PASS_HASH": hash(ADMIN_PASS),
        # optional: store when updated
        "updated_at": __import__("datetime").datetime.utcnow(),
    }

    # Upsert the single admin doc (so repeated calls don't insert duplicates)
    res = my_information.update_one(
        {"type": "admin_credentials"},
        {"$set": admin_doc},
        upsert=True
    )
    return res
