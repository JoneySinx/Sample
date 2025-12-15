import logging
from hydrogram import Client, __version__
from hydrogram.raw.all import layer
from database.ia_filterdb import Media
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR
from utils import temp

# --- Simple Logging Setup (No external file needed) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("hydrogram").setLevel(logging.ERROR)

class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        # Hydrogram Client Start
        await super().start()
        
        # Database Indexes Create karna (Fast Search ke liye)
        await Media.ensure_indexes()
        
        # Bot Info Fetch karna
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        
        # Logs print karna
        logging.info(f"{me.first_name} with Hydrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

# Bot Start
app = Bot()
app.run()

