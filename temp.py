import os
import dotenv 
dotenv.load_dotenv()
from pymongo import MongoClient
from urllib.parse import quote_plus
from pymongo.server_api import ServerApi
import certifi
def admin_credentials():
    ADMIN_USER = os.getenv('ADMIN_USER')
    ADMIN_PASS = os.getenv('ADMIN_PASS')
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASS")
    host = os.getenv("MONGO_HOST")
    dbname = os.getenv("DB_NAME")

    user_enc = quote_plus(user)
    pass_enc = quote_plus(password)

    MONGO_URI = (
    f"mongodb+srv://{user_enc}:{pass_enc}@{host}/"
    f"?retryWrites=true&w=majority&appName=Cluster0"
    )
    client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()
    )
    db = client[dbname]
    my_information = db["My information"]
    admin_information = {"ADMIN_PASS_HASH":hash(ADMIN_PASS), "ADMIN_USER_HASH":hash(ADMIN_USER)}
    
    my_information.insert_one(admin_information)
    print("Admin information push done.")

# admin_credentials()
