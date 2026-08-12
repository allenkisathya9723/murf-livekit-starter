import os
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def main():
    # 1. Get the SIP destination from the user
    destination_input = input("Enter the destination SIP URI or username to call (e.g., sip:allenkisathya@sip.linphone.org or allenkisathya): ").strip()
    
    # Normalize destination: SipCallTo requires just the user/number, not a full URI
    destination = destination_input
    if destination.startswith("sip:"):
        destination = destination[4:]
    if "@" in destination:
        destination = destination.split("@")[0]
        
    # 2. Get the SIP Trunk ID (Linphone Trunk created in LiveKit Cloud)
    sip_trunk_id = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
    if not sip_trunk_id:
        print("ERROR: You must add LIVEKIT_SIP_OUTBOUND_TRUNK_ID to your .env.local file!")
        return

    print(f"Connecting to LiveKit to initiate outbound call to {destination}...")

    # 3. Initialize the LiveKit API client
    livekit_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    try:
        # 4. Explicitly create a unique room and dispatch the agent to it
        import random
        import time
        room_name = f"voice_assistant_room_outbound_{int(time.time())}_{random.randint(100, 999)}"
        await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=10,
                max_participants=2,
                agents=[api.RoomAgentDispatch(agent_name="my-agent")]
            )
        )

        # 5. Trigger the outbound SIP call!
        await livekit_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=destination,
                sip_number="allenkisathya",
                room_name=room_name,
                participant_identity="janmitra-outbound-caller",
                participant_name="JanMitra Patient",
            )
        )
        print("✅ Outbound call triggered successfully!")
        print("Keep your 'uv run python src/agent.py dev' running in the other terminal so the agent can join the call.")

    except Exception as e:
        print(f"❌ Failed to make outbound call: {e}")
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
