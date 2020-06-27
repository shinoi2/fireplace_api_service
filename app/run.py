from flask import Flask, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from logger import INFO, WARN, ERROR, DEBUG
from user import User, UserManager, DeckNameDuplicate, DeckNotExists
from error_code import ErrorCode
from handler import success, failed
from config import url_config, app_config, game_language
from room import RoomManager, RoomFull, RoomNotExists
from cards_map import cards_name_map


app = Flask(__name__)
app.secret_key = app_config['secret_key']
app.config['JSON_AS_ASCII'] = False

login_manager = LoginManager()
user_manager = UserManager()
room_manager = RoomManager()

login_manager.init_app(app)


@login_manager.user_loader
def user_loader(username):
    if username not in user_manager.users:
        return
    return user_manager.users[username]


@login_manager.request_loader
def request_loader(request):
    data = request.json
    if not data:
        return
    username = data['username']
    password = data['password']
    if username not in user_manager.users:
        return

    user = user_manager.users[username]
    user.is_authenticated = user_manager.users[username].authenticate(password)

    return user


@app.route('/api/login_in', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    if username not in user_manager.users:
        return failed(rtn=ErrorCode.USER_NOT_EXISTS, message="User %s does not exist" % (username))

    if user_manager.users[username].authenticate(password):
        user = user_manager.users[username]
        login_user(user)
        return redirect(url_for('protected'))

    return failed(rtn=ErrorCode.WRONG_USERNAME_OR_PASSWORD, message='Wrong username or password')


@app.route('/api/sign_up', methods=['PUT'])
def sign_up():
    data = request.json
    username = data['username']
    password = data['password']
    DEBUG("username is %s, password is %s" % (username, password))
    DEBUG("users is %s" % user_manager.users)
    if username not in user_manager.users:
        user_manager.save_user(User(username, password))
        return success(message="User %s sign up success" % username)

    return failed(rtn=ErrorCode.USER_ALREADY_EXISTS, message="User %s already exists" % (username))


@app.route('/api/user')
@login_required
def protected():
    return success(message='Logged in as: ' + current_user.id)


@app.route('/api/logout', methods=['POST'])
def logout():
    logout_user()
    return success(message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return failed(rtn=ErrorCode.UNAUTHORIZED, message='Unauthorized')


@app.route("/api/deck", methods=['PUT'])
def add_deck():
    data = request.json
    try:
        current_user.add_deck(data["name"], data["code"])
        current_user.choose_deck(data["name"])
        user_manager.save_user(current_user)
    except DeckNameDuplicate:
        return failed(rtn=ErrorCode.DECK_NAME_DUPLICATE, message="Deck name %s already exists")
    return success(data=current_user.deck_json)


@app.route("/api/deck", methods=['POST'])
def choose_deck():
    name = request.json["name"]
    try:
        current_user.choose_deck(name)
    except DeckNotExists:
        return failed("Deck %s not exists" % name)
    return success(data=current_user.deck_json)


@app.route("/api/deck", methods=['DELETE'])
def delete_deck():
    name = request.json["name"]
    try:
        current_user.delete_deck(name)
        user_manager.save_user(current_user)
    except DeckNotExists:
        return failed("Deck %s not exists" % name)
    return success(data=current_user.deck_json)


@app.route("/api/deck", methods=['GET'])
def get_deck():
    return success(data=current_user.deck_json)


@app.route("/api/room", methods=['PUT'])
def create_room():
    room = room_manager.create_room()
    return success(data={"room_id": room.id}, message="Create room success")


@app.route("/api/room/<int:room_id>", methods=["GET"])
def get_room(room_id):
    try:
        room = room_manager.get_room(room_id)
        DEBUG(room.players)
        return success(data={
            "players": [{
                "name": player.name,
                "hero": cards_name_map[player.starting_hero],
                "deck": [cards_name_map[card] for card in player.starting_deck]
            } for player in room.players]
        })
    except RoomNotExists:
        return failed(rtn=ErrorCode.ROOM_NOT_EXISTS, message="Room %s does not exist" % room_id)


@app.route("/api/room/<int:room_id>", methods=["POST"])
def join_room(room_id):
    try:
        if current_user.playing_room == -1:
            room_manager.join_room(room_id, current_user)
            return success(message="Join room %s success" % room_id)
        else:
            return failed(
                ErrorCode.PLAYER_ALREADLY_PLAYING,
                message="playing in room %s")
    except RoomNotExists:
        return failed(rtn=ErrorCode.ROOM_NOT_EXISTS, message="Room %s does not exist" % room_id)
    except RoomFull:
        return failed(rtn=ErrorCode.ROOM_FULL, message="Room %s is full")


@app.route("/api/room/<int:room_id>", methods=["DELETE"])
def leave_room(room_id):
    if current_user.playing_room == -1:
        return failed(rtn=ErrorCode.PLAYER_NOT_PLAYING, message="not in room")
    room = room_manager.get_room(current_user.playing_room)
    room.players.remove(current_user.player)
    if len(room.players) == 0:
        room_manager.delete_room(room_id)
    return success(message="Join room %s success" % room_id)


if __name__ == '__main__':
    app.run(host=url_config['host'], port=url_config['port'], debug=url_config['debug'])
