import asyncio
import re
import ast
import math
import logging

from hydrogram import Client, filters, enums
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.errors import (
    FloodWait,
    UserIsBlocked,
    MessageNotModified,
    PeerIdInvalid,
    MediaEmpty,
    PhotoInvalidDimensions,
    WebpageMediaEmpty,
)

from Script import script
from database.connections_mdb import (
    active_connection,
    all_connections,
    delete_connection,
    if_active,
    make_active,
    make_inactive,
)
from info import (
    ADMINS,
    AUTH_CHANNEL,
    AUTH_USERS,
    CUSTOM_FILE_CAPTION,
    AUTH_GROUPS,
    P_TTI_SHOW_OFF,
    IMDB,
    SINGLE_BUTTON,
    SPELL_CHECK_REPLY,
    IMDB_TEMPLATE,
)
from utils import (
    get_size,
    is_subscribed,
    get_poster,
    search_gagala,
    temp,
    get_settings,
    save_group_settings,
)
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import del_all, find_filter, get_filters

from .search_results import build_text_results, build_keyboard   # नया helper

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client: Client, message):
    k = await manual_filters(client, message)
    if k is False:
        await auto_filter(client, message)


@Client.on_callback_query(filters.regex(r"^next_"))
async def next_page(bot: Client, query: CallbackQuery):
    ident, req, key, offset = query.data.split("_")

    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("oKda", show_alert=True)

    try:
        offset = int(offset)
    except Exception:
        offset = 0

    search = BUTTONS.get(key)
    if not search:
        return await query.answer(
            "You are using one of my old messages, please send the request again.",
            show_alert=True,
        )

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)

    try:
        n_offset = int(n_offset)
    except Exception:
        n_offset = 0

    if not files:
        return

    user_mention = query.from_user.mention if query.from_user else "Guest"
    text = build_text_results(search, files, total, user_mention)
    kb = build_keyboard(int(req), key, offset, total, n_offset)

    try:
        await query.message.edit_text(text=text, reply_markup=kb, disable_web_page_preview=True)
    except MessageNotModified:
        pass

    await query.answer()


async def auto_filter(client: Client, msg, spoll: bool = False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)

        # commands ignore
        if message.text.startswith("/"):
            return

        # emoji spam ignore
        if re.findall(r"[^ws]", message.text) and len(message.text) <= 2:
            return

        if 2 <= len(message.text) <= 100:
            search = message.text
            files, offset, total_results = await get_search_results(
                search.lower(), offset=0, filter=True
            )

            if not files:
                if settings["spellcheck"]:
                    return await advantage_spell_chok(msg)
                return
        else:
            return
    else:
        # spoll से आया हुआ (spell check)
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll

    # result text + keyboard बनाना
    key = f"{message.chat.id}-{message.id}"
    BUTTONS[key] = search

    user_mention = message.from_user.mention if message.from_user else "Guest"
    text = build_text_results(search, files, total_results, user_mention)
    kb = build_keyboard(
        message.from_user.id if message.from_user else 0,
        key,
        offset,
        total_results,
        offset,  # first call में n_offset के लिए 0 या offset; बाद में next_page handle करेगा
    )

    if not spoll:
        await message.reply_text(
            text,
            reply_markup=kb,
            disable_web_page_preview=True,
        )
    else:
        await msg.message.edit_text(
            text,
            reply_markup=kb,
            disable_web_page_preview=True,
        )
