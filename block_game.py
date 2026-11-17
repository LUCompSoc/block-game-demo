import argparse
import math
import socket
import time
import struct

import pyray as rl

### NETWORKING

IP = "127.0.0.1"  # localhost
PORT = 5005  # default port but feel free to change
DESTINATION_PORTS = []  # all ports that send data to
DELAY = 0  # in milliseconds
COLOUR = 0 # use --colour to assign this, can 0 for red, 1 for blue, 2 for yellow and 3 for green

### GAME 
TILES_X = 16
TILES_Y = 16
TILE_SCALE = 32

PLAYER_SIZE = rl.Vector2(1, 1)

AIR = 0
STONE = 1
DIRT = 2
GRASS = 3

TILE_COUNT = 3
TILE_NAMES = ["Stone", "Dirt", "Grass"]
BACK_COLOUR = rl.Color(0, 255, 255, 255)
PLAYER_COLOUR = rl.Color(255, 0, 0, 255)
GRAVITY = 0.006
TERMINAL_VELOCITY = 0.2
WALK_SPEED = 0.1
JUMP_VEL = math.sqrt(2 * GRAVITY * 4)


def send_state(state):
    for pos, block in state.updated_tiles.items():
        x = pos[0]
        y = pos[1]
        pass


def receive_state(state):
    for data in receive_data():
       pass 

# Turn a variables into a single bytestream
def pack_data() -> bytes:
    return struct.pack()


# Turn bytes into a list of variables
def unpack_data(data: bytes) -> tuple:
    return struct.unpack()


# Sends a bytestream to all of the specified destination ports
def send_data(data: bytes) -> None:
    sock = SOCK
    if not hasattr(send_data, "buffer"):
        send_data.buffer = []
    global DESTINATION_PORTS
    current_time = time.monotonic()
    send_data.buffer.append((data, current_time))

    remaining = []

    for packet_data, timestamp in send_data.buffer:
        if current_time - timestamp >= DELAY / 1000:
            for port in DESTINATION_PORTS:
                sock.sendto(packet_data, (IP, port))
                print("sent message")
        else:
            remaining.append((packet_data, timestamp))
    send_data.buffer = remaining


# Returns a list of bytes, may be empty, each item is its own transmission
def receive_data() -> list:
    sock = SOCK
    return_data = []
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            return_data.append(data)
        except BlockingIOError:
            break
    return return_data


class Player:
    def __init__(self, colour: int):
        self.player_pos = rl.Vector2(0, 0)
        self.player_vel = rl.Vector2(0, 0)
        self.player_grounded = False
        self.colour = colour


class GameState:
    def __init__(self):
        self.spritesheet = None
        self.grid = [0 for _ in range(TILES_X * TILES_Y)]
        self.player = Player(COLOUR)
        self.other_players = []
        self.other_players.append(Player(1))
        self.updated_tiles: dict[tuple[int, int], int] = {}
        self.selected_tile = 1


def get_tile(state: GameState, x, y: int) -> int:
    return state.grid[y * TILES_X + x]


def set_tile(state: GameState, x, y: int, tile: int):
    state.grid[y * TILES_X + x] = tile


def init_game_state(state: GameState):
    state.spritesheet = rl.load_texture("sprites.png")
    for y in range(8, 16):
        for x in range(0, 16):
            set_tile(state, x, y, STONE)
    


def update_state(state: GameState):
    if rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_LEFT):
        m = rl.get_mouse_position()
        x = int(m.x / TILE_SCALE)
        y = int(m.y / TILE_SCALE)
        set_tile(state, x, y, state.selected_tile)
        state.updated_tiles[(x, y)] = state.selected_tile
    elif rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_RIGHT):
        m = rl.get_mouse_position()
        x = int(m.x / TILE_SCALE)
        y = int(m.y / TILE_SCALE)
        set_tile(state, x, y, AIR)
        state.updated_tiles[(x, y)] = AIR

    scroll_delta = rl.get_mouse_wheel_move()

    if scroll_delta > 0:
        state.selected_tile = min(state.selected_tile + 1, TILE_COUNT)
    elif scroll_delta < 0:
        state.selected_tile = max(state.selected_tile - 1, 1)

    player_move_and_collide(state)


def player_move_and_collide(state: GameState):
    state.player.player_vel.y += GRAVITY
    state.player.player_vel.y = min(state.player.player_vel.y, TERMINAL_VELOCITY)

    if state.player.player_grounded and (rl.is_key_pressed(rl.KeyboardKey.KEY_Z) or rl.is_key_pressed(rl.KeyboardKey.KEY_W)):
        state.player.player_vel.y = -JUMP_VEL

    state.player.player_grounded = False

    state.player.player_pos.y += state.player.player_vel.y

    if is_player_intersecting_ground_tiles(state):
        if state.player.player_vel.y >= 0:
            state.player.player_pos.y = math.floor(state.player.player_pos.y + PLAYER_SIZE.y / 2) - PLAYER_SIZE.y / 2
            state.player.player_grounded = True
        else:
            state.player.player_pos.y = math.ceil(state.player.player_pos.y - PLAYER_SIZE.y / 2) + PLAYER_SIZE.y / 2

        state.player.player_vel.y = 0

    dx = 0
    if rl.is_key_down(rl.KeyboardKey.KEY_RIGHT) or rl.is_key_down(rl.KeyboardKey.KEY_D):
        dx += 1
    elif rl.is_key_down(rl.KeyboardKey.KEY_LEFT) or rl.is_key_down(rl.KeyboardKey.KEY_A):
        dx -= 1

    state.player.player_vel.x = dx * WALK_SPEED

    state.player.player_pos.x += state.player.player_vel.x

    if is_player_intersecting_ground_tiles(state):
        if state.player.player_vel.x >= 0:
            state.player.player_pos.x = math.floor(state.player.player_pos.x + PLAYER_SIZE.y / 2) - PLAYER_SIZE.x / 2
        else:
            state.player.player_pos.x = math.ceil(state.player.player_pos.x - PLAYER_SIZE.y / 2) + PLAYER_SIZE.x / 2

        state.player.player_vel.x = 0

def is_player_intersecting_ground_tiles(state: GameState) -> bool:
    min_y = max(int(state.player.player_pos.y - 0.5), 0)
    max_y = min(int(math.ceil(state.player.player_pos.y + 0.5)), TILES_Y)

    min_x = max(int(state.player.player_pos.x - 0.5), 0)
    max_x = min(int(math.ceil(state.player.player_pos.x + 0.5)), TILES_X)

    for y in range(min_y, max_y):
        for x in range(min_x, max_x):
            tile = get_tile(state, x, y)

            if tile != 0:
                return True

    return False


def draw_state(state: GameState):
    # Draw tiles
    for y in range(0, 16):
        for x in range(0, 16):
            tile = get_tile(state, x, y)

            if tile == 0:
                continue

            #c = TILE_COLOURS[tile - 1]
            tile += 3

            rl.draw_texture_pro(state.spritesheet, 
                                rl.Rectangle(tile * 16, 0, 16, 16), 
                                rl.Rectangle(x * TILE_SCALE, y * TILE_SCALE, TILE_SCALE, TILE_SCALE),
                                rl.Vector2(0, 0),
                                0,
                                rl.WHITE)

            #rl.draw_rectangle(x * TILE_SCALE, y * TILE_SCALE, TILE_SCALE, TILE_SCALE, c)

    # Draw player
    #draw_rectangle_from_centre(state.player_pos.x * TILE_SCALE, state.player_pos.y * TILE_SCALE, TILE_SCALE, TILE_SCALE, PLAYER_COLOUR)
    draw_sprite_from_centre(state.spritesheet, 8*state.player.colour, state.player.player_pos.x * TILE_SCALE, state.player.player_pos.y * TILE_SCALE, TILE_SCALE, TILE_SCALE, rl.WHITE, state.player.player_pos.x * 50)

    m = rl.get_mouse_position()
    rl.draw_line(int(state.player.player_pos.x * TILE_SCALE), int(state.player.player_pos.y * TILE_SCALE), int(m.x), int(m.y), rl.Color(0, 0, 0, 255))
    rl.draw_line(int(m.x - 5), int(m.y), int(m.x + 5), int(m.y), rl.Color(0, 0, 0, 255))
    rl.draw_line(int(m.x), int(m.y - 5), int(m.x), int(m.y + 5), rl.Color(0, 0, 0, 255))
    
    for player in state.other_players:
        draw_sprite_from_centre(state.spritesheet, 8*player.colour, player.player_pos.x * TILE_SCALE, player.player_pos.y * TILE_SCALE, TILE_SCALE, TILE_SCALE, rl.WHITE, player.player_pos.x * 50)

def draw_rectangle_from_centre(cx: float, cy: float, w: float, h: float, c: rl.Color):
    rl.draw_rectangle(int(cx - w/2), int(cy - h/2), int(w), int(h), c)


def draw_sprite_from_centre(tex: rl.Texture, sprite_id: int, cx: float, cy: float, w: float, h: float, c: rl.Color, rot: float):
    rl.draw_texture_pro(tex,
                        rl.Rectangle(sprite_id * 16, 0, 16, 16),
                        rl.Rectangle(cx, cy, w, h),
                        rl.Vector2(w/2, h/2),
                        rot,
                        rl.WHITE)



def main():
    global PORT
    global DESTINATION_PORTS
    global SOCK
    global COLOUR
    parser = argparse.ArgumentParser(description="networking demo")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--connect", type=int, action="append",
                        help="add a game instance by providing the port number (can be used multiple times)")
    parser.add_argument("--colour", type=int, default=0)
    args = parser.parse_args()
    PORT = args.port
    DESTINATION_PORTS = args.connect
    COLOUR = args.colour
    SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SOCK.bind((IP, PORT))
    SOCK.setblocking(False)

    state = GameState()

    rl.init_window(TILES_X * TILE_SCALE, TILES_Y * TILE_SCALE, "Game")
    rl.set_target_fps(60)

    init_game_state(state)

    while not rl.window_should_close():
        update_state(state)
        send_state(state)
        state.updated_tiles = {}
        receive_state(state)

        rl.begin_drawing()
        rl.clear_background(BACK_COLOUR)

        draw_state(state)

        rl.draw_text("Selected Tile: " + TILE_NAMES[state.selected_tile - 1], 20, 20, 16, rl.WHITE)

        rl.end_drawing()



if __name__ == "__main__":
    main()
