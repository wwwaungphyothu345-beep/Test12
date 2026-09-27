import os
import logging
import warnings
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from google import genai
import database

# Render Port Detection အတွက် Dummy Web Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Web Server ကို Thread သီးသန့်ဖြင့် Background တွင် Run ခိုင်းခြင်း
threading.Thread(target=run_web_server, daemon=True).start()

# Warnings များ ပိတ်ထားခြင်း
warnings.filterwarnings("ignore")

load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

BAD_WORDS = ["badword1", "badword2", "ဆဲစာ1", "ဆဲစာ2"]

def is_bad_word(text: str) -> bool:
    if not text:
        return False
    return any(word in text.lower() for word in BAD_WORDS)

database.init_db()

# Synchronous Gemini Call Function
def call_gemini(prompt: str) -> str:
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text.strip() if response.text else ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not message.text or not user:
        return

    chat_id = chat.id
    user_id = user.id
    user_name = user.first_name or "Member"
    text = message.text

    # Bad Word Check
    if is_bad_word(text):
        warn_count = database.add_warn(chat_id, user_id)

        if warn_count == 1:
            await message.reply_text(f"⚠️ မင်္ဂလာပါ {user_name}၊ ကျေးဇူးပြုပြီး ယဉ်ကျေးသော စကားလုံးများကိုသာ သုံးပေးပါ။ (သတိပေးချက် ၁/၃)")
        elif warn_count == 2:
            await message.reply_text(f"⚠️ သတိပေးချက် (၂/၃) {user_name}၊ နောက်တစ်ကြိမ် မကောင်းသော စကားလုံး သုံးပါက Group မှ Ban ခံရပါမည်။")
        elif warn_count >= 3:
            try:
                await context.bot.ban_chat_member(chat_id, user_id)
                await message.reply_text(f"⛔ {user_name} သည် သတိပေးချက် (၃) ကြိမ်ပြည့်သွားပါသဖြင့် Group မှ Ban လိုက်ပါပြီ။")
                database.reset_warns(chat_id, user_id)
            except Exception as e:
                await message.reply_text(f"❌ Ban ရန် Bot တွင် Admin Permission မရှိပါ။")
        return

    # Gemini AI Fast Response Engine
    system_instruction = (
        "မင်းက Telegram Group ထဲက ဖော်ရွေပြီး ချစ်စရာကောင်းတဲ့ မိန်းကလေး သူငယ်ချင်းတစ်ယောက်ပါ။ "
        "စကားပြောရင် မိန်းကလေးတစ်ယောက်လို ပေါ့ပေါ့ပါးပါး သူငယ်ချင်းလို မြန်မာလို စာပြန်ပါ။ "
        "စာအရှည်ကြီး မရေးဘဲ ၁ ကြောင်း သို့မဟုတ် ၂ ကြောင်းတိုတိုနဲ့ လိုရင်းပဲ ချက်ချင်း စာပြန်ပေးပါ။"
    )

    full_prompt = f"{system_instruction}\n\n{user_name}: {text}"

    try:
        # Async-safe thread execution
        ai_response = await asyncio.to_thread(call_gemini, full_prompt)
        if ai_response:
            await message.reply_text(ai_response)
    except Exception as e:
        print(f"AI Error: {e}")

if __name__ == "__main__":
    print("🚀 Smart Telegram Bot စတင်ပွင့်နေပါပြီ...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)