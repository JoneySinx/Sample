# plugins/search_results.py

from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_size

def display_name(file_name: str) -> str:
    # result में extension नहीं दिखानी
    return file_name.rsplit(".", 1)[0]

def build_text_results(query: str, files: list, total: int, user_mention: str) -> str:
    lines = []
    lines.append(f"✅ Search Results : {query}")
    lines.append(f"👤 Requested By : {user_mention}")
    lines.append(f"📁 Total File Found : {total}")
    lines.append("")  # blank line

    for f in files:
        size = get_size(f.file_size)
        name = display_name(f.file_name)
        lines.append(f"[{size}] {name}")

    return "
".join(lines)

def build_keyboard(req_id: int, key: str, offset: int, total: int, n_offset: int):
    # current page
    try:
        page_now = (offset // 10) + 1
    except ZeroDivisionError:
        page_now = 1
    total_pages = (total + 9) // 10

    if 0 < offset <= 10:
        back_offset = 0
    elif offset == 0:
        back_offset = None
    else:
        back_offset = offset - 10

    rows = [
        [
            InlineKeyboardButton("🌐 LANGUAGE", callback_data=f"lang_{key}"),
            InlineKeyboardButton("📤 SEND ALL", callback_data=f"sendall_{key}"),
            InlineKeyboardButton("🎞 QUALITY", callback_data=f"quality_{key}"),
        ]
    ]

    nav_row = []
    if back_offset is not None:
        nav_row.append(
            InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req_id}_{key}_{back_offset}")
        )
    nav_row.append(
        InlineKeyboardButton(f"{page_now}/{total_pages}", callback_data="pages")
    )
    if n_offset != 0:
        nav_row.append(
            InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req_id}_{key}_{n_offset}")
        )

    rows.append(nav_row)
    return InlineKeyboardMarkup(rows)
