import hashlib
from flask_login import UserMixin
from pymongo import MongoClient
from config import db_config
from hearthstone import deckstrings
from fireplace.player import Player
from cards_map import cards_map, cards_name_map


class DeckNameDuplicate(Exception):
    pass


class DeckNotExists(Exception):
    pass


class User(UserMixin):
    def __init__(self, username, password, decks={}):
        self.id = username
        self._password = self.encode(password)
        self._decks = decks
        self._current_deck_name = None
        self._player = None
        if len(self.decks) > 0:
            self.current_deck_name = list(self.decks)[0]
            deck = self.decks[self.current_deck_name]
            print(deck.card_list)
            print(deck.hero)
            self.player = Player(self.id, deck.card_list, deck.hero)
        self._playing_room = -1

    @property
    def decks(self):
        return self._decks

    @property
    def current_deck_name(self):
        return self._current_deck_name

    @property
    def player(self):
        return self._player

    @property
    def playing_room(self):
        return self._playing_room

    @decks.setter
    def decks(self, decks):
        self._decks = decks

    @current_deck_name.setter
    def current_deck_name(self, current_deck_name):
        self._current_deck_name = current_deck_name

    @player.setter
    def player(self, player):
        self._player = player

    @playing_room.setter
    def playing_room(self, playing_room):
        self._playing_room = playing_room

    @property
    def deck_json(self):
        response = {"decks": {}}
        for name in self.decks:
            deck = self.decks[name]
            response["decks"][name] = {
                "hero": deck.hero_name,
                "card_list": deck.card_list_name
            }
        response["current_deck"] = self.current_deck_name
        return response

    @classmethod
    def load(cls, data):
        username = data['_id']
        password = data['password']
        decks = {}
        for deck_name in data['decks']:
            decks[deck_name] = Deck(data['decks'][deck_name])
        user = cls(username, password, decks)
        user._password = password
        return user

    def serialize(self):
        deck_map = {}
        for name in self.decks:
            deck_map[name] = self.decks[name].code
        return {
            "_id": self.id,
            "password": self._password,
            "decks": deck_map
        }

    def authenticate(self, password):
        return self._password == self.encode(password)

    def add_deck(self, name, code):
        if name in self.decks:
            raise DeckNameDuplicate
        self.decks[name] = Deck(code)

    def choose_deck(self, name):
        if name not in self.decks:
            raise DeckNotExists
        self.current_deck_name = name
        deck = self.decks[name]
        self.player = Player(self.id, deck.card_list, deck.hero)

    def delete_deck(self, name):
        if name not in self.decks:
            raise DeckNotExists
        self.decks.remove(name)
        if self.current_deck_name == name:
            self.player = None
            self.current_deck_name = None
            if len(self.decks) > 0:
                self.current_deck_name = list(self.decks)[0]
                deck = self.decks[self.current_deck_name]
                self.player = Player(self.id, deck.card_list, deck.hero)

    @property
    def password(self):
        return '*'*len(self._password)

    @password.setter
    def password(self, password):
        self.password = self.encode(password)

    @staticmethod
    def encode(password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()


class Deck():
    def __init__(self, code):
        self.code = code
        self.deck = deckstrings.Deck().from_deckstring(code)

    @property
    def hero(self):
        return cards_map[self.deck.heroes[0]]

    @property
    def hero_name(self):
        return cards_name_map[self.hero]

    @property
    def card_list(self):
        card_list = []
        for card in self.deck.cards:
            print(card)
            card_id = cards_map[card[0]]
            card_num = card[1]
            card_list.extend([card_id for i in range(card_num)])
        return card_list

    @property
    def card_list_name(self):
        return [cards_name_map[card] for card in self.card_list]


class UserManager():
    def __init__(self):
        self.db = MongoClient(
            host=db_config['host'], port=db_config['password'])[db_config['db_name']]
        self.users = self.load_users()

    def load_users(self):
        users = {}
        for user in self.db.users.find({}):
            user = User.load(user)
            users[user.id] = user
        return users

    def save_user(self, user: User):
        self.users[user.id] = user
        self.db.users.save(user.serialize())
