import random
import string

def generate_api_key():

    characters = string.ascii_uppercase + string.digits

    key = '-'.join(
        ''.join(random.choices(characters, k=4))
        for _ in range(4)
    )

    return key