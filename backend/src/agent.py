import asyncio
import json
import logging
import os

import httpx
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    tokenize,
)
from livekit.plugins import (
    deepgram,
    murf,
    openai,
    silero,
)
from openai import AsyncClient as OpenAIAsyncClient

from database import delete_user, get_user, init_db, save_user, save_escalation, get_escalations

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Shared background tasks set to prevent Python GC from dropping async tasks
_background_tasks: set[asyncio.Task] = set()

# Shared HTTP client to avoid connection leaks across sessions
_http_client = httpx.AsyncClient(verify=False)


SYSTEM_PROMPT = """
You are JanMitra, an AI healthcare voice assistant for the VoiceForBharat Challenge under Health Access.
Purpose: Help users with general healthcare info, vaccinations, health camps, and human escalation. You are NOT a doctor and NEVER diagnose or prescribe.

IMPORTANT CONVERSATION RULES:
1. ALWAYS answer the user's CURRENT question directly. Keep responses concise (1-2 short sentences, under 30 words).
2. MODE A (Normal Browser/Inbound): Answer questions directly. NEVER repeat introductions ("Namaste, this is JanMitra..."), outbound disclaimers ("I am calling to remind you..."), or opt-out notices ("say stop to end call").
3. MODE B (Outbound Phone Call): Speak the WHO/WHY/OPT-OUT greeting automatically on the first turn only.
4. MULTILINGUAL & SCRIPT: Mirror the user's language. Write Hindi strictly in Devanagari script (देवनागरी लिपि, e.g., "नमस्ते, मैं जनमित्र हूँ।"). Never use Romanized Hindi.
5. PERSISTENT MEMORY: Use `lookup_caller` at session start. Ask explicit consent before using `save_caller_info`. Call `forget_caller` if requested.
6. DAY 7 PERMISSION GATE & ESCALATION:
   - If user asks for a diagnosis or reports red-flag symptoms (severe chest pain, difficulty breathing, etc.):
     a) State your limitation / emergency advice.
     b) Ask for explicit permission: "I can send a short request to a human health-support representative. Would you like me to send that request?"
     c) DO NOT call `create_escalation` on turn 1. STOP AND WAIT.
   - If user answers YES: Call `create_escalation(user_consented=True)`. MANDATORY: In your immediate spoken response, state the exact Reference ID (e.g. "Done. Your request has been created. Your reference ID is [Reference ID].").
   - If user answers NO: Do NOT call `create_escalation`.
7. HEALTH CAMP SCHEDULE: When user asks about health camps, call `get_health_camp_schedule`. Answer directly for the requested city without listing all camps.
"""


class Assistant(Agent):
    def __init__(self, user_id: str, ctx: JobContext) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.user_id = user_id
        self.ctx = ctx

    @function_tool
    async def opt_out_and_end_call(self, context: RunContext, execute: bool = True) -> str:
        """Call this tool ONLY on outbound calls when the user explicitly asks to stop receiving phone calls (e.g. 'stop', 'stop calling me').
        DO NOT call this tool when the user reports medical symptoms or asks medical questions.
        """
        if "outbound" not in self.ctx.room.name:
            return "Understood. I will not send any unwanted call notifications."

        import asyncio
        from livekit import api
        logger.info("Opt-out tool invoked on outbound call! Scheduling room deletion to terminate SIP call on Linphone mobile...")
        
        async def _delayed_disconnect():
            await asyncio.sleep(1.5)
            try:
                lk_api = api.LiveKitAPI(
                    url=os.getenv("LIVEKIT_URL"),
                    api_key=os.getenv("LIVEKIT_API_KEY"),
                    api_secret=os.getenv("LIVEKIT_API_SECRET"),
                )
                await lk_api.room.delete_room(api.DeleteRoomRequest(room=self.ctx.room.name))
                await lk_api.aclose()
                logger.info(f"Room {self.ctx.room.name} deleted via API. Linphone mobile call terminated.")
            except Exception as e:
                logger.error(f"Error deleting room via API: {e}")
                try:
                    await self.ctx.room.disconnect()
                except Exception:
                    pass

        task = asyncio.create_task(_delayed_disconnect())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return "Understood. I will remove you from our calling list and end this call. Goodbye!"

    @function_tool
    async def lookup_caller(self, context: RunContext, execute: bool = True) -> str:
        """Look up caller memory for the current user ID using persistent database. Call this at the start of the call."""
        user = get_user(self.user_id)
        if not user or not user.get("name"):
            return json.dumps(
                {
                    "status": "not_found",
                    "message": "New caller, no memory recorded yet.",
                }
            )
        return json.dumps(
            {
                "status": "found",
                "name": user.get("name"),
                "language_preference": user.get("language_preference"),
                "facts": user.get("facts", {}),
                "last_interaction": user.get("last_interaction"),
            }
        )

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: str,
        user_consented: bool = False,
    ) -> str:
        """Save caller information to persistent memory. MUST ONLY be called if user_consented is True."""
        if not user_consented:
            return "ERROR: Cannot save caller information without explicit user consent."

        saved = save_user(
            user_id=self.user_id,
            name=name,
            language_preference=language_preference,
            facts=facts,
        )
        if saved:
            return f"Successfully saved caller information for {name}."
        return "Failed to save caller information due to a database error."

    @function_tool
    async def forget_caller(self, context: RunContext, execute: bool = True) -> str:
        """Delete all stored memory for the current caller when they ask to be forgotten."""
        deleted = delete_user(self.user_id)
        if deleted:
            return "Successfully deleted caller memory. User is now forgotten."
        return "No stored memory was found to delete."

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        reason: str,
        summary: str,
        what_checked: str,
        user_consented: bool = False,
        urgency: str = "Medium",
        language: str = "English",
        preferred_follow_up: str = "Phone",
        execute: bool = True,
    ) -> str:
        """Create a human help/escalation request. MUST ONLY be called AFTER user explicitly answered YES to permission prompt."""
        if not user_consented:
            return "ERROR: Cannot create human help request without explicit user consent."

        escalation = save_escalation(
            reason=reason,
            summary=summary,
            what_checked=what_checked,
            urgency=urgency,
            language=language,
            preferred_follow_up=preferred_follow_up,
            caller_id=self.user_id,
        )

        if escalation:
            ref_id = escalation["reference_id"]
            return f"Successfully created human escalation request. The unique Reference ID is {ref_id}. YOU MUST IMMEDIATELY SPEAK THIS EXACT REFERENCE ID TO THE USER in your response (e.g., 'Done. Your request has been created. Your reference ID is {ref_id}.')."
        return "Failed to create human escalation request due to a database error."

    @function_tool
    async def get_health_camp_schedule(
        self, context: RunContext, location: str, execute: bool = True
    ) -> str:
        """Get the upcoming free health camp dates for a given location or village."""
        location = location.lower().strip()
        if location == "hyderabad":
            return "There is a free general health camp in Kukatpally, Hyderabad on 12 August 2026."
        elif location in ["vizag", "vijayawada"]:
            return f"There is a free general health camp in {location.title()} on the 15th of this month from 9 AM to 2 PM at the main Panchayat office."
        else:
            return f"We do not have a scheduled camp for {location.title()} this week, but they can visit the nearest Primary Health Center (PHC)."


server = AgentServer()


def prewarm(proc: JobProcess):
    init_db()
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    await ctx.connect()
    try:
        participant = await ctx.wait_for_participant()
        user_id = participant.identity if participant else "default_user"
    except Exception as e:
        import logging
        logging.getLogger("agent").warning(f"Participant never joined or disconnected: {e}")
        return

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),
        llm=openai.LLM(
            model="llama-3.1-8b-instant",
            client=OpenAIAsyncClient(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY"),
                http_client=_http_client,
            ),
        ),
        tts=murf.TTS(
            voice="Pooja",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=False,
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        aec_warmup_duration=0.0,
    )

    await session.start(
        agent=Assistant(user_id=user_id, ctx=ctx),
        room=ctx.room,
    )

    logger.info(f"Participant connected to room {ctx.room.name}: {participant.identity}")

    if "outbound" in ctx.room.name:
        logger.info("Outbound call detected. Triggering immediate TTS greeting via session.say()...")
        session.say(
            "Namaste, this is JanMitra, your health access assistant. I am calling to inform you that there is a free health camp in Kukatpally, Hyderabad on the 12th of August 2026. If you don't want these calls, you can simply say stop to end the call."
        )
    else:
        logger.info("Inbound call detected. Triggering initial memory lookup...")
        session.generate_reply(
            instructions="The call has just started. Immediately call `lookup_caller` tool to check if memory exists for this caller. If memory exists, greet them warmly by name in their preferred language and reference their prior context. If no memory exists, greet them as a new caller using the standard JanMitra first greeting."
        )


if __name__ == "__main__":
    cli.run_app(server)
