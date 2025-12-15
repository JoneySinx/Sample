import re
from os import environ

id_pattern = re.compile(r'^.\d+$')

def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# =========================================================
#                    BOT INFORMATION
# =========================================================
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ['API_ID'])
API_HASH = environ['API_HASH']
BOT_TOKEN = environ['BOT_TOKEN']

# =========================================================
#                    DATABASE (MongoDB)
# =========================================================
DATABASE_URI = environ.get('DATABASE_URI', "")
DATABASE_NAME = environ.get('DATABASE_NAME', "Simple")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_files')

# =========================================================
#                    ADMINS & CHANNELS
# =========================================================
# सिर्फ ADMINS ही बॉट को इस्तेमाल कर पाएंगे
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '').split()]

# जिन चैनल्स से फाइल इंडेक्स करनी है
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '0').split()]

# लॉग चैनल (Errors और Indexing Logs के लिए)
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', 0))

# =========================================================
#                    FEATURE SETTINGS
# =========================================================
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = is_enabled((environ.get('USE_CAPTION_FILTER', "True")), True)

# लिंक मोड में यह तय करेगा कि कंटेंट फॉरवर्ड (Protect) होगा या नहीं
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)

# अगर आप चाहते हैं कि फाइल के साथ कोई कस्टम कैप्शन जाए
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", None)

# सर्च में दिखने वाली तस्वीरें (अगर कोई फोटो नहीं मिली तो)
PICS = (environ.get('PICS', 'https://telegra.ph/file/7e56d907542396289fee4.jpg https://telegra.ph/file/9aa8dd372f4739fe02d85.jpg')).split()

# =========================================================
#                    LOGGING (Startup)
# =========================================================
LOG_STR = "Current Customized Configurations are:-\n"
LOG_STR += (f"CUSTOM_FILE_CAPTION enabled with value {CUSTOM_FILE_CAPTION}\n" if CUSTOM_FILE_CAPTION else "No CUSTOM_FILE_CAPTION Found.\n")
LOG_STR += ("PROTECT_CONTENT is enabled.\n" if PROTECT_CONTENT else "PROTECT_CONTENT is disabled.\n")

