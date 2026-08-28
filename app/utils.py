import random
import string

# Characters used to build short codes: mixed-case letters + digits.
_ALPHABET = string.ascii_letters + string.digits
_CODE_LENGTH = 6


def generate_short_code(length: int = _CODE_LENGTH) -> str:
    """Generate a random alphanumeric short code.

    Using a random code (rather than a sequential counter) avoids
    leaking the total number of URLs stored and avoids collisions
    tied to database auto-increment ids.
    """
    return "".join(random.choices(_ALPHABET, k=length))
