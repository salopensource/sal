import base64
import bz2
import re


def class_to_title(text):
    return re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', text)


def safe_bytes(s):
    """Return utf-8 encoded bytes, replacing chars if needed."""
    # This handles the special case that postgres can't write a null
    # charecter to a TextField.
    # TODO: This function is provisional until we can remove it.
    if isinstance(s, str):
        s = s.encode('utf-8', errors='replace')
    if isinstance(s, bytes):
        s = s.replace(b'\x00', b'')
    # What's going on here? Most of the time this is supposed to take
    # text as input; but sometimes it's getting bools or model instances
    # so we can't just blindly do a replcae method on everything!
    return s


def stringify(data):
    """Sanitize collection data into a string format for db storage.

    Args:
        data (str, bool, numeric, dict, list): Condition values to
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


def decode_to_string(data, compression=''):
    """Decodes a string optionally bz2 compressed and/or base64 encoded.

    Will decode base64 first if specified. Then decompress bz2 if
    specified.

    Args:
        data (str): Data to decode. May just be a regular string!
        compression (str): Type of encoding and compression. Defaults
            to empty str. Uses substrings to determine what to do:
            'base64' results in first base64 decoding.
            'bz2' results in bz2.decompression.

    Returns:
        The decoded, decompressed string, or '' if there were
        exceptions.
    """
    if 'base64' in compression:
        try:
            data = base64.b64decode(data)
        except TypeError:
            data = ''

    if 'bz2' in compression:
        try:
            data = bz2.decompress(data)
        except IOError:
            data = ''

    return data
