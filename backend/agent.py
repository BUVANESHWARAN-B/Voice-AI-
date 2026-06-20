import os
import asyncio
import logging
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import cartesia, deepgram, openai, simli
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
        model="llama-3.1-8b-instant" # Downgraded to 8b to avoid Groq TPM limits
    )

    # Initialize tools context
    fnc_ctx = VoiceAgentTools(room=ctx.room)

    # Create the Voice Agent
    agent = Agent(
        stt=deepgram.STT(),
        llm=llm_instance,
        tts=cartesia.TTS(),
        tools=llm.find_function_tools(fnc_ctx),
        instructions="""You are a front-desk AI voice assistant for Mykare healthcare. 
Your job is to talk to users, understand their intent, book or manage appointments, and maintain a polite and helpful demeanor.
Keep your responses short, natural, and conversational to minimize latency. 
Use the provided tools to identify users, check slots, and book appointments. 
When the user wants to end the conversation, use the end_conversation tool to summarize the interaction and say goodbye."""
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    # Initialize Simli Avatar
    simli_api_key = os.getenv("SIMLI_API_KEY")
    if simli_api_key:
        simli_config = simli.SimliConfig(
            api_key=simli_api_key,
            face_id="0c2b8b04-5274-41f1-a21c-d5c98322efa9", # Updated face ID
        )
        avatar = simli.avatar.AvatarSession(simli_config=simli_config)
        await avatar.start(agent_session=session, room=ctx.room)

    async def generate_summary_task(chat_ctx):
        try:
            from openai import AsyncOpenAI
            from database import save_call_summary
            messages = [{"role": m.role, "content": m.text} for m in chat_ctx.messages if m.role in ["user", "assistant"]]
            if not messages: return
            
            client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
            prompt = "Summarize the following healthcare appointment booking conversation in 1-2 sentences. Focus on the user intent and final outcome."
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": prompt}] + messages
            )
            summary_text = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            save_call_summary("unknown", "general", summary_text, {"llm_tokens": tokens})
            logger.info("Call summary generated and saved successfully.")
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        logger.info("Room disconnected, launching summary task...")
        asyncio.create_task(generate_summary_task(agent.chat_ctx))

    await asyncio.sleep(1)
    await session.say("Hello, welcome to Mykare Healthcare. How can I assist you today?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
