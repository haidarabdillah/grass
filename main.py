import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
import os
from dotenv import load_dotenv  # Import modul load_dotenv

# Load environment variables from .env file
load_dotenv()

user_agent = UserAgent()
random_user_agent = user_agent.random
_user_id = os.getenv("USER_ID")  # Mengambil user_id dari environment variables
proxy_connected_file = os.getenv("PROXY_CONNECTED_FILE")

async def save_proxy_to_file(proxy):
    try:
        with open(proxy_connected_file, "r") as file:
            lines = file.readlines()

        seen_proxies = set(line.strip() for line in lines)

        if proxy not in seen_proxies:
            with open(proxy_connected_file, "a") as file:
                file.write(proxy + '\n')
    except Exception as e:
        logger.error(f"Error while saving proxy to file: {e}")

async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                await asyncio.sleep(2)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "3.3.2"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        logger.debug('menyalaa abangku 🔥🔥🔥🔥🔥🔥')
                        logger.debug(socks5_proxy)
                        await websocket.send(json.dumps(pong_response))
                        await save_proxy_to_file(socks5_proxy)
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)

async def main():
    with open('proxylist.txt', 'r') as file:
        socks5_proxy_list = file.read().splitlines()
    
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in socks5_proxy_list]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    #поехали нафик
    asyncio.run(main())
