from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))

db = client["steganography_db"]

encode_logs = db["encode_logs"]
decode_logs = db["decode_logs"]
