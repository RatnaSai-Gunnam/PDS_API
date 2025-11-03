import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_UNITS = os.getenv("OPENWEATHER_UNITS", "imperial")
