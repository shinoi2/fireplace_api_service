from fireplace.player import Player
from fireplace.game import Game


class RoomFull(Exception):
    pass


class RoomNotExists(Exception):
    pass


class Room():
    def __init__(self):
        self.id = -1
        self.players = []
        self.game = None

    def add_player(self, player):
        if len(self.players) >= 2:
            raise RoomFull

        self.players.append(player)
        if len(self.players) == 2:
            self.game = Game(players=self.players)
            self.game.start()


class RoomManager:
    def __init__(self):
        self.rooms = [None]

    def create_room(self):
        room = Room()
        self.rooms.append(room)
        room.id = self.rooms.index(room)
        return room

    def join_room(self, room_id, user):
        if room_id < 0 or room_id >= len(self.rooms) or not self.rooms[room_id]:
            raise RoomNotExists()

        room = self.rooms[room_id]
        print(user.player)
        room.add_player(user.player)
        user.playing_room = room_id

    def get_room(self, room_id):
        if room_id < 0 or room_id >= len(self.rooms):
            raise RoomNotExists()
        return self.rooms[room_id]

    def delete_room(self, room_id):
        if room_id < 0 or room_id >= len(self.rooms):
            raise RoomNotExists()
        self.rooms[room_id] = None
