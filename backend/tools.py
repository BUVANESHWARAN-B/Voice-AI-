from livekit.agents import llm
import logging
from typing import Annotated

from database import (
    create_appointment,
    get_user_appointments,
    cancel_appointment_db,
    modify_appointment_db,
    save_call_summary,
    get_session_history,
    delete_session
)

logger = logging.getLogger("voice-agent-tools")

class VoiceAgentTools:
    def __init__(self, room=None):
        self.room = room

    async def _send_indicator(self, text: str):
        if self.room and self.room.local_participant:
            import asyncio
            # publish_data expects payload bytes and a topic
            await self.room.local_participant.publish_data(payload=text.encode("utf-8"), topic="tools")

    @llm.function_tool(description="Identify the user by their phone number (e.g. +1234567890). Must be called before booking or retrieving appointments.")
    async def identify_user(self, phone_number: Annotated[str, "The user's phone number"]):
        logger.info(f"identify_user called: {phone_number}")
        await self._send_indicator("Identifying user...")
        # In a real app, we might create the user if they don't exist
        return f"User identified with phone {phone_number}. You may proceed with their request."

    @llm.function_tool(description="Return available appointment slots for a specific date (YYYY-MM-DD).")
    async def fetch_slots(self, date: Annotated[str, "The date to check availability for, in YYYY-MM-DD format"]):
        logger.info(f"fetch_slots called for date: {date}")
        await self._send_indicator("Fetching slots...")
        from database import get_available_slots
        available = get_available_slots(date)
        if not available:
            return f"No available slots for {date}."
        return f"Available slots on {date}: {available}"

    @llm.function_tool(description="Book an appointment for the user. Save in DB and prevent double booking.")
    async def book_appointment(
        self, 
        user_phone: Annotated[str, "The user's phone number"],
        date: Annotated[str, "The date of the appointment (YYYY-MM-DD)"],
        time: Annotated[str, "The time of the appointment (e.g., 10:00 AM)"]
    ):
        logger.info(f"book_appointment called: {user_phone}, {date}, {time}")
        await self._send_indicator("Booking appointment...")
        from database import create_appointment
        result = create_appointment(user_phone, date, time)
        if result and "error" in result:
            await self._send_indicator("Booking failed ❌")
            return f"Failed to book: {result['error']}"
        await self._send_indicator("Booking confirmed ✅")
        return f"Booking confirmed for {date} at {time}."

    @llm.function_tool(description="Show the user's past or upcoming bookings.")
    async def retrieve_appointments(self, user_phone: Annotated[str, "The user's phone number"]):
        logger.info(f"retrieve_appointments called: {user_phone}")
        await self._send_indicator("Retrieving appointments...")
        from database import get_user_appointments
        appointments = get_user_appointments(user_phone)
        if not appointments:
            return "No appointments found."
        return f"User appointments: {appointments}"

    @llm.function_tool(description="Cancel an existing appointment.")
    async def cancel_appointment(self, appointment_id: Annotated[str, "The UUID of the appointment to cancel"]):
        logger.info(f"cancel_appointment called: {appointment_id}")
        await self._send_indicator("Cancelling appointment...")
        from database import cancel_appointment_db
        success = cancel_appointment_db(appointment_id)
        if success:
            await self._send_indicator("Cancelled ✅")
            return "Appointment cancelled successfully."
        return "Failed to cancel appointment. Database not connected or invalid ID."

    @llm.function_tool(description="Modify an existing appointment.")
    def modify_appointment(
        self, 
        appointment_id: Annotated[str, "The UUID of the appointment"],
        new_date: Annotated[str, "The new date (YYYY-MM-DD)"],
        new_time: Annotated[str, "The new time (e.g., 10:00 AM)"]
    ):
        logger.info(f"modify_appointment called: {appointment_id}, {new_date}, {new_time}")
        result = modify_appointment_db(appointment_id, new_date, new_time)
        if result and "error" in result:
            return f"Failed to modify: {result['error']}"
        return f"Appointment modified to {new_date} at {new_time}."

    @llm.function_tool(description="End the conversation and trigger summarization phase.")
    def end_conversation(
        self, 
        user_phone: Annotated[str, "The user's phone number"],
        intent: Annotated[str, "The main intent of the user (e.g., Book Appointment, Cancel)"],
        summary: Annotated[str, "A brief summary of the conversation and preferences"]
    ):
        logger.info(f"end_conversation called: {user_phone}")
        # Normally we would fetch the entire Redis history here and prompt Groq again 
        # for a more thorough summary. Since we are in the LLM tool call itself, 
        # we can accept the summary generated by the agent or do a separate LLM call.
        
        # We will save the summary using the provided text.
        cost = {"llm_tokens": "estimated", "audio_seconds": "estimated"}
        result = save_call_summary(user_phone, intent, summary, cost)
        
        # We could delete the session from Redis here, but we need the room_id.
        # We can handle session cleanup in the agent's disconnect event.
        return "Conversation ended. Summary saved."
