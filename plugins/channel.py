import re
from hydrogram import Client, filters
from hydrogram.types import Message
from info import CHANNELS
from database.ia_filterdb import save_file

# मीडिया फिल्टर
media_filter = filters.document | filters.video | filters.audio

def modify_name(name):
    """
    यह फंक्शन फाइल के नाम को आपके नियमों के अनुसार सुधारता है:
    1. डॉट्स (.) और अंडरस्कोर (_) को हटाकर स्पेस बनाता है।
    2. Title Case करता है (पहला अक्षर बड़ा)।
    3. अगर ' L ' है तो उसे ' l ' करता है।
    """
    if not name:
        return name

    # 1. रिप्लेसमेंट और टाइटल केस
    # हम एक्सटेंशन को अलग नहीं कर रहे क्योंकि आपने कहा था डेटाबेस में एक्सटेंशन के साथ सेव करना है।
    # लेकिन .mkv को स्पेस .Mkv बनने से रोकने के लिए हम बेसिक टाइटल का यूज़ करेंगे।
    
    clean_name = name.replace("_", " ").title()

    # 2. ' L ' को ' l ' करना (Regex Logic)
    # (?<=\s) मतलब पीछे स्पेस हो, (?=\s) मतलब आगे स्पेस हो
    clean_name = re.sub(r'(?<=\s)L(?=\s)', 'l', clean_name)
    
    return clean_name

async def append_emoji(message, emoji):
    """
    यह फंक्शन मैसेज के कैप्शन में इमोजी जोड़ता है।
    """
    try:
        caption = message.caption if message.caption else ""
        
        # अगर इमोजी पहले से है तो वापस लौट जाएं
        if emoji in caption:
            return

        # पुराने इमोजी को साफ करें (ताकि ✅ के बाद ✏️ आए तो ✅ हट जाए)
        clean_caption = caption.replace("✅", "").replace("♻️", "").replace("✏️", "").strip()
        
        # नया कैप्शन तैयार करें
        new_caption = f"{clean_caption} {emoji}"
        
        # टेलीग्राम की लिमिट (1024) चेक करें
        if len(new_caption) < 1024:
            await message.edit_caption(new_caption)
    except Exception as e:
        print(f"Error appending emoji: {e}")

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """
    नई फाइल आने पर उसे प्रोसेस और सेव करता है।
    """
    # सही मीडिया टाइप ढूँढना
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return

    # मीडिया ऑब्जेक्ट में कस्टम प्रॉपर्टी सेट करना
    media.file_type = file_type
    media.caption = message.caption
    
    # --- NAME LOGIC ---
    # फाइल का नाम सुधार कर डेटाबेस में भेजेंगे
    if hasattr(media, 'file_name') and media.file_name:
        media.file_name = modify_name(media.file_name)

    try:
        # save_file को कॉल करें
        is_new = await save_file(media)
        
        if is_new:
            # नई फाइल है -> ✅
            await append_emoji(message, "✅")
        else:
            # डुप्लीकेट है -> ♻️
            await append_emoji(message, "♻️")
            
    except Exception as e:
        print(f"Error saving file: {e}")
        # एरर आने पर भी हम मान सकते हैं कि डुप्लीकेट या कोई इशू है
        await append_emoji(message, "♻️")

@Client.on_edited_message(filters.chat(CHANNELS) & media_filter)
async def media_edit(bot, message):
    """
    अगर एडमिन मैसेज एडिट करता है, तो डेटाबेस अपडेट होगा।
    """
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return

    media.file_type = file_type
    media.caption = message.caption
    
    # एडिट करते वक्त भी नाम सुधारें
    if hasattr(media, 'file_name') and media.file_name:
        media.file_name = modify_name(media.file_name)

    try:
        # अपडेट करने की कोशिश
        await save_file(media)
        # अपडेट सफल -> ✏️
        await append_emoji(message, "✏️")
    except Exception as e:
        print(f"Error updating file: {e}")

