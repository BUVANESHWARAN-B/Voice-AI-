import os
import asyncio
import logging
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import cartesia, deepgram, openai, silero
# Note: we use livekit.plugins.openai for the LLM interface, but we will configure it for Groq.
# Groq is OpenAI compatible, so we just pass the Groq base URL and API key to the OpenAI plugin.

from tools import VoiceAgentTools

load_dotenv()
logger = logging.getLogger("mykare-voice-agent")

async def entrypoint(ctx: JobContext):
    # Setup Groq LLM (via OpenAI compatibility)
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm_instance = openai.LLM(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key,
        model="llama3-70b-8192" # or llama3-8b-8192 depending on speed/quality tradeoff
    )

    # Initialize tools context
    fnc_ctx = VoiceAgentTools()

    # Create the Voice Assistant
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=llm_instance,
        tts=cartesia.TTS(),
        fnc_ctx=fnc_ctx,
        system_instruction="""You are a front-desk AI voice assistant for Mykare healthcare. 
Your job is to talk to users, understand their intent, book or manage appointments, and maintain a polite and helpful demeanor.
Keep your responses short, natural, and conversational to minimize latency. 
Use the provided tools to identify users, check slots, and book appointments. 
When the user wants to end the conversation, use the end_conversation tool to summarize the interaction and say goodbye.""",
    )

    assistant.start(ctx.room)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    await asyncio.sleep(1)
    await assistant.say("Hello, welcome to Mykare Healthcare. How can I assist you today?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
