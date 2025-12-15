import logging
from hydrogram import enums
from typing import Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Temporary Cache for Bot Info ---
class temp(object):
    ME = None
    U_NAME = None # Username
    B_NAME = None # Bot Name

def get_size(size):
    """
    Get size in readable format (Bytes, KB, MB, GB)
    """
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def get_file_id(msg):
    """
    Extract File ID from a message (Document, Video, Audio, etc.)
    """
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message) -> Union[int, str]:
    """
    Extracts the user ID and Name from a message
    """
    user_id = None
    user_first_name = None
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name

    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            user_first_name = user_id
            try:
                user_id = int(user_id)
            except ValueError:
                pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
        
    return (user_id, user_first_name)

