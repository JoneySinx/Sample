import logging
from struct import pack
import re
import base64
from hydrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Database Connection ---
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def save_file(media):
    """
    Save file in database with Custom Formatting & Update Logic
    """

    # 1. File ID और Reference निकालना
    file_id, file_ref = unpack_new_file_id(media.file_id)
    
    # 2. --- NAME FORMATTING LOGIC ---
    # सिम्बल्स को स्पेस में बदलना
    raw_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    
    # Title Case (पहला अक्षर बड़ा)
    title_name = raw_name.title()
    
    # Special Rule: ' L ' (जिसके दोनों तरफ स्पेस हो) को ' l ' करना
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
            # नई फाइल सेव करने की कोशिश
            await file.commit()
        except DuplicateKeyError:      
            # 3. --- UPDATE LOGIC ---
            # अगर फाइल पहले से है, तो हम उसका नाम, कैप्शन और ref अपडेट कर देंगे
            logger.warning(
                f'{getattr(media, "file_name", "NO_FILE")} is already saved in database. Updating details...'
            )
            
            # पुराना डेटा अपडेट करें
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
            
            # False रिटर्न करने से channel.py में ♻️ इमोजी लगेगा (Duplicate/Existing)
            # लेकिन बैकग्राउंड में डेटा अपडेट हो चुका है।
            return False, 0
        else:
            logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
            # True रिटर्न करने से channel.py में ✅ इमोजी लगेगा (New File)
            return True, 1

async def get_search_results(query, file_type=None, max_results=10, offset=0, filter=False):
    """
    Search query in database and return results
    """
    query = query.strip()

    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return [], '', 0

    if USE_CAPTION_FILTER:
        # नाम या कैप्शन दोनों में ढूँढेगा
        filter_criteria = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        # सिर्फ नाम में ढूँढेगा
        filter_criteria = {'file_name': regex}

    if file_type:
        filter_criteria['file_type'] = file_type

    total_results = await Media.count_documents(filter_criteria)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter_criteria)
    # Sort by recent (Newest first)
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    files = await cursor.to_list(length=max_results)

    return files, next_offset, total_results

async def get_file_details(query):
    filter_criteria = {'file_id': query}
    cursor = Media.find(filter_criteria)
    filedetails = await cursor.to_list(length=1)
    return filedetails

# --- Helper Functions for File ID ---

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

