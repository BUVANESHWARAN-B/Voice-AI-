# Mykare AI Voice Agent - Execution Master Plan

## Project Overview
[cite_start]Build a real-world, ultra-low latency AI voice agent for a healthcare front desk that can talk, understand, and take actions[cite: 2]. [cite_start]The system must listen to speech [cite: 11][cite_start], understand intent [cite: 11][cite_start], synthesize natural voice [cite: 12][cite_start], display a synced talking avatar [cite: 13][cite_start], book/manage appointments [cite: 14][cite_start], and summarize the conversation[cite: 15].

[cite_start]**Target Latency:** strictly < 3-5 seconds[cite: 29].
[cite_start]**Expected Effort Scope:** 3-6 hours[cite: 5].

---

## 📁 Folder Structure Requirements
Create a root directory containing two separate subfolders:
1. `/frontend` (Next.js)
2. `/backend` (Python/FastAPI)

---

## 🛠️ Installation & Dependencies

### Backend Requirements (`/backend`)
Initialize a Python virtual environment and install the following packages:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install fastapi uvicorn
pip install livekit-server-sdk livekit-agents
pip install deepgram-sdk cartesia groq
pip install supabase redis python-dotenv
Frontend Requirements (/frontend)Initialize a Next.js application and install the required packages:Bashnpx create-next-app@latest .
npm install @livekit/components-react livekit-client
npm install @supabase/supabase-js
npm install lucide-react
🔐 Environment Variables (.env)Backend .env FileCreate a .env file in the /backend directory:Code snippet# LiveKit WebRTC Configuration
LIVEKIT_URL=wss://<your-project>.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# AI Model Providers
DEEPGRAM_API_KEY=your_deepgram_api_key
CARTESIA_API_KEY=your_cartesia_api_key
GROQ_API_KEY=your_groq_api_key

# Databases (State & Persistence)
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
UPSTASH_REDIS_REST_URL=your_upstash_redis_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token

# Avatar WebRTC
SIMLI_API_KEY=your_simli_api_key
Frontend .env.local FileCreate a .env.local file in the /frontend directory:Code snippetNEXT_PUBLIC_LIVEKIT_URL=wss://<your-project>.livekit.cloud
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_SIMLI_API_KEY=your_simli_api_key
NEXT_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
🏗️ Execution PhasesPhase 1: Database & State Schema1. Supabase (Persistent Storage): Create the following SQL tables.users table: phone_number (Primary Key), name, preferences.appointments table: id (UUID), user_phone (Foreign Key), date, time, status.call_summaries table: id (Primary Key), user_phone (Foreign Key), intent, summary_text, timestamp.2. Redis (Active State): Define the key-value structure for active sessions.Key: session:{livekit_room_id}.Value: JSON array of the message history appended in real-time.Phase 2: Backend API & AI Pipeline (/backend)1. API Initialization: Build a FastAPI server with CORS enabled.2. Token Generation: Create a /get-token endpoint that returns a secure LiveKit Access Token.3. LiveKit Agent: Implement a LiveKit WebRTC worker using livekit-agents.4. Orchestration Loop:Ingest user audio via Deepgram STT.  Fetch active conversation history from Redis.Send history + STT text to Groq LLM.Append Groq's response to Redis.Synthesize Groq's text via Cartesia TTS  and stream back to LiveKit.  Phase 3: Tool Calling Logic (Python Backend)Register the following tools with the Groq LLM. The agent must extract Name, Phone number, Date, Time, and Intent.  identify_user: Ask phone number , use as unique ID.  fetch_slots: Return hardcoded available slots.  book_appointment: Save in DB , prevent double booking , clearly confirm date/time.  retrieve_appointments: Show user's past bookings.  cancel_appointment & modify_appointment: Update Supabase records.  end_conversation: Trigger summarization phase.  Phase 4: Frontend UI & Avatar (/frontend)1. UI Elements: Build a clean UI with a "Start Call" interface.
2. WebRTC Connection: Fetch the token from /get-token and connect to <LiveKitRoom>.
3. Avatar Sync: Render the Simli Avatar component. Pass the incoming WebRTC audio track to it so it syncs lips with voice without freezing.
4. Visual Tool Indicators: Listen for custom data events over LiveKit. When a backend tool executes, show it visually on screen (e.g., "Fetching slots...", "Booking confirmed").  Phase 5: Summarization & Cleanup EngineWhen the end_conversation tool is called:Fetch the entire conversation history from Redis.Prompt Groq to generate a final summary containing: Summary of conversation, List of appointments, User preferences, and Timestamp.  Calculate the exact cost per call breakdown  (LLM tokens + Audio seconds) and append it.  Save the final summary to the Supabase call_summaries table.Delete the active session key from Redis.Push the summary object to the frontend to show on UI within 10 seconds.  