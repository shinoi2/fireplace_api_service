from fireplace.cards import db
from config import game_language

db.initialize(game_language)
cards_map = {}
cards_name_map = {}

for id in db:
    cards_map[db[id].dbf_id] = id
    cards_name_map[id] = db[id].name
