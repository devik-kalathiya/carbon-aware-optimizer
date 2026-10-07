import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing.")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing.")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)