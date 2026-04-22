import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from threading import Thread
import time

# Tokenni to'g'ridan-to'g'ri shu yerga yozdim, hech qanday os.getenv shartmas
TOKEN = '8778441842:AAGcBN58qsOQ6YWaDQlOgmWSF8I75FMhFKA'
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DOWNLOAD_PATH = 'downloads'
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

user_data = {}

def download_media(chat_id, url, mode, msg_id):
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        })
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        bot.edit_message_text("⏳ <b>Iltimos, biroz kutib turing...</b>\nSiz uchun faylni tayyorlayapman 😊", chat_id, msg_id)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            f_path = ydl.prepare_filename(info)
            if mode == 'audio': f_path = os.path.splitext(f_path)[0] + ".mp3"

            with open(f_path, 'rb') as f:
                bot.send_chat_action(chat_id, 'upload_document')
                title = info.get('title', 'Media')
                cap = f"✨ <b>Marhamat, siz so'ragan fayl tayyor!</b>\n\n🎵 <b>Nomi:</b> {title}\n\n🤝 <b>Xizmatingizda ekanimdan xursandman!</b>"
                if mode == 'audio': bot.send_audio(chat_id, f, caption=cap)
                else: bot.send_video(chat_id, f, caption=cap)
            if os.path.exists(f_path): os.remove(f_path)
        bot.delete_message(chat_id, msg_id)
    except:
        bot.edit_message_text("😔 <b>Uzr, biroz muammo chiqdi...</b>\nFayl juda katta yoki linkda xatolik bor shekilli.", chat_id, msg_id)

@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    welcome = (f"👋 <b>Assalomu alaykum, {name}!</b>\n\n"
               "Xush kelibsiz! Men sizga video yoki musiqalarni yuklab olishda yordam beraman. ✨\n\n"
               "👇 <b>Nima qilamiz?</b>\n"
               "• Video <b>linkini</b> yuboring\n"
               "• Yoki musiqa <b>nomini</b> yozing")
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text.strip()
    if text.startswith('http'):
        user_data[message.chat.id] = text
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🎬 Video yuklash", callback_data="v"),
                   types.InlineKeyboardButton("🎵 MP3 yuklash", callback_data="a"))
        bot.send_message(message.chat.id, "💎 <b>Ajoyib tanlov!</b>\nQaysi formatda yuklab beray?", reply_markup=markup)
    else:
        search_music(message.chat.id, text, offset=1)

def search_music(chat_id, query, offset=1):
    status = bot.send_message(chat_id, "🔍 <b>Siz uchun qidiryapman...</b>")
    limit = 5
    with YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
        try:
            results = ydl.extract_info(f"ytsearch{offset + limit - 1}:{query}", download=False)['entries']
            current_results = results[offset-1:]
            if not current_results:
                bot.edit_message_text("😔 <b>Hech narsa topilmadi...</b>", chat_id, status.message_id)
                return
            markup = types.InlineKeyboardMarkup()
            for i, video in enumerate(current_results, start=offset):
                markup.add(types.InlineKeyboardButton(f"🎧 {video.get('title')[:40]}...", callback_data=f"dl|{video.get('id')}"))
            nav = []
            if offset > 1: nav.append(types.InlineKeyboardButton("⬅️ Avvalgilar", callback_data=f"next|{max(1, offset-5)}|{query}"))
            nav.append(types.InlineKeyboardButton("Keyingilar ➡️", callback_data=f"next|{offset + 5}|{query}"))
            markup.add(*nav)
            bot.edit_message_text(f"🎯 <b>Natijalar:</b>", chat_id, status.message_id, reply_markup=markup)
        except: bot.edit_message_text("❌ Qidiruvda xatolik yuz berdi.", chat_id, status.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data.startswith("dl|"):
        url = f"https://www.youtube.com/watch?v={call.data.split('|')[1]}"
        mid = bot.send_message(chat_id, "🚀 <b>Tayyorlanyapti...</b>").message_id
        Thread(target=download_media, args=(chat_id, url, 'audio', mid)).start()
    elif call.data.startswith("next|"):
        _, next_off, query = call.data.split('|')
        bot.delete_message(chat_id, call.message.message_id)
        search_music(chat_id, query, offset=int(next_off))
    elif call.data in ['v', 'a']:
        url = user_data.get(chat_id)
        if url:
            mode = 'audio' if call.data == 'a' else 'video'
            mid = bot.send_message(chat_id, "🚀 <b>Boshladik!</b>").message_id
            Thread(target=download_media, args=(chat_id, url, mode, mid)).start()

if __name__ == "__main__":
    print("✅ Bot yoqildi!")
    bot.infinity_polling(timeout=90)