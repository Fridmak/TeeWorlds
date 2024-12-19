import math
import pygame, os
from scripts.infrustructure import load_sprite

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) + '\\assets\\sprites\\'

class Door:
    def __init__(self, pos, game):
        self.sprites = {
            'closed_door': load_sprite(BASE_DIR + '\\blocks\\closed_door.png'),
            'opened_door': load_sprite(BASE_DIR + '\\blocks\\opened_door.png'),
            'closed_gray_door': load_sprite(BASE_DIR + '\\blocks\\closed_gray_door.png'),
            'opened_gray_door': load_sprite(BASE_DIR + '\\blocks\\opened_gray_door.png')
        }
        self.pos = pos
        self.game = game
        self.center_coordinates = [pos[0] + 8, pos[1] + 16]
        self.can_be_closed = True
        self.door_kd = 60
        self.current_tick = 0
        
        # Инициализируем состояние из карты
        blockmap_key = self.get_blockmap_key()
        block_type = self.game.blockmap.blockmap[blockmap_key]['type']
        self.is_open = block_type in ['opened_door', 'opened_gray_door']

    def update(self):
        self.current_tick += 1
        self.can_be_closed = not any(
            player.rect().colliderect(self.rect()) for player in [self.game.player, *self.game.players.values()])

        if self.current_tick <= self.door_kd:
            return

        for player in [self.game.player, *self.game.players.values()]:
            if self.distance_to_player(player) < 30 and player.is_e_active:
                self.toggle_door()
                self.current_tick = 0
                break

    def toggle_door(self):
        blockmap_key = self.get_blockmap_key()
        if not self.is_open:
            self.open_door(blockmap_key)
        elif self.can_be_closed:
            self.close_door(blockmap_key)

    def open_door(self, blockmap_key):
        self.is_open = True
        current_type = self.game.blockmap.blockmap[blockmap_key]['type']
        if current_type == 'closed_door':
            self.game.blockmap.blockmap[blockmap_key]['type'] = 'opened_door'
        elif current_type == 'closed_gray_door':
            self.game.blockmap.blockmap[blockmap_key]['type'] = 'opened_gray_door'
        self._send_map()

    def close_door(self, blockmap_key):
        self.is_open = False
        current_type = self.game.blockmap.blockmap[blockmap_key]['type']
        if current_type == 'opened_door':
            self.game.blockmap.blockmap[blockmap_key]['type'] = 'closed_door'
        elif current_type == 'opened_gray_door':
            self.game.blockmap.blockmap[blockmap_key]['type'] = 'closed_gray_door'
        self._send_map()

    def _send_map(self):
        map_data = {'map': self.game.blockmap.blockmap}
        self.game.client.send_data(map_data)

    def get_blockmap_key(self):
        return f"{self.pos[0] // 16};{self.pos[1] // 16}"

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], *self.sprites['closed_door'].get_rect().size)

    def distance_to_player(self, player):
        return math.sqrt((self.pos[0] - player.pos[0]) ** 2 + (self.pos[1] - player.pos[1]) ** 2)

    def render(self, surface, offset=(0, 0)):
        blockmap_key = self.get_blockmap_key()
        door_type = self.game.blockmap.blockmap[blockmap_key]['type']
        image = self.sprites[door_type]
        surface.blit(image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))