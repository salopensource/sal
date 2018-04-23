import base64
import bz2
import re


def class_to_title(text):
    return re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', text)


def safe_unicode(s):
    if isinstance(s, unicode):
        return s.encode('utf-8', errors='replace')
    else:
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


def decode_to_string(data, compression='base64bz2'):
    '''Decodes a string that is optionally bz2 compressed and always base64 encoded.'''
    if compression == 'base64bz2':
        try:
            bz2data = base64.b64decode(data)
            return bz2.decompress(bz2data)
        except Exception:
            return ''
    elif compression == 'base64':
        try:
            return base64.b64decode(data)
        except Exception:
            return
            ''

    return ''
