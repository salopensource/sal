import base64
import binascii
import bz2
import plistlib
import re
from typing import Any, Union, Dict
from xml.parsers.expat import ExpatError


Plist = Dict[str, Any]
Text = Union[str, bytes]


def class_to_title(text):
    return re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', text)


def safe_text(text: Any) -> str:
    """Process text of any type to ensure it can be saved in the DB."""
    # Ensure bytes get decoded, no matter what, to unicode.
    if isinstance(text, bytes):
        text = text.decode('UTF-8', errors='replace')
    elif not isinstance(text, str):
        text = str(text)
    # Replace null characters with nothing to prevent db errors.
    return text.replace('\x00', '')


def stringify(data):
    """Sanitize collection data into a string format for db storage.

    Args:
        data (str, bool, numeric, dict, list): Values to
            squash into strings.

    Returns:
        list data returns as a comma separated string or '{EMPTY}'
        if the list is empty.

        All other data types are `str()` converted, including nested
        collections in a list.
    """
    if isinstance(data, list):
        return ", ".join(str(i) for i in data) if data else "{EMPTY}"

    # Handle dict, int, float, bool values.
    return str(data)


def decode_submission_data(data: Text, compression: str = '') -> bytes:
    """Returns bytes from compressed or base64 encoded text.

    Sal submissions include plist data that has been base64 encoded
    and bz2 coompressed. Historically, this data may also have been
    passed as just text, or only base64 encoded.

    This function first decodes from base64 to bytes. Then it will
    perforom bz2 decompression if requested. As this data is normally
    then parsed through plistlib, the data is returned as bytes under
    all circumstances.

    Args:
        data (str, bytes): Data to decode. May just be a regular string!
        compression (str): Type of encoding and compression. Defaults
            to empty str. Uses substrings to determine what to do:
            'base64' results in first base64 decoding.
            'bz2' results in bz2.decompression.

    Returns:
        The decoded, decompressed bytes, or b'' if there were
        exceptions.
    """
    if 'base64' in compression:
        try:
            data = base64.b64decode(data)
        except (TypeError, binascii.Error):
            data = b''

    if 'bz2' in compression:
        try:
            data = bz2.decompress(data)
        except IOError:
            data = b''

    # Make sure we're returning bytes, even if the compression
    # arg is empty.
    if isinstance(data, str):
        data = data.encode()

    return data


def submission_plist_loads(data: Text, compression: str = '') -> Plist:
    if compression:
        data = decode_submission_data(data, compression)
    if isinstance(data, str):
        data = data.encode()
    try:
        plist = plistlib.loads(data)
    except (plistlib.InvalidFileException, ExpatError):
        plist = {}
    return plist


def is_valid_plist(data: Text) -> bool:
    if isinstance(data, str):
        data = data.encode()
    try:
        plistlib.loads(data)
        return True
    except (plistlib.InvalidFileException, ExpatError):
        return False
