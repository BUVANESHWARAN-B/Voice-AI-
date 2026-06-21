# MAVI - Agentic HealthCare Voice AI 🏥🤖

MAVI is an intelligent, real-time Voice AI assistant designed to act as a virtual front desk for healthcare clinics. It allows users to talk naturally through their browser, book or manage medical appointments, and receive a rich post-call summary.

## Features
- **Real-Time Voice Interaction**: Speak naturally to the AI over a WebRTC connection with near-zero latency.
- **Visual Avatar Integration**: Uses Simli to render a highly realistic and responsive digital avatar on the frontend.
- **Smart Appointment Booking**: Checks available slots, registers new appointments, and seamlessly saves them to a Supabase PostgreSQL database.
- **Intelligent Summarization**: Automatically generates a robust JSON summary of the conversation and estimated costs after every call using Groq LLMs.

## Technology Stack
- **Frontend**: Next.js (React), TailwindCSS, LiveKit React Components, Simli Avatar API.
- **Backend**: FastAPI (Python), LiveKit Agents Framework, `asyncio`.
- **AI Engine**: 
  - **LLM**: Groq (Llama-3.1-8b)
  - **Speech-to-Text (STT)**: Deepgram
  - **Text-to-Speech (TTS)**: Cartesia
- **Database**: Supabase (PostgreSQL)

## Project Structure
- `/frontend`: The Next.js application containing the UI, Call Summary view, and WebRTC logic.
- `/backend`: The Python server.
  - `agent.py`: The LiveKit worker script that drives the AI personality and Voice loop.
  - `main.py`: The FastAPI server that handles LiveKit token generation and fetching Call Summaries.
  - `tools.py`: Python function calling (tools) allowing the AI to interact with the database.
  - `database.py`: Supabase database logic for appointments and summaries.

## Getting Started

### 1. Environment Variables
Ensure you have the following keys in your environment (e.g. `.env` and `.env.local`):
- `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL`
- `GROQ_API_KEY`
- `DEEPGRAM_API_KEY`, `CARTESIA_API_KEY`, `SIMLI_API_KEY`
- `SUPABASE_URL`, `SUPABASE_KEY`

### 2. Run the Application

You will need to run three separate processes concurrently.

**Terminal 1: Start the Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 2: Start the Backend API**
```bash
cd backend
./start.sh
# (This runs: uvicorn main:app --reload --port 8000)
```

**Terminal 3: Start the LiveKit Agent**
```bash
cd backend
./start_agent.sh
# (This runs: python agent.py dev)
```

### 3. Usage
Once all servers are running, open your browser to `http://localhost:3000`. Click **Start New Call**, allow microphone permissions, and start talking to MAVI!

---
*Note: Ensure your API quotas (especially Cartesia TTS credits) are active, as the AI will disconnect or throw a 402 error if it runs out of speech generation credits.*
