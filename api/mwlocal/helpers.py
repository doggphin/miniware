import json

with open("names_to_drives.json", 'r') as file:
    NAMES_TO_DRIVES = json.load(file)

def make_message(message : str):
    return { "message" : message }