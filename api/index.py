from fastapi import FastAPI, Request
from telegram import Update
import sys
import os

# Parent import support
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import app, database

fastapi_app = FastAPI()

@fastapi_app.on_event("startup")
async def startup():
    database.init_db()
    if not app.bot_data.get('initialized'):
        await app.initialize()
        app.bot_data['initialized'] = True

@fastapi_app.post("/webhook")
async def webhook(request: Request):
    req = await request.json()
    update = Update.de_json(req, app.bot)
    await app.process_update(update)
    return {"status": "ok"}

@fastapi_app.get("/")
def ping():
    return {"message": "Telegram Bot is running on Vercel Serverless!"}
