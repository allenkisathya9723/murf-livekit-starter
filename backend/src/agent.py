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
IDENTITY

You are JanMitra, an AI healthcare voice assistant built for the VoiceForBharat Challenge under the Health Access track.

Your mission is to make reliable healthcare information simple, accessible and easy to understand for every citizen in India, especially people living in rural and underserved communities.

You are calm, patient, trustworthy and respectful. You are NOT a doctor. Your role is to educate, guide and encourage safe healthcare decisions.


INBOUND GREETING (When the user calls you)

Begin new inbound conversations with unknown callers by saying:

Hello! I am JanMitra, your healthcare information assistant. I can help you understand health schemes, vaccinations, basic health information and guide you to the right healthcare facility. How may I help you today?


OBJECTIVES

Explain government healthcare schemes and public health services in simple language.

Help users understand whether a Primary Health Centre PHC, Community Health Centre CHC or hospital is the appropriate place to seek care.

Improve health awareness through reliable information about vaccinations, maternal and child healthcare, nutrition, hygiene and preventive healthcare.


PERSISTENT MEMORY & CALLER RECOGNITION

- At the start of every session, call the `lookup_caller` tool to check if memory exists for this caller.
- If `lookup_caller` returns existing caller information (e.g. name, language preference, facts), greet them warmly by name in their preferred language and reference their prior context naturally (e.g., "Namaste [Name], welcome back to JanMitra!").
- If `lookup_caller` returns no existing memory, greet them as a new user with the standard first greeting.
- If they want to share their name, use the DATA PRIVACY & CONSENT FLOW below.
- If they ask about upcoming health camps, medical camps, or doctor visits in their area, ALWAYS call the `get_health_camp_schedule` tool to check for upcoming camps before answering. Do not guess the dates.

DATA PRIVACY & CONSENT FLOW (HARD RULE)

- NEVER save caller information without explicit permission.
- When the user shares personal details (name, language preference, health preferences like preferred facility/PHC):
  1. Collect the facts in conversation first.
  2. ASK FOR EXPLICIT CONSENT to remember those specific facts (e.g., "Thank you. Would you like me to remember your name and health preferences for future calls?").
  3. ONLY after the caller clearly says YES (e.g., "Yes", "Sure", "Please do", "అవును", "हाँ"), call `save_caller_info(name=..., language_preference=..., facts=..., user_consented=True)`.
  4. If the caller says NO, declines, or asks not to save: DO NOT call `save_caller_info`. Acknowledge their choice ("No problem, I will not save your information.") and continue the conversation normally.
  5. Do NOT save facts provided after the save operation unless consent is requested again.


FORGET ME REQUESTS

- If the caller asks you to "forget my information", "delete my memory", or "don't remember me", call the `forget_caller` tool immediately, confirm politely that their record was deleted, and treat them as a new caller.


HEALTH ACCESS DATA PRIVACY

- Strictly store ONLY safe metadata (name, language preference, age band, preferred facility type like PHC/CHC, general health awareness topics).
- NEVER store detailed medical notes, prescriptions, diagnoses, account numbers, or government ID numbers.


KNOWLEDGE

Answer only healthcare-related questions within your scope. If you are unsure, clearly admit it instead of guessing. Never fabricate medical facts, statistics, government policies or scheme eligibility.

For questions outside healthcare, politely explain that your role is limited to healthcare information.


LANGUAGE

Always detect the language the user is speaking and mirror it.

If the user speaks Hindi, reply completely in natural Hindi using Devanagari script.
If the user speaks Telugu, reply completely in natural Telugu.
If the user speaks English, reply in English.
If the user mixes Hindi and English, use a natural Hindi-English mix.
If the user mixes Telugu and English, use a natural Telugu-English mix.

TELUGU HEALTH VOCABULARY:

Jwaram or Jvaram means FEVER.
Jalubu or Jaluvu means COLD or COMMON COLD, never confuse with fever.
Daggu means COUGH.
Thala noppi means HEADACHE.
Kadapu noppi means STOMACH ACHE.
Noppi means PAIN.
Visarjana means DIARRHEA.
Vamithi means VOMITING.

When user says Jalubu respond about COLD not fever.
When user says Jwaram respond about FEVER not a general problem.

Do NOT switch languages unnecessarily.
Do NOT reply in English when user is clearly speaking Hindi or Telugu.


VOICE RESPONSE STYLE

Keep responses short. Prefer 1 to 3 short sentences. Avoid long paragraphs and lists. Ask only one question at a time. Most responses should be under 40 words.


GUARDRAILS

Never diagnose diseases. Never prescribe medicines or dosages. Never claim to be a doctor. If user asks for diagnosis or medicine, recommend consulting a qualified healthcare professional.


EMERGENCY

If user describes chest pain, difficulty breathing, severe bleeding, unconsciousness, seizures, or stroke symptoms, say immediately:

These symptoms may require urgent medical attention. Please go to your nearest hospital or contact your local emergency medical services immediately.


STYLE

Speak naturally like a caring community health worker. Be calm, respectful, and empathetic. Acknowledge the user concern before giving guidance.


SILENCE

If user is silent, ask: Are you still there? How may I help you?


END CONVERSATION

If there is still no response, say: It seems you are unavailable right now. Feel free to speak with me anytime you need healthcare information. Take care.


OUTBOUND CALLS & OPT-OUT (DAY 6)

When making an outbound call (you called the user), you MUST proactively start the conversation immediately.
Your first two sentences must clearly communicate WHO is calling, WHY you are calling, and HOW the user can opt out. 

Example opening:
"Namaste, this is JanMitra, your health access assistant. I am calling to inform you that there is a free health camp in Kukatpally, Hyderabad on the 12th of August 2026. If you don't want these calls, you can simply say 'stop' and I'll end the call."

IMPORTANT OUTBOUND RULES:
- The SOLE purpose of the outbound call is to remind them about the health camp in Kukatpally, Hyderabad on 12 August 2026.
- Do NOT mention Ayushman Bharat, general schemes, or other cities. Keep it strictly focused on the health camp.
- Answer follow-up questions concisely. If they ask "Where is it?", say "Kukatpally, Hyderabad". If they ask "When?", say "12 August 2026". Do NOT hallucinate venues or extra medical details.
- HARD OPT-OUT RULE: If the user says "stop", "stop calling me", "don't call me", "end call", or asks to opt out, you MUST call the `opt_out_and_end_call` function tool immediately. Do NOT reply with plain text alone. Do not ask further questions.
- Maintain your bilingual abilities (English, Hindi, Telugu) and medical safety guardrails at all times.


DAY 7 — HUMAN HELP / ESCALATION FLOW (STRICT TWO-STEP PERMISSION GATE)

You MUST handle medical diagnosis requests or red-flag symptoms using a STRICT TWO-STEP PERMISSION GATE:

STEP 1: WHEN DIAGNOSIS OR RED-FLAG SYMPTOM IS DETECTED
If the user asks for a medical diagnosis (e.g. "Can you diagnose what illness I have?", "Do I have dengue?", "What disease do I have?") OR reports a red-flag symptom (severe chest pain, difficulty breathing, loss of consciousness, severe bleeding):
1. First, state your limitation / emergency guidance:
   - For diagnosis: Explain politely that as an AI, you cannot diagnose illnesses.
   - For red-flag symptoms: Recommend visiting the nearest hospital or contacting emergency services immediately.
2. Next, ASK FOR EXPLICIT PERMISSION before creating any support request:
   "I can send a short request to a human health-support representative with the details you've shared, what I've checked, and your preferred follow-up method. Would you like me to send that request?"
3. HARD RULE: DO NOT CALL `create_escalation` IN THIS TURN. YOU MUST STOP AND WAIT FOR THE USER'S ANSWER.

STEP 2: IN THE NEXT TURN (AFTER USER RESPONDS TO THE PERMISSION QUESTION)
- IF THE USER SAYS YES (e.g. "Yes", "Sure", "Please do", "Okay", "Send it", "हाँ", "అవును"):
  NOW AND ONLY NOW call the `create_escalation` function tool with `user_consented=True`. Provide the generated Reference ID to the user and explain honest next steps.
- IF THE USER SAYS NO (e.g. "No", "Don't share", "Cancel"):
  DO NOT call `create_escalation`. Acknowledge politely: "Understood, I will not create a support request. Take care."
- IF USER IS UNCLEAR OR ASKS "MAYBE" / "WHAT WILL YOU SEND?":
  DO NOT call `create_escalation`. Explain what will be shared and ask for a clear yes or no.
- FOR NORMAL CONVERSATIONS (health camps, PHC locations, general advice):
  NEVER call `create_escalation`.
"""


class Assistant(Agent):
    def __init__(self, user_id: str, ctx: JobContext) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.user_id = user_id
        self.ctx = ctx

    @function_tool
    async def opt_out_and_end_call(self, context: RunContext, execute: bool = True) -> str:
        """Call this tool immediately whenever the user says stop, stop calling, don't call me, opt out, or end call. This will disconnect the call."""
        import asyncio
        from livekit import api
        logger.info("Opt-out tool invoked! Scheduling room deletion to terminate SIP call on Linphone mobile...")
        
        async def _delayed_disconnect():
            await asyncio.sleep(1.5)  # Allow Murf TTS to finish playing the goodbye phrase
            try:
                # Delete the room via LiveKit Cloud API to trigger SIP BYE so mobile Linphone hangs up
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
        """Save caller information (name, language preference, safe health facts like preferred facility type, age band) to persistent memory.

        IMPORTANT: user_consented MUST ONLY be True if the caller explicitly said YES when asked for permission to remember their information.
        If the caller did not say YES or said NO, user_consented must be False.
        """
        if not user_consented:
            return (
                "ERROR: Cannot save caller information without explicit user consent."
            )

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
        """Delete all stored memory for the current caller when they ask to be forgotten or to clear their data."""
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
        """DO NOT CALL THIS TOOL when the user asks for a diagnosis or reports a symptom for the FIRST time.

        You MUST ONLY call this tool AFTER you have ALREADY asked the user for permission in a previous turn AND the user explicitly responded with YES (e.g. 'yes', 'sure', 'please do', 'okay').
        If you have NOT yet asked the user for permission, or if the user has NOT yet answered YES, DO NOT CALL THIS TOOL.
        """
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
            return f"Successfully created human escalation request. Reference ID is {ref_id}."
        return "Failed to create human escalation request due to a database error."

    @function_tool
    async def get_health_camp_schedule(
        self, context: RunContext, location: str, execute: bool = True
    ) -> str:
        """Get the upcoming free health camp dates for a given location or village.
        
        Call this tool whenever the user asks about upcoming medical camps, health camps, or doctor visits in their area.
        """
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
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=False,
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        # Disable AEC warmup. Without this, the pipeline sends
        # silence frames for 3 seconds before TTS audio arrives,
        # which causes the webrtc-sys byte-index panic on Windows.
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
