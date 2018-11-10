import base64
import bz2
import re
import typing


def class_to_title(text):
    return re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', text)


def safe_text(text: typing.Any) -> str:
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
