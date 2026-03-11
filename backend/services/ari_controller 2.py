
import asyncio
import aiohttp
import logging
import json
import os
import sys

# Configure Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ari_controller")

# Config
ASTERISK_HOST = os.getenv("ASTERISK_HOST", "localhost")
ASTERISK_PORT = os.getenv("ASTERISK_PORT", 8088)
ARI_USER = os.getenv("ARI_USER", "jane_user")
ARI_PASS = os.getenv("ARI_PASS", "supaagent_secret")
APP_NAME = "JaneApp_Bridge"
LIVEKIT_SIP_DOMAIN = os.getenv("LIVEKIT_SIP_DOMAIN", "c54dhff28i8.sip.livekit.cloud")

BASE_URL = f"http://{ASTERISK_HOST}:{ASTERISK_PORT}/ari"
# Clean WS URL (Auth handled via Headers)
WS_URL = f"ws://{ASTERISK_HOST}:{ASTERISK_PORT}/ari/events?app={APP_NAME}"

async def answer_channel(session, channel_id):
    url = f"{BASE_URL}/channels/{channel_id}/answer"
    async with session.post(url) as resp:
        if resp.status != 204:
            logger.error(f"Failed to answer channel {channel_id}: {resp.status}")
            return False
        logger.info(f"Answered channel {channel_id}")
        return True

async def create_bridge(session):
    url = f"{BASE_URL}/bridges?type=mixing"
    async with session.post(url) as resp:
        if resp.status != 200:
            logger.error(f"Failed to create bridge: {resp.status}")
            return None
        data = await resp.json()
        bridge_id = data['id']
        logger.info(f"Created bridge {bridge_id}")
        return bridge_id

async def add_channel_to_bridge(session, bridge_id, channel_id):
    url = f"{BASE_URL}/bridges/{bridge_id}/addChannel?channel={channel_id}"
    async with session.post(url) as resp:
        if resp.status != 204:
            logger.error(f"Failed to add channel {channel_id} to bridge {bridge_id}: {resp.status}")
            return False
        logger.info(f"Added channel {channel_id} to bridge {bridge_id}")
        return True

async def originate_call(session, caller_number):
    # LiveKit outbound trunk is configured to accept calls to +16478006854
    # Use PJSIP dial format: PJSIP/destination@endpoint
    livekit_destination = "+16478006854"  # This matches the LiveKit outbound trunk number
    livekit_endpoint = f"PJSIP/{livekit_destination}@livekit"
    url = f"{BASE_URL}/channels"
    params = {
        'endpoint': livekit_endpoint,
        'app': APP_NAME,
        'appArgs': 'dialed',
        'callerId': caller_number
    }
    
    logger.info(f"Dialing LiveKit: {livekit_endpoint}")
    async with session.post(url, json=params) as resp:
        if resp.status != 200:
            text = await resp.text()
            logger.error(f"Failed to originate call: {resp.status} - {text}")
            return None
        data = await resp.json()
        channel_id = data['id']
        logger.info(f"Originated outbound channel {channel_id}")
        return channel_id

async def handle_stasis_start(session, event):
    channel = event.get('channel')
    args = event.get('args', [])
    channel_id = channel['id']
    
    # Check if this is the outbound leg we created
    if 'dialed' in args:
        logger.info(f"Ignoring outbound channel {channel_id} (already handled)")
        return

    caller_number = channel.get('caller', {}).get('number', 'unknown')
    logger.info(f"Incoming call detected! Channel: {channel_id}, Caller: {caller_number}")

    # 1. Answer
    if not await answer_channel(session, channel_id):
        return

    # 2. Create Bridge
    bridge_id = await create_bridge(session)
    if not bridge_id:
        return

    # 3. Add Incoming to Bridge
    await add_channel_to_bridge(session, bridge_id, channel_id)

    # 4. Dial LiveKit
    outbound_id = await originate_call(session, caller_number)
    if outbound_id:
        # 5. Add Outbound to Bridge
        await add_channel_to_bridge(session, bridge_id, outbound_id)

async def listen_events():
    auth = aiohttp.BasicAuth(ARI_USER, ARI_PASS)
    async with aiohttp.ClientSession(auth=auth) as session:
        logger.info(f"Connecting to WebSocket: {WS_URL}")
        try:
            async with session.ws_connect(WS_URL) as ws:
                logger.info("WebSocket Connected! Waiting for events...")
                
                # Connectivity Check: List channels via REST to prove we can talk
                try:
                    async with session.get(f"{BASE_URL}/channels") as resp:
                        if resp.status == 200:
                            chans = await resp.json()
                            logger.info(f"Connected OK. Current Active Channels: {len(chans)}")
                        else:
                            logger.error(f"REST Check Failed: {resp.status}")
                except Exception as e:
                    logger.error(f"REST Check Error: {e}")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            event = json.loads(msg.data)
                            event_type = event.get('type')
                            
                            # Log heartbeats less frequently if needed, but for now log everything relevant
                            if event_type == 'StasisStart':
                                logger.info(f"🔥 EVENT RECEIVED: {event_type}")
                                asyncio.create_task(handle_stasis_start(session, event))
                            elif event_type == 'StasisEnd':
                                logger.info(f"Call Ended: {event.get('channel', {}).get('id')}")
                            elif event_type not in ['ChannelVarset', 'ChannelStateChange', 'PlaybackStarted', 'PlaybackFinished']:
                                logger.debug(f"Event: {event_type}")
                                
                        except Exception as e:
                            logger.error(f"Error parsing event: {e}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket connection closed with exception {ws.exception()}")
                        break
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            # Simple retry logic could go here
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(listen_events())
    except KeyboardInterrupt:
        logger.info("Stopping...")
