import logging
from hydrogram import Client, filters, enums
from info import ADMINS
from utils import temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@Client.on_message(filters.command(['link', 'plink']) & filters.user(ADMINS))
async def gen_link_s(bot, message):
    """
    Generate a direct link for a file (Admin Only).
    Note: The file must be indexed in the database for the link to work.
    """
    replied = message.reply_to_message
    if not replied:
        return await message.reply('❌ **Reply to a media message to get a shareable link.**')
    
    file_type = replied.media
    if file_type not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
        return await message.reply("❌ **Unsupported media type.**\nPlease reply to Video, Audio, or Document.")
    
    # मीडिया ऑब्जेक्ट निकालना
    media = getattr(replied, file_type.value)
    file_id = media.file_id
    
    # लिंक जनरेट करना
    # commands.py 'file_' prefix के साथ ID एक्सपेक्ट करता है
    # लिंक: https://t.me/BotUser?start=file_FileID
    
    link = f"https://t.me/{temp.U_NAME}?start=file_{file_id}"
    
    await message.reply(
        f"🔗 **Here is your Link:**\n\n{link}",
        disable_web_page_preview=True
    )

