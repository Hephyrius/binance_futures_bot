import json
from types import SimpleNamespace

def getBotSettings():
    return json.load(open ("settings.json", "r"), object_hook=lambda d: SimpleNamespace(**d)) #convert array to object

def getAPIKeys():
    return json.load(open ("keys.json", "r"), object_hook=lambda d: SimpleNamespace(**d)) #convert array to object

def getPublicKey():
    return getAPIKeys().api_key

def getPrivateKey():
    return getAPIKeys().api_secret
