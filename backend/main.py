import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MAVI - Agentic HealthCare API")

# Setup CORS
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, # Configured via env var to prevent wildcard+credential browser blocks
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.get("/get-token")
def get_token(room_name: str, participant_name: str):
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials missing")

    token = api.AccessToken(
        LIVEKIT_API_KEY, 
        LIVEKIT_API_SECRET
    )
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
    ))

    return {"token": token.to_jwt()}

@app.get("/summary")
async def get_summary():
    import asyncio
    await asyncio.sleep(4) # Give background task time to generate summary
    
    from database import supabase
    if not supabase:
        return {"status": "error", "summary": "Call ended. Database not connected.", "appointments": []}
    
    try:
        # Fetch the latest call summary
        summary_data = supabase.table("call_summaries").select("*").order("created_at", desc=True).limit(1).execute()
        
        if not summary_data.data or len(summary_data.data) == 0:
            return {"status": "completed", "summary_text": "No summary found.", "appointments": []}
            
        latest_summary = summary_data.data[0]
        user_phone = latest_summary.get("user_phone", "unknown")
        
        # Parse the JSON string from summary_text
        import json
        try:
            parsed_summary = json.loads(latest_summary.get("summary_text", "{}"))
        except Exception:
            parsed_summary = {"summary": latest_summary.get("summary_text", "")}
            
        # Fetch the user's appointments (or recent ones)
        if user_phone and user_phone != "unknown":
            appts_data = supabase.table("appointments").select("*").eq("user_phone", user_phone).order("created_at", desc=True).limit(3).execute()
        else:
            appts_data = supabase.table("appointments").select("*").order("created_at", desc=True).limit(3).execute()
            
        appointments = appts_data.data if appts_data.data else []
        
        import datetime
        return {
            "status": "completed",
            "intent": latest_summary.get("intent", parsed_summary.get("intent", "unknown")),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "summary_text": parsed_summary.get("summary", "Call completed."),
            "user": {
                "phone": user_phone,
                "preferences": parsed_summary.get("preferences", "None recorded.")
            },
            "appointments": [
                {
                    "date": appt.get("date", ""),
                    "time": appt.get("time", ""),
                    "status": appt.get("status", "booked")
                } for appt in appointments
            ],
            "cost_breakdown": latest_summary.get("cost_breakdown", {})
        }
    except Exception as e:
        import datetime
        return {
            "status": "error",
            "summary_text": f"Call ended. Error fetching summary: {str(e)}", 
            "appointments": [],
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
