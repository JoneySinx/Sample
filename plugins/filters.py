import re
from hydrogram import Client, filters
from info import ADMINS, PICS
from database.ia_filterdb import get_search_results
from utils import get_size
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.text & filters.incoming)
async def auto_filter(client, message):
    """
    Main Search Handler (Admin Only) - Works in PM & Groups
    """
    # 1. Check: सिर्फ एडमिन ही सर्च कर सके
    if message.from_user.id not in ADMINS:
        return

    # 2. कमांड्स (/start, /help) को इग्नोर करें
    if message.text.startswith("/"):
        return

    # 3. सर्च लॉजिक
    query = message.text
    if len(query) < 2:
        return

    try:
        # डेटाबेस से सर्च करें
        files, _, total_results = await get_search_results(query.lower(), max_results=50)

        if not files:
            return

        # 4. रिजल्ट को लिंक मोड (Link Mode) में बदलना
        results_text = f"<b>🔍 Results for:</b> <code>{query}</code>\n\n"
        bot_username = client.me.username

        for file in files:
            # एक्सटेंशन (.mkv, .mp4) हटाना
            file_name = re.sub(r'\.[a-zA-Z0-9]+$', '', file.file_name)
            file_size = get_size(file.file_size)
            
            # डायरेक्ट लिंक बनाना
            file_link = f"https://t.me/{bot_username}?start=file_{file.file_id}"
            
            results_text += f"📂 <a href='{file_link}'>{file_name}</a> <b>[{file_size}]</b>\n"

        # 5. मैसेज भेजना
        if PICS:
            await message.reply_photo(photo=PICS[0], caption=results_text, disable_web_page_preview=True)
        else:
            await message.reply_text(results_text, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error in auto_filter: {e}")

