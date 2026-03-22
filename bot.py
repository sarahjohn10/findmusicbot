import os
import time
import asyncio
import logging
import socket
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
import utils
import database

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Ultra-Fast concurrency
download_semaphore = asyncio.Semaphore(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Qo'shiq nomini yoki Artist ismini yozing! 🚀 (Ultra-Turbo mode)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    results = database.get_search(query)
    if not results:
        results = await utils.search_music_async(query, limit=10)
        if results:
            database.save_search(query, results)
        
    if not results:
        await update.message.reply_text("❌ Qidiruvda xatolik yuz berdi yoki qo'shiq topilmadi.")
        return

    text = f"🎵 Qidiruv: {query}\n\n"
    for i, res in enumerate(results[:5]):
        text += f"{i+1}. {res.get('title')} - {res.get('uploader')}\n"
        
    row1 = [InlineKeyboardButton(f"⬇️ {i+1}", callback_data=f"dl_{res.get('id')}") for i, res in enumerate(results[:5])]
    keyboard = [row1]
    
    first = results[0]
    q = query.lower().strip()
    if q in first.get('uploader', '').lower() or q in first.get('channel', '').lower():
        keyboard.append([InlineKeyboardButton("📥 Barchasini yuklash (Turbo)", callback_data=f"bulk_{query}")])
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

active_downloads = set()

async def download_and_send(chat_id, video_id, bot):
    if not video_id or len(str(video_id)) != 11:
        logging.error(f"Invalid Video ID blocked: {video_id}")
        return
    if video_id in active_downloads: return
    
    cached = database.get_file_cache(video_id)
    if cached:
        try:
            await bot.send_audio(chat_id=chat_id, audio=cached['file_id'], caption=f"🎵 {cached['title']}\n👤 {cached['artist']}", read_timeout=120, write_timeout=120)
            return
        except Exception: pass

    async with download_semaphore:
        active_downloads.add(video_id)
        try:
            info = await utils.download_audio_async(f"https://www.youtube.com/watch?v={video_id}")
            with open(info['filepath'], 'rb') as f:
                msg = await bot.send_audio(
                    chat_id=chat_id, audio=f, title=info['title'], performer=info['artist'], 
                    duration=info['duration'], caption=f"🎵 {info['title']}\n👤 {info['artist']}",
                    read_timeout=120, write_timeout=120
                )
                if msg.audio and msg.audio.file_id:
                    database.save_file_id(video_id, msg.audio.file_id, info['title'], info['artist'], info['duration'])
            if os.path.exists(info['filepath']): os.remove(info['filepath'])
        except Exception as e:
            logging.error(f"Download speed/error issue: {e}")
            try: await bot.send_message(chat_id=chat_id, text="❌ Yuklashda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
            except: pass
        finally: active_downloads.discard(video_id)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    
    if query.data.startswith("dl_"):
        asyncio.create_task(download_and_send(query.message.chat_id, query.data.split("_")[1], context.bot))
    if query.data.startswith("bulk_"):
        artist = query.data.split("_", 1)[1]
        results = database.get_search(artist)
        if not results:
            results = await utils.search_music_async(artist, limit=10)
            if results: database.save_search(artist, results)
        if not results:
            try: await query.message.reply_text("❌ Tarmoqda xatolik yuz berdi.")
            except: pass
            return
        try: await query.message.reply_text("📥 Yuklanmoqda... (Turbo mode) 🔥")
        except: pass
        for res in results: asyncio.create_task(download_and_send(query.message.chat_id, res.get('id'), context.bot))
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "Conflict: terminated by other getUpdates request" in str(context.error):
        os._exit(1)
    logging.error(f"Telegram Exception: {context.error}")

# Global App Export for Vercel Webhooks
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_error_handler(error_handler)
app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
app.add_handler(CallbackQueryHandler(button_callback))

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    else:
        for f in os.listdir('downloads'):
            try: os.remove(os.path.join('downloads', f))
            except: pass
    database.init_db()

    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler("bot_log.txt"), logging.StreamHandler()]
    )
    
    print("Turbo Bot Polling is running locally...")
    app.run_polling()

if __name__ == '__main__': main()
