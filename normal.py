# normal.py
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

# Load environment variables
load_dotenv()

# --- Read required values from .env ---
user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")
host = os.getenv("MONGO_HOST")
dbname = os.getenv("DB_NAME")

# Ensure all variables exist
if not (user and password and host and dbname):
    raise RuntimeError(
        "Missing environment variables. Please set MONGO_USER, MONGO_PASS, MONGO_HOST, DB_NAME in .env"
    )

# --- URL encode username & password ---
user_enc = quote_plus(user)
pass_enc = quote_plus(password)

# --- Build the MongoDB Atlas URI (matching Atlas format) ---
MONGO_URI = (
    f"mongodb+srv://{user_enc}:{pass_enc}@{host}/"
    f"?retryWrites=true&w=majority&appName=Cluster0"
)

# --- Connect to MongoDB with Server API ---
client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()
)

# --- Select database and collection ---
db = client[dbname]
my_information = db["My information"]

# --- Helper: Convert ObjectId to string for templates ---
def fix_doc_ids(doc):
    if not doc:
        return doc
    newdoc = dict(doc)
    if "_id" in newdoc:
        newdoc["_id"] = str(newdoc["_id"])
    return newdoc

# --- Ping function for connection testing ---
def ping():
    return client.admin.command("ping")