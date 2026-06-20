import os
import json
from supabase import create_client, Client
import redis
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.startswith("http"):
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("WARNING: Supabase URL or Key is missing/invalid. DB operations will fail.")

# Initialize Redis
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if REDIS_URL and REDIS_URL.startswith("redis"):
    # Assuming the URL is a standard redis:// or rediss:// connection string
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
elif REDIS_URL and REDIS_TOKEN and "upstash" in REDIS_URL:
    # If the user provides a REST URL but we installed standard redis, 
    # we would normally need the upstash-redis library. 
    # For now, we will assume REDIS_URL is a standard redis connection string.
    print("WARNING: Please provide a standard redis:// connection string in UPSTASH_REDIS_REST_URL.")
    r = None
else:
    r = None
    print("WARNING: Redis credentials missing. State operations will fail.")

def get_session_history(room_id: str):
    if not r: return []
    history_json = r.get(f"session:{room_id}")
    if history_json:
        return json.loads(history_json)
    return []

def append_to_session(room_id: str, role: str, content: str):
    if not r: return
    history = get_session_history(room_id)
    history.append({"role": role, "content": content})
    r.set(f"session:{room_id}", json.dumps(history))

def delete_session(room_id: str):
    if not r: return
    r.delete(f"session:{room_id}")

def create_appointment(user_phone: str, date: str, time: str):
    if not supabase: return {"error": "Database not connected"}
    # Check if slot is already booked
    existing = supabase.table("appointments").select("*").eq("date", date).eq("time", time).eq("status", "scheduled").execute()
    if existing.data and len(existing.data) > 0:
        return {"error": "Slot already booked"}
    
    # Save appointment
    data = supabase.table("appointments").insert({
        "user_phone": user_phone,
        "date": date,
        "time": time,
        "status": "scheduled"
    }).execute()
    return {"success": True, "data": data.data}

def get_user_appointments(user_phone: str):
    if not supabase: return []
    data = supabase.table("appointments").select("*").eq("user_phone", user_phone).execute()
    return data.data

def cancel_appointment_db(appointment_id: str):
    if not supabase: return False
    data = supabase.table("appointments").update({"status": "cancelled"}).eq("id", appointment_id).execute()
    return True

def modify_appointment_db(appointment_id: str, new_date: str, new_time: str):
    if not supabase: return {"error": "Database not connected"}
    existing = supabase.table("appointments").select("*").eq("date", new_date).eq("time", new_time).eq("status", "scheduled").execute()
    if existing.data and len(existing.data) > 0:
        return {"error": "Slot already booked"}
        
    data = supabase.table("appointments").update({
        "date": new_date,
        "time": new_time
    }).eq("id", appointment_id).execute()
    return {"success": True, "data": data.data}

def save_call_summary(user_phone: str, intent: str, summary_text: str, cost: dict):
    if not supabase: return None
    data = supabase.table("call_summaries").insert({
        "user_phone": user_phone,
        "intent": intent,
        "summary_text": summary_text,
        "cost_breakdown": cost
    }).execute()
    return data.data
