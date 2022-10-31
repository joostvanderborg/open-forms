from typing import Tuple


def restructure_names_to_zgw(first_name: str, last_name: str) -> Tuple[str, str, str]:
    """
    minimal effort to get a Django first_name/last_name vaguely in ZGW shape
    """
    letters = " ".join(f[0].upper() for f in first_name.split(None))
    last_parts = last_name.rsplit(None, maxsplit=1)
    prefix = ""
    if len(last_parts) > 1:
        prefix = last_parts[0].lower()
        last_name_parts = last_parts[1].title()
    elif len(last_parts) == 1:
        last_name_parts = last_parts[0].title()
    else:
        last_name_parts = ""
    return letters, prefix, last_name_parts
