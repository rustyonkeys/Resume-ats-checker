# import psycopg2
#using sqlalchemy to connect to the db instead of psycopg2 as it used for exectuting sql manually

from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured in .env")