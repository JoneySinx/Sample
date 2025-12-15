class script(object):
    # स्टार्ट मैसेज (सिर्फ एडमिन के लिए)
    START_TXT = """<b>👋 Hello Admin {},</b>

I am your private file manager bot.
I can index files from your channels and store them in the database.

<b>🔍 Features:</b>
• Auto Indexing with Title Formatting
• Smart Search (No Extensions)
• Direct File Links
• Status Emojis (✅ ♻️ ✏️)

<i>Use /help to see available commands.</i>"""

    # हेल्प मैसेज (सिर्फ काम के कमांड्स)
    HELP_TXT = """<b>🛠 Admin Commands:</b>

<b>📂 File Management:</b>
• <code>/link</code> - Reply to a file to get a Direct Link.
• <code>/delete</code> - Reply to a file to delete it from DB.
• <code>/stats</code> - Check total files in Database.
• <code>/logs</code> - Get the bot logs (for errors).

<b>⚙️ Indexing:</b>
• Just add me to your channel as Admin.
• I will auto-index new files.
• If you edit a caption, I will update the DB."""

    # अबाउट (About)
    ABOUT_TXT = """<b>🤖 Bot Info:</b>

✯ <b>Name:</b> {}
✯ <b>Owner:</b> <a href=https://t.me/TeamEvamaria>You</a>
✯ <b>Server:</b> Koyeb
✯ <b>Language:</b> Python 3
✯ <b>Library:</b> Hydrogram
✯ <b>Database:</b> MongoDB"""

    # स्टेटस (Stats)
    STATUS_TXT = """<b>📊 Database Status:</b>

★ <b>Total Files:</b> <code>{}</code>
★ <b>Storage Used:</b> <code>{}</code> MiB"""

    # लॉग्स (Logs)
    LOG_TEXT_G = """#NewGroup
<b>Group:</b> {}(<code>{}</code>)
<b>Total Members:</b> <code>{}</code>"""

    LOG_TEXT_P = """#NewUser
<b>ID:</b> <code>{}</code>
<b>Name:</b> {}"""

