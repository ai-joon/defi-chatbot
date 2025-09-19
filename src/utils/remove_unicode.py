import re
import unicodedata


def remove_unicode(string):
    # Remove combining characters
    string = unicodedata.normalize("NFKD", string)
    string = "".join([c for c in string if not unicodedata.combining(c)])

    # Remove remaining non-ASCII characters
    string = re.sub(r"[^\x00-\x7F]+", "", string)

    return string