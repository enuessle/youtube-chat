import threading
import time
import queue
from chat_scraper import YouTube
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio

CHANNEL_ID = "UC_SI1j1d8vJo_rYMV5o_dRg"  # replace with your channel ID

yt = YouTube()
message_queue = queue.Queue()
messages = []  # all messages
stop_thread = False
MAX_MESSAGES = 10  # frontend limit

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def get():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_index = 0
    while True:
        # Send new messages
        if last_index < len(messages):
            for msg in messages[last_index:]:
                await websocket.send_json(msg)
            last_index = len(messages)
        await asyncio.sleep(0.5)

def youtube_loop():
    global stop_thread
    try:
        print("Connecting to YouTube...")
        yt.youtube_connect(CHANNEL_ID)
        print("Connected!")
        while not stop_thread:
            new_msgs = yt.twitch_receive_messages()
            for msg in new_msgs:
                message_queue.put(msg)
                messages.append(msg)
            time.sleep(1)
    except Exception as e:
        print("YouTube loop error:", e)

if __name__ == "__main__":
    thread = threading.Thread(target=youtube_loop, daemon=True)
    thread.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
    stop_thread = True
    thread.join()
