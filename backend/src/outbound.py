import os
import asyncio
from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=".env.local")

async def main():
    # 1. Get the phone number from the user
    phone_number = input("Enter the phone number to call (e.g., +919866168396): ").strip()
    
    # 2. Get the SIP Trunk ID (You must create a SIP Trunk in LiveKit Cloud dashboard)
    # SIP Trunks let LiveKit talk to the normal telephone network (via Twilio/Telnyx)
    sip_trunk_id = os.getenv("SIP_TRUNK_ID")
    if not sip_trunk_id:
        print("ERROR: You must add SIP_TRUNK_ID to your .env.local file!")
        print("To get one, go to LiveKit Cloud Dashboard -> SIP -> Create SIP Trunk.")
        return

    print(f"Connecting to LiveKit to initiate outbound call to {phone_number}...")

    # 3. Initialize the LiveKit API client
    livekit_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    try:
        # 4. Trigger the outbound SIP call!
        # This tells LiveKit to dial the phone number and place them into the room.
        # Your background worker (agent.py) will automatically join this room and start talking!
        await livekit_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                room_name="outbound-health-check-room",
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
