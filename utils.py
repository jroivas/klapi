import random
import string
import uuid

def generatePassword(characters=8):
    # Disabling 0 and O to prevent misreadings
    return ''.join(random.SystemRandom().choice(string.letters.replace('O','') + string.digits.replace('0','')) for _ in range(characters))

def generateID():
    return str(uuid.uuid4())

def generateApiKey():
    return generateID()

