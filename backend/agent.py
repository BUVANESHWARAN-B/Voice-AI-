import os
import asyncio
import logging
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import cartesia, deepgram, openai, simli
from openai import AsyncOpenAI
from database import save_call_summary
# Note: we use livekit.plugins.openai for the LLM interface, but we will configure it for Groq.
# Groq is OpenAI compatible, so we just pass the Groq base URL and API key to the OpenAI plugin.

from tools import VoiceAgentTools

load_dotenv()
logger = logging.getLogger("mykare-voice-agent")

async def entrypoint(ctx: JobContext):
    # Setup Groq LLM (via OpenAI compatibility)
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    llm_instance = openai.LLM(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key,
        model=groq_model # Downgraded to 8b to avoid Groq TPM limits
    )

    # Initialize tools context
    fnc_ctx = VoiceAgentTools(room=ctx.room)

    import datetime
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    current_year = datetime.date.today().year
    
    # Create the Voice Agent
    agent = Agent(
        stt=deepgram.STT(),
        llm=llm_instance,
        tts=cartesia.TTS(),
        tools=llm.find_function_tools(fnc_ctx),
        instructions=f"""You are MAVI, a front-desk AI voice assistant for Agentic HealthCare. 
Your job is to talk to users, understand their intent, book or manage appointments, and maintain a polite and helpful demeanor.
Keep your responses short, natural, and conversational to minimize latency. 
CRITICAL RULES:
0. The current date is {current_date}. If a user specifies a month and day without a year, ALWAYS assume the year is {current_year}.
1. Always explicitly ask the user for their contact number before attempting to book an appointment or identify them.
2. When confirming or repeating a phone number to the user, format it with dashes so you read it digit by digit (e.g., "9-4-4-5-7-8"). Do NOT read numbers as hundreds or thousands.
3. When using tools, format the phone number as a continuous string of digits without spaces or dashes.
4. After successfully booking an appointment, explicitly ask: "Is there anything else I can help you with?".
5. If the user indicates they have no further requests (e.g., "no", "that's it", "nothing else"), you MUST immediately use the end_conversation tool to hang up.
Use the provided tools to identify users, check slots, book appointments, and end the call."""
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    # Initialize Simli Avatar
    simli_api_key = os.getenv("SIMLI_API_KEY")
    if simli_api_key:
        simli_face_id = os.getenv("SIMLI_FACE_ID", "0c2b8b04-5274-41f1-a21c-d5c98322efa9")
        simli_config = simli.SimliConfig(
            api_key=simli_api_key,
            face_id=simli_face_id, # Updated face ID
        )
        avatar = simli.avatar.AvatarSession(simli_config=simli_config)
        await avatar.start(agent_session=session, room=ctx.room)

    async def generate_summary_task(chat_ctx):
        try:
            # Handle newer livekit versions where chat_ctx.messages is a method
            msgs = chat_ctx.messages() if callable(chat_ctx.messages) else chat_ctx.messages
            
            # Message content could be stored in m.content or m.text
            messages = []
            for m in msgs:
                if m.role in ["user", "assistant"]:
                    content = getattr(m, "content", getattr(m, "text", ""))
                    # Sometimes content is a list of ChatContent objects (in newer SDKs)
                    if isinstance(content, list):
                        content = " ".join([getattr(c, "text", str(c)) for c in content if hasattr(c, "text") or isinstance(c, str)])
                    messages.append({"role": m.role, "content": str(content)})
                    
            if not messages: return
            
            client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
            prompt = """Analyze the following healthcare appointment booking conversation and return a JSON object with this exact structure:
{"intent": "book_appointment", "summary": "1-2 sentence summary", "preferences": "any user preferences mentioned"}
Return ONLY valid JSON."""
            groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            
            try:
                response = await client.chat.completions.create(
                    model=groq_model,
                    response_format={"type": "json_object"},
                    messages=[{"role": "system", "content": prompt}] + messages
                )
                
                import json
                llm_content = response.choices[0].message.content
                try:
                    parsed = json.loads(llm_content)
                    intent = parsed.get("intent", "general")
                    summary_text_db = json.dumps(parsed)
                except Exception:
                    intent = "general"
                    summary_text_db = json.dumps({"summary": llm_content})
                    
                tokens = response.usage.total_tokens if response.usage else 0
                estimated_cost = f"${(tokens / 1000) * 0.0001:.4f}"
            except Exception as api_err:
                logger.error(f"Groq API error during summary: {api_err}")
                import json
                intent = "general"
                summary_text_db = json.dumps({
                    "summary": "Conversation ended. (Summary generation skipped due to Groq API Rate Limit)",
                    "intent": "general"
                })
                tokens = 0
                estimated_cost = "$0.00"

            user_phone = getattr(fnc_ctx, 'user_phone', None) or "unknown"
            save_call_summary(user_phone, intent, summary_text_db, {"llm_tokens": tokens, "estimated_cost": estimated_cost})
            logger.info("Call summary generated and saved successfully.")
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")

    fnc_ctx.generate_summary_task = generate_summary_task
    fnc_ctx.chat_ctx = agent.chat_ctx

    @ctx.room.on("disconnected")
    def on_disconnected(*args, **kwargs):
        logger.info("Room disconnected, launching summary task in background thread...")
        
        # Copy chat context safely before the task shuts down
        msgs = agent.chat_ctx.messages() if callable(agent.chat_ctx.messages) else agent.chat_ctx.messages
        messages = []
        for m in msgs:
            if m.role in ["user", "assistant"]:
                content = getattr(m, "content", getattr(m, "text", ""))
                if isinstance(content, list):
                    content = " ".join([getattr(c, "text", str(c)) for c in content if hasattr(c, "text") or isinstance(c, str)])
                messages.append({"role": m.role, "content": str(content)})
        
        user_phone = getattr(fnc_ctx, 'user_phone', None) or "unknown"
        
        import threading
        def _run_summary():
            import asyncio
            async def _async_summary():
                if not messages: return
                client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
                prompt = """Analyze the following healthcare appointment booking conversation and return a JSON object with this exact structure:
{"intent": "book_appointment", "summary": "1-2 sentence summary", "preferences": "any user preferences mentioned"}
Return ONLY valid JSON."""
                groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
                try:
                    response = await client.chat.completions.create(
                        model=groq_model, response_format={"type": "json_object"},
                        messages=[{"role": "system", "content": prompt}] + messages
                    )
                    import json
                    llm_content = response.choices[0].message.content
                    try:
                        parsed = json.loads(llm_content)
                        intent = parsed.get("intent", "general")
                        summary_text_db = json.dumps(parsed)
                    except Exception:
                        intent = "general"
                        summary_text_db = json.dumps({"summary": llm_content})
                    tokens = response.usage.total_tokens if response.usage else 0
                    estimated_cost = f"${(tokens / 1000) * 0.0001:.4f}"
                except Exception as api_err:
                    logger.error(f"Groq API error during summary: {api_err}")
                    import json
                    intent = "general"
                    summary_text_db = json.dumps({"summary": "Conversation ended. (Summary generation skipped due to Groq API Rate Limit)", "intent": "general"})
                    tokens = 0
                    estimated_cost = "$0.00"

                save_call_summary(user_phone, intent, summary_text_db, {"llm_tokens": tokens, "estimated_cost": estimated_cost})
                logger.info("Call summary generated and saved successfully via thread.")
                
            try:
                asyncio.run(_async_summary())
            except Exception as e:
                logger.error(f"Threaded summary failed: {e}")
            
        t = threading.Thread(target=_run_summary)
        t.start()

    # Wait for the user to join the room before greeting
    user_joined = False
    wait_time = 0
    while not user_joined and wait_time < 30:
        for p in ctx.room.remote_participants.values():
            if "user" in p.identity:
                user_joined = True
                break
        if not user_joined:
            await asyncio.sleep(0.5)
            wait_time += 0.5
            
    if not user_joined:
        logger.warning("No user joined within 30 seconds. Exiting agent gracefully.")
        return

    # Give WebRTC an extra 3 seconds for Simli avatar to fully establish video track stream
    await asyncio.sleep(3)
    await session.say("Hello I am  MAVI. Welcome to Mykare HealthCare. How can I assist you today?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        num_idle_processes=1,       # Only pre-warm 1 process on a single-CPU machine
        load_threshold=0.8,         # Give more headroom before marking "at capacity"
    ))
