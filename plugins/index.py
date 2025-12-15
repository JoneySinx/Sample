import asyncio
import logging
import re

from hydrogram import Client, filters, enums
from hydrogram.errors import FloodWait
from hydrogram.errors import (
    ChannelInvalid,
    ChatAdminRequired,
    UsernameInvalid,
    UsernameNotModified
)
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from info import ADMINS
from info import INDEXREQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from utils import temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

lock = asyncio.Lock()


# ----------------- /setskip ----------------- #

@Client.on_message(filters.command("setskip") & filters.user(ADMINS))
async def set_skip_number(bot: Client, message):
    if " " in message.text:
        _, skip = message.text.split(" ", 1)
        try:
            skip = int(skip)
        except ValueError:
            return await message.reply("Skip number should be an integer.")
        temp.CURRENT = skip
        await message.reply(f"Successfully set SKIP number as {skip}")
    else:
        await message.reply("Give me a skip number")


# ------------- accept / reject index -------- #

@Client.on_callback_query(filters.regex(r"^index"))
async def index_files(bot: Client, query):
    if query.data == "index_cancel":
        temp.CANCEL = True
        return await query.answer("Cancelling indexing ...", show_alert=True)

    _tag, action, chat, last_msg_id, from_user = query.data.split("#")

    if action == "reject":
        await query.message.delete()
        await bot.send_message(
            int(from_user),
            f"Your submission for indexing {chat} has been declined by moderators.",
            reply_to_message_id=int(last_msg_id)
        )
        return

    if lock.locked():
        return await query.answer(
            "Wait until previous indexing process completes.",
            show_alert=True
        )

    msg = query.message
    await query.answer("Processing ...", show_alert=True)

    if int(from_user) not in ADMINS:
        await bot.send_message(
            int(from_user),
            f"Your submission for indexing {chat} has been accepted and will be added soon.",
            reply_to_message_id=int(last_msg_id)
        )

    await msg.edit(
        "Starting indexing ...",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="index_cancel")]]
        )
    )

    try:
        chat_id = int(chat)
    except ValueError:
        chat_id = chat

    await index_files_to_db(int(last_msg_id), chat_id, msg, bot)


# --------- user se index request lena -------- #

@Client.on_message(
    (
        filters.regex(r"https?://t.me/[wd_]+/d+") |
        filters.forwarded
    )
    & filters.text
    & filters.private
    & filters.incoming
)
async def send_for_index(bot: Client, message):
    chat_id = None
    last_msg_id = None

    # 1) direct link
    if message.text:
        m = re.match(r"https?://t.me/([wd_]+)/(d+)", message.text)
        if m:
            chat_id = m.group(1)
            last_msg_id = int(m.group(2))

    # 2) forwarded from channel
    if not chat_id and message.forward_from_chat:
        if message.forward_from_chat.type != enums.ChatType.CHANNEL:
            return
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
        last_msg_id = message.forward_from_message_id

    if not chat_id or not last_msg_id:
        return await message.reply("Invalid link.")

    # chat exist / bot admin check
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply("This looks like a private channel/group. Make me admin there.")
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply("Invalid link specified.")
    except Exception as e:
        logger.exception(e)
        return await message.reply(f"Error: {e}")

    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except Exception:
        return await message.reply("Make sure I am admin in that chat.")
    if k.empty:
        return await message.reply("This might be a group where I am not admin.")

    # अगर खुद admin ने भेजा
    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton(
                    "Yes",
                    callback_data=f"index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}"
                ),
                InlineKeyboardButton("Close", callback_data="closedata")
            ]
        ]
        return await message.reply(
            f"Do you want to index this chat?

"
            f"ID / Username: `{chat_id}`
"
            f"Last message ID: `{last_msg_id}`",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # नहीं तो LOG_CHANNEL को request
    if isinstance(chat_id, int):
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply(
                "Make sure I am admin in the chat and have permission to invite users."
            )
    else:
        link = f"https://t.me/{chat_id}"

    buttons = [
        [
            InlineKeyboardButton(
                "Accept Index",
                callback_data=f"index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}"
            ),
            InlineKeyboardButton(
                "Reject Index",
                callback_data=f"index#reject#{chat_id}#{message.id}#{message.from_user.id}"
            )
        ]
    ]

    await bot.send_message(
        LOG_CHANNEL,
        (
            "#IndexRequest

"
            f"By: {message.from_user.mention} (`{message.from_user.id}`)
"
            f"Chat ID / Username: `{chat_id}`
"
            f"Last Message ID: `{last_msg_id}`
"
            f"Invite link: {link}"
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await message.reply(
        "Thank you for the contribution, wait for moderators to verify the files."
    )


# ----------------- main indexing loop ----------------- #

async def index_files_to_db(last_msg_id: int, chat, msg, bot: Client):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0

    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False

            async for message in bot.iter_messages(chat, last_msg_id, temp.CURRENT):
                if temp.CANCEL:
                    await msg.edit(
                        "Successfully cancelled!!

"
                        f"Saved `{total_files}` files to database!
"
                        f"Duplicate files skipped: `{duplicate}`
"
                        f"Deleted messages skipped: `{deleted}`
"
                        f"Non‑media messages skipped: `{no_media + unsupported}` "
                        f"(Unsupported media: `{unsupported}`)
"
                        f"Errors occurred: `{errors}`"
                    )
                    break

                current += 1

                if current % 20 == 0:
                    can = [[InlineKeyboardButton("Cancel", callback_data="index_cancel")]]
                    await msg.edit_text(
                        text=(
                            f"Total messages fetched: `{current}`
"
                            f"Total messages saved: `{total_files}`
"
                            f"Duplicate files skipped: `{duplicate}`
"
                            f"Deleted messages skipped: `{deleted}`
"
                            f"Non‑media messages skipped: `{no_media + unsupported}` "
                            f"(Unsupported media: `{unsupported}`)
"
                            f"Errors occurred: `{errors}`"
                        ),
                        reply_markup=InlineKeyboardMarkup(can)
                    )

                if message.empty:
                    deleted += 1
                    continue
                if not message.media:
                    no_media += 1
                    continue
                if message.media not in (
                    enums.MessageMediaType.VIDEO,
                    enums.MessageMediaType.AUDIO,
                    enums.MessageMediaType.DOCUMENT,
                ):
                    unsupported += 1
                    continue

                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue

                media.file_type = message.media.value
                media.caption = message.caption

                try:
                    ok, code = await save_file(media)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    ok, code = await save_file(media)

                if ok:
                    total_files += 1
                elif code == 0:
                    duplicate += 1
                elif code == 2:
                    errors += 1

        except Exception as e:
            logger.exception(e)
            await msg.edit(f"Error: {e}")
        else:
            await msg.edit(
                "Successfully saved "
                f"`{total_files}` files to database!
"
                f"Duplicate files skipped: `{duplicate}`
"
                f"Deleted messages skipped: `{deleted}`
"
                f"Non‑media messages skipped: `{no_media + unsupported}` "
                f"(Unsupported media: `{unsupported}`)
"
                f"Errors occurred: `{errors}`"
            )
