from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into the environment

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vectordb/")  # default fallback
