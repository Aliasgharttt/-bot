import asyncio
import logging
import os
import json
import requests
from datetime import datetime
from typing import List, Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))
DB_URL = os.getenv("DB_URL", "")
DB_TOKEN = os.getenv("DB_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if DB_URL and DB_URL.startswith("libsql://"):
    DB_URL = DB_URL.replace("libsql://", "https://")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties())
dp = Dispatcher()

def db_query(sql: str, params: List = None):
    try:
        url = f"{DB_URL}"
        headers = {
            "Authorization": f"Bearer {DB_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "statements": [
                {"q": sql, "params": params or []}
            ]
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            first = result[0]
            if "results" in first:
                return first["results"]
        return None
    except:
        return None

def get_all_users() -> List[Dict]:
    try:
        result = db_query("SELECT * FROM users ORDER BY join_date DESC")
        users = []
        if result and "rows" in result:
            for row in result["rows"]:
                users.append({
                    "user_id": row[0],
                    "full_name": row[1] or "بی‌نام",
                    "username": row[2] or "",
                    "join_date": row[3] or ""
                })
        return users
    except:
        return []

async def health_check(request):
    return web.Response(text="OK")

@dp.message()
async def forward_all(message: Message):
    user = message.from_user
    await message.answer(
        "⚠️ **ربات جدید**\n\n"
        "سلام " + user.full_name + " عزیز\n\n"
        "این ربات دیگر پشتیبانی نمی‌شود.\n"
        "برای دریافت خدمات به ربات جدید مراجعه کنید:\n\n"
        "👉 @R61vipbot",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

@dp.message(Command("notify_all"))
async def notify_all(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = get_all_users()
    count = 0
    failed = 0
    
    for u in users:
        try:
            await bot.send_message(
                u["user_id"],
                "⚠️ **اطلاع‌رسانی**\n\n"
                "کاربر گرامی، ربات به آدرس جدید منتقل شده است.\n"
                "برای دریافت خدمات به ربات زیر مراجعه کنید:\n\n"
                "👉 @R61vipbot",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            count += 1
            await asyncio.sleep(0.3)
        except:
            failed += 1
    
    await message.answer(
        f"✅ اطلاع‌رسانی انجام شد.\n\n"
        f"📨 ارسال شده: {count} نفر\n"
        f"❌ ناموفق: {failed} نفر"
    )

async def main():
    if WEBHOOK_URL:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler
        await bot.delete_webhook()
        await bot.set_webhook(WEBHOOK_URL + "/webhook")
        app = web.Application()
        app.router.add_get("/", health_check)
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", PORT).start()
        await asyncio.Event().wait()
    else:
        from threading import Thread
        def run_health():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            app = web.Application()
            app.router.add_get("/", health_check)
            runner = web.AppRunner(app)
            loop.run_until_complete(runner.setup())
            loop.run_until_complete(web.TCPSite(runner, "0.0.0.0", PORT).start())
            loop.run_forever()
        Thread(target=run_health, daemon=True).start()
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
