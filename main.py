import asyncio
import logging
import os
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

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties())
dp = Dispatcher()

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

async def main():
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler
    
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    if WEBHOOK_URL:
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
