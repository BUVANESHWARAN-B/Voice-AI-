import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Mykare Voice AI Agent API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Next.js frontend origin (e.g. "http://localhost:3000")
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
        return {"summary_text": "Call ended. Database not connected.", "appointments": []}
    
    try:
        # Fetch the most recent 3 appointments
        data = supabase.table("appointments").select("*").order("created_at", desc=True).limit(3).execute()
        appointments = data.data if data.data else []
        
        # Fetch the latest call summary
        summary_data = supabase.table("call_summaries").select("*").order("created_at", desc=True).limit(1).execute()
        if summary_data.data:
            summary_text = summary_data.data[0]["summary_text"]
        elif appointments:
            summary_text = "The user successfully booked the following appointments during the call."
        else:
            summary_text = "The call ended without any new appointments booked."
            
        import datetime
        return {
            "summary_text": summary_text,
            "appointments": appointments,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        import datetime
        return {
            "summary_text": f"Call ended. Error fetching summary: {str(e)}", 
            "appointments": [],
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
