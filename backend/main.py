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
