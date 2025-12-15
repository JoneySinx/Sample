async def save_file(media):
    """Save file in database with Custom Formatting"""

    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)
    
    # --- NAME FORMATTING LOGIC ---
    raw_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    title_name = raw_name.title()
    file_name = re.sub(r'(?<=\s)L(?=\s)', 'l', title_name)
    # -----------------------------

    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
        except DuplicateKeyError:      
            # --- FIX: यहाँ हमने अपडेट लॉजिक जोड़ा है ---
            # अगर फाइल पहले से है, तो हम उसका नाम और कैप्शन अपडेट कर देंगे
            logger.warning(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database. Updating...'
            )
            
            await Media.collection.update_one(
                {'_id': file_id},
                {
                    '$set': {
                        'file_name': file_name,
                        'caption': media.caption.html if media.caption else None,
                        'file_ref': file_ref
                    }
                }
            )
            # -------------------------------------------
            
            # यह False रिटर्न करेगा ताकि channel.py में ♻️ इमोजी ही रहे (अगर नई फाइल नहीं है)
            # लेकिन डेटाबेस बैकग्राउंड में अपडेट हो चुका होगा।
            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            return True, 1

