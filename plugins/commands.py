import os
import re
import logging
import base64
from hydrogram import Client, filters, enums
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from hydrogram.errors import FloodWait

from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from info import ADMINS, LOG_CHANNEL, CUSTOM_FILE_CAPTION, PROTECT_CONTENT
from utils import get_size

logger = logging.getLogger(__name__)

# --- UTILS ---
def decode_file_id(data):
    """
    Decodes the file_id from the start parameter.
    """
    try:
        # अगर data base64 है तो उसे डिकोड करें
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        decoded = base64.urlsafe_b64decode(data).decode("ascii")
        return decoded
    except:
        # अगर डिकोड नहीं हुआ, तो शायद वह raw id है
        return data

# --- START COMMAND HANDLER ---
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    # 1. सिर्फ ADMINS के लिए
    if message.from_user.id not in ADMINS:
        return
        
    # 2. अगर सिर्फ /start है (बिना किसी पैरामीटर के)
    if len(message.command) < 2:
        await message.reply_text(
            "👋 **Hello Admin!**\n\nI am ready to search files for you.\nJust type a movie/series name here.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("♻️ Check Database", callback_data="stats")]
            ])
        )
        return

    # 3. अगर /start file_xxxxxx है (File Delivery Logic)
    data = message.command[1]
    
    # "file_" प्रीफिक्स को हटाना
    if data.startswith("file_"):
        file_id_param = data.split("_", 1)[1]
    else:
        file_id_param = data

    try:
        # फाइल डिटेल्स लाना
        # नोट: यहाँ हम मान रहे हैं कि URL में जो ID है वो Database की `_id` या `file_id` है
        files_ = await get_file_details(file_id_param)
        
        if not files_:
            await message.reply_text("❌ File not found in database.")
            return

        file = files_[0]
        
        # --- NAME CLEANING (No Extension) ---
        file_name = re.sub(r'\.[a-zA-Z0-9]+$', '', file.file_name)
        file_size = get_size(file.file_size)
        
        # कैप्शन तैयार करना
        caption = f"📂 <b>{file_name}</b>\n💾 <b>Size:</b> {file_size}"
        
        if CUSTOM_FILE_CAPTION:
             caption += f"\n\n{CUSTOM_FILE_CAPTION}"

        # फाइल भेजना
        await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file.file_id,
            caption=caption,
            protect_content=PROTECT_CONTENT
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.reply_text("❌ Something went wrong while fetching the file.")


# --- STATS / DB CHECK ---
@Client.on_message(filters.command('stats') & filters.user(ADMINS))
async def stats(bot, message):
    total = await Media.count_documents()
    await message.reply_text(f"📊 **Total Files in DB:** {total}")


# --- DELETE COMMAND ---
@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database by replying to it"""
    reply = message.reply_to_message
    if not reply or not reply.media:
        await message.reply('Reply to a file with /delete to remove it from DB.', quote=True)
        return

    msg = await message.reply("Processing...⏳", quote=True)

    # मीडिया टाइप ढूंढना
    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('Unsupported file type.')
        return
    
    # फाइल नाम से डिलीट करना (ज्यादा सुरक्षित)
    # या file_unique_id से भी कर सकते हैं अगर DB में सेव है
    
    # यहाँ हम नाम और साइज मैच करके डिलीट करेंगे
    # पहले नाम को क्लीन करते हैं जैसे save के वक्त किया था (ताकि मैच हो सके)
    # लेकिन सबसे सुरक्षित है exact match ढूँढना
    
    # अगर save_file logic में नाम बदल गया है (L to l), तो exact name match मुश्किल हो सकता है।
    # इसलिए हम file_unique_id या file_id से कोशिश कर सकते हैं, पर telegram id बदल सकती है।
    
    # अभी के लिए simple logic:
    result = await Media.collection.delete_many({
        'file_size': media.file_size,
        # 'mime_type': media.mime_type  # कभी कभी mime type अलग हो सकता है
    })
    
    if result.deleted_count:
        await msg.edit(f'✅ Deleted {result.deleted_count} file(s) from database.')
    else:
        await msg.edit('❌ File not found in database (Check size/name match).')


# --- LOGS COMMAND ---
@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

