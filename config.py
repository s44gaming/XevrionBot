import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
WEB_PORT = int(os.getenv("WEB_PORT", 5000))
