"""
Teeworlds Game Client

This module implements the main game client, handling rendering, player movement,
networking, and game state management.
"""

import pygame
import sys, os
import json
import threading
import math
import random
from typing import Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_menu.input.input_box import InputBox
from scripts.settings import *
from scripts.game_items.potions.random_potion import RandomPotion
from scripts.infrustructure import load_sprite
from scripts.player import Player
from scripts.blocks.blockmap import Blockmap
from scripts.game_items.rpg import bullet as rpg_bullet
from scripts.game_items.default_guns import default_bullet
from main_menu.menu import MainMenu
from scripts.cheat_codes import cheat_cods
from scripts.game_items.potions.heal_potion import HealPotion
from scripts.game_items.door import Door
from scripts import settings
from client import Client

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class Game:
    """Main game class handling game initialization, rendering, and game loop."""

    # inizialization opened -----------------------------------------------------------------

    def __init__(self):
        """Initialize the game, setup display, load assets, and establish network connection."""
        self.running = True
        self._init_pygame()
        self._load_assets()
        self._setup_network()
        self._init_menu_assets()
        self._init_game_state()
        self._init_game_map()

    def _init_pygame(self) -> None:
        """Initialize Pygame and setup display."""
        pygame.init()
        pygame.display.set_caption('Teeworlds Game')
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.display = pygame.Surface((WIDTH / 2, HEIGHT / 2))
        self.clock = pygame.time.Clock()

    def load_assets_paths(self, directory):
        block_paths = {}
        for filename in os.listdir(BASE_DIR + '\\assets\\sprites\\' + directory):
            if filename.endswith('.png'):
                file_way = os.path.join(BASE_DIR + '\\assets\\sprites\\' + directory + '\\' + filename)
                name_without_extension = filename.rsplit('.', 1)[0]
                block_paths[name_without_extension] = file_way
        return block_paths

    def _load_assets(self) -> None:
        """Load and store all game assets."""
        paths = self.load_assets_paths('blocks')
        paths['player'] = BASE_DIR + '\\assets\\sprites\\player.png'
        self.assets: {str, pygame.Surface} = {name: load_sprite(path) for name, path in paths.items()}

    def _init_menu_assets(self) -> None:
        """Load menu-specific assets before initializing game state."""
        for i in range(1, 5):
            asset_name = f'menu_bg_{i}'
            self.assets[asset_name] = pygame.transform.scale(
                pygame.image.load(BASE_DIR + f"\\assets\\default\\background\\{i}.png"),
                (WIDTH, HEIGHT)
            )

    def _init_game_state(self) -> None:
        """Initialize game state variables."""
        self.movement = [False, False]
        self.scroll = [0, 0]
        self.render_scroll = (0, 0)
        self.camera_speed = 30

    def _setup_network(self) -> None:
        """Setup network connection to game server."""
        self.client = Client(host=settings.HOST, port=settings.PORT)
        self.client.setup_network()

    def _init_game_map(self, exit=False) -> None:
        """Initialize game map and blockmap."""
        if not exit:
            received_map = self.client.get_map()
        else:
            received_map = None
        self.blockmap = Blockmap(self)

        if received_map is None:
            name, self.map = MainMenu(self.screen, True, self).main_menu()
            with open(BASE_DIR + f'\\maps\\{self.map}.json', 'r', encoding='utf-8') as file:
                self.blockmap.blockmap = json.load(file)
            # Добавляем разделитель в конец сообщения
            map_data = {'map': self.blockmap.blockmap}
            self.client.send_data(map_data)
        else:
            name, _ = MainMenu(self.screen, False, self).main_menu()
            self.blockmap.blockmap = received_map

        self._initialize_blockmap()
        self._setup_networking()
        self._initialize_player(name)

        self._initialize_ui_elements()
        self._initialize_game_objects()

    def _initialize_blockmap(self) -> None:
        """Find positions of various elements in the blockmap."""
        self.blockmap.find_spawnpoints()
        self.blockmap.find_heal_positions()
        self.blockmap.find_random_potion_positions()
        self.blockmap.find_hiding_blocks_positions()
        self.blockmap.find_door_positions()

    def _setup_networking(self) -> None:
        """Setup networking components."""
        self.player_info = {}
        self.players_data = {}
        self.players = {}
        self.receive_thread = threading.Thread(target=self.client.receive_data, args=(self._process_incoming_data,))
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def _initialize_player(self, name) -> None:
        """Initialize player."""
        spawnpoint_pos = random.choice(self.blockmap.spawnpoint_positions)
        start_pos = [spawnpoint_pos[0] * 16, spawnpoint_pos[1] * 16]
        self.player = Player(self, start_pos, (10, 16))
        self.player.name = name

    def _initialize_ui_elements(self) -> None:
        """Initialize user interface elements."""
        self.is_cheat_menu_active = False
        self.input_box = InputBox(
            5, 5, 300, 48, self.screen,
            active_color=pygame.Color('black'),
            inactive_color=pygame.Color('darkslategrey')
        )
        self.text_surface = pygame.font.Font(BASE_DIR + '\\fonts\\JapanBentoDemoVersionRegular-nRWAJ.otf', 48).render(
            "ERROR WITH CODE", True, (0, 0, 0)
        )
        self.text_rect = self.text_surface.get_rect(center=(WIDTH / 2, 100))
        self.is_warning_active = False

    def _initialize_game_objects(self) -> None:
        """Initialize game objects like potions and doors."""
        self.heals = [HealPotion([pos[0] * 16, pos[1] * 16], self)
                      for pos in self.blockmap.heal_positions]
        self.random_potions = [RandomPotion([pos[0] * 16, pos[1] * 16], self)
                               for pos in self.blockmap.random_potion_positions]
        self.doors = [Door([pos[0] * 16, pos[1] * 16], self)
                      for pos in self.blockmap.door_positions]
        self.main_background = [
            pygame.transform.scale(
                pygame.image.load(BASE_DIR + f"\\assets\\default\\background\\{i + 1}.png"),
                (WIDTH // 2, HEIGHT // 2)
            ) for i in range(4)
        ]

    # inizialization closed -----------------------------------------------------------------

    def _handle_rendering(self) -> None:
        """Handle all rendering operations."""
        # Clear screen and render background
        self.screen.fill((0, 0, 0))
        for bg in self.main_background:
            self.display.blit(bg, (0, 0))

        self._update_camera()

        self._render_game_elements()

    def _update_camera(self) -> None:
        """Update camera position to follow player."""
        target_x = self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]
        target_y = self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]
        self.scroll = [
            self.scroll[0] + target_x,
            self.scroll[1] + target_y
        ]
        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

    def _render_game_elements(self) -> None:
        """Render all game elements in the correct order."""
        self._clear_display_surface()
        self._render_static_elements()
        self._render_dynamic_elements()
        self._render_overlay_elements()
        self._scale_and_display()

    def _clear_display_surface(self) -> None:
        """Clear the display surface with a sky blue background."""
        self.display.fill((148, 200, 255))

    def _render_static_elements(self) -> None:
        """Render static elements such as map and player."""
        self.blockmap.render(self.display, False, self.render_scroll)
        self.player.update(self.blockmap, ((self.movement[1] - self.movement[0]) * 2, 0))
        self.player.render(self.display, self.render_scroll)

    def _render_dynamic_elements(self) -> None:
        """Render dynamic elements like collectibles and interactive objects."""
        for game_element in [*self.heals, *self.random_potions, *self.doors]:
            game_element.update()
            game_element.render(self.display, self.render_scroll)

    def _render_overlay_elements(self) -> None:
        """Render overlay elements on top of other elements."""
        self.blockmap.render_hiding_block(self.display, self.render_scroll)
        self.render_players(self.render_scroll)

    def _scale_and_display(self) -> None:
        """Scale the display surface to the screen size and blit it."""
        scaled_surface = pygame.transform.scale(self.display, (WIDTH, HEIGHT))
        self.screen.blit(scaled_surface, (0, 0))

    def _process_events(self) -> None:
        """Process all game events including input handling."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._handle_quit()

            if self.is_cheat_menu_active:
                self._handle_cheat_menu_input(event)
            else:
                self._handle_gameplay_input(event)

            self.input_box.handle_event(event)

    def _handle_quit(self) -> None:
        """Clean up and quit the game."""
        pygame.quit()
        sys.exit()

    def _handle_gameplay_input(self, event: pygame.event.Event) -> None:
        """Handle input events during normal gameplay."""
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)
        elif event.type == pygame.KEYUP:
            self._handle_keyup(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._handle_mouse_up(event)
        elif event.type == pygame.MOUSEWHEEL:
            self._handle_mouse_wheel(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle keyboard key press events."""
        if event.key == 96:  # Tilde key
            self.is_cheat_menu_active = True
            self.input_box.text = ""
        elif event.key == pygame.K_e:
            self.player.is_e_active = True
        elif event.key == pygame.K_a:
            self.movement[0] = True
        elif event.key == pygame.K_d:
            self.movement[1] = True
        elif event.key == pygame.K_SPACE:
            self.player.jump()

    def _handle_keyup(self, event: pygame.event.Event) -> None:
        """Handle keyboard key release events."""
        if event.key == pygame.K_a:
            self.movement[0] = False
            self.player.velocity[0] = 0
        elif event.key == pygame.K_e:
            self.player.is_e_active = False
        elif event.key == pygame.K_d:
            self.movement[1] = False
            self.player.velocity[0] = 0

    def _handle_mouse_down(self, event: pygame.event.Event) -> None:
        """Handle mouse button press events."""
        mouse_pos = pygame.mouse.get_pos()
        world_mouse_pos = (mouse_pos[0], mouse_pos[1])
        direction = self._calculate_direction(world_mouse_pos)

        if event.button == 3:  # Right click
            self.player.hook.shoot(direction)
        elif event.button == 1:  # Left click
            self.player.current_weapon.shoot(direction)
            self.player.current_weapon.is_shooting = True

    def _handle_mouse_up(self, event: pygame.event.Event) -> None:
        """Handle mouse button release events."""
        if event.button == 1:  # Left click release
            self.player.current_weapon.is_shooting = False

    def _handle_mouse_wheel(self, event: pygame.event.Event) -> None:
        """Handle mouse wheel events for weapon switching."""
        if event.y > 0:
            self.player.switch_weapon(1)
        elif event.y < 0:
            self.player.switch_weapon(-1)

    def _calculate_direction(self, world_mouse_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate normalized direction vector from player to mouse position."""
        direction = (world_mouse_pos[0] - WIDTH / 2, world_mouse_pos[1] - HEIGHT / 2)
        length = math.sqrt(direction[0] * direction[0] + direction[1] * direction[1])
        return (direction[0] / length, direction[1] / length)

    def _handle_cheat_menu_input(self, event: pygame.event.Event) -> None:
        """Handle input events when cheat menu is active."""
        if event.type == pygame.KEYDOWN:
            if event.key == 96:  # Tilde key
                self._close_cheat_menu()
            elif event.key == pygame.K_RETURN or self.input_box.is_enter_pressed:
                self._handle_cheat_code()

    def _close_cheat_menu(self) -> None:
        """Close the cheat menu and reset its state."""
        self.is_cheat_menu_active = False
        self.is_warning_active = False
        self.input_box.text = ''

    def _handle_cheat_code(self) -> None:
        """Process entered cheat code."""
        input_text = self.input_box.text
        if input_text not in cheat_cods:
            self.is_warning_active = True
        else:
            self._apply_cheat_code(cheat_cods[input_text])

        self.input_box.is_enter_pressed = False
        self.input_box.text = ""

    def _apply_cheat_code(self, code: str) -> None:
        """Apply the effect of a cheat code."""
        self.is_cheat_menu_active = False
        self.is_warning_active = False

        if code == "immortality":
            self.player.is_immortal = True
        elif code == "full_hp":
            self.player.hp = 100
        elif code == "damage_up":
            self.player.current_weapon.damage *= 2
        elif code == "no_jump_limits":
            self.player.no_jump_limits = True
        elif code == "no_recoil":
            self.player.current_weapon.shooting_timeout = 0.01
        elif code == "no_knockback":
            self.player.current_weapon.push_power = 0  # 0 is important (in rpg_bullet)

    def _update_game_state(self) -> None:
        """Update game state and network synchronization."""
        self.input_box.update()
        self.send_player_info()

    def _update_display(self) -> None:
        """Update the game display with the current frame."""
        if self.is_cheat_menu_active:
            self.input_box.draw()
        if self.is_warning_active:
            self.screen.blit(self.text_surface, self.text_rect)

        pygame.display.update()

    def send_player_info(self):
        self._update_player_info()
        self.client.send_data(self.player_info)

    def _update_player_info(self):
        """Updates the player_info dictionary with the current player state."""
        player, hook = self.player, self.player.hook
        self.player_info.update({
            'x': player.pos[0],
            'y': player.pos[1],
            'is_rope_torn': hook.is_rope_torn,
            'hook_x': hook.pos[0],
            'hook_y': hook.pos[1],
            'direction': player.direction,
            'mouse_pos': player.mouse_pos,
            'weapon_index': player.weapons.index(player.current_weapon),
            'bullets': [bullet.serialize() for bullet in player.bullets],
            'hp': player.hp,
            'nickname': player.name,
            'id': player.id,
            'is_e_active': player.is_e_active,
            'is_hiding': player.is_hiding
        })

    def _process_incoming_data(self, data):
        """Processes the incoming data from the client."""
        self._update_players_data(data)
        self._remove_disconnected_players()
        self._update_or_add_players()

    def _update_players_data(self, data):
        """Updates the players_data dictionary with deserialized data."""
        self.players_data = json.loads(data)
        self.players_data.pop(self.client.address, None)

    def _remove_disconnected_players(self):
        """Removes players from the internal state that are no longer connected."""
        current_addresses = set(self.players_data.keys())
        for addr in list(self.players.keys()):  # Create a list to avoid RuntimeError
            if addr not in current_addresses:
                self.players.pop(addr)

    def _update_or_add_players(self):
        """Adds new players and updates existing ones with the latest data."""
        # Проверяем, что player уже инициализирован
        if not hasattr(self, 'player'):
            return

        self.player.other_bullets = []

        for addr, player_info in self.players_data.items():
            player = self.players.get(addr)
            if not player:
                player = Player(self, (player_info['x'], player_info['y']), (10, 16))
                self.players[addr] = player
            self._update_player(player, player_info)

            self.player.other_bullets.extend(player.bullets)

    def _update_player(self, player, player_info):
        """Updates a single player's attributes."""
        player.pos = (player_info['x'], player_info['y'])
        player.direction = player_info['direction']
        player.hook.is_rope_torn = player_info['is_rope_torn']
        player.hook.pos = (player_info['hook_x'], player_info['hook_y'])
        player.mouse_pos = player_info['mouse_pos']
        player.current_weapon = player.weapons[player_info['weapon_index']]
        player.bullets = [self.deserialize_bullet(bullet) for bullet in player_info['bullets']]
        player.hp = player_info['hp']
        player.name = player_info['nickname']
        player.id = player_info['id']
        player.is_e_active = player_info['is_e_active']
        player.is_hiding = player_info['is_hiding']

    def deserialize_bullet(self, bullet_info):
        pos = bullet_info['pos']
        direction = bullet_info['direction']
        damage = bullet_info['damage']
        if bullet_info['bullet_type'] == 'rpg':
            is_bullet_flipped = bullet_info['is_bullet_flipped']
            angle = bullet_info['angle']
            bullet = rpg_bullet.Bullet(self, pos, direction, is_bullet_flipped, angle, damage)
            bullet.is_damaged = bullet_info['is_damaged']
            bullet.exploded = bullet_info['is_exploded']
            bullet.damaged_players = bullet_info['damaged_players']
            return bullet
        elif bullet_info['bullet_type'] == 'minigun_bullet':
            return self.handle_default_gun('minigun', pos, direction, damage, bullet_info)
        elif bullet_info['bullet_type'] == 'shotgun_bullet':
            return self.handle_default_gun('shotgun', pos, direction, damage, bullet_info)
        elif bullet_info['bullet_type'] == 'awp_bullet':
            return self.handle_default_gun('awp', pos, direction, damage, bullet_info)
        elif bullet_info['bullet_type'] == 'deagle_bullet':
            return self.handle_default_gun('deagle', pos, direction, damage, bullet_info)

    def handle_default_gun(self, name, pos, direction, damage, bullet_info):
        bullet = default_bullet.Bullet(self, pos, direction, damage, self.get_bullets_image(name))
        bullet.is_exist = bullet_info['is_exist']
        bullet.damaged_player = bullet_info['damaged_player']
        bullet.is_damaged = bullet_info['is_damaged']
        bullet.shooter_id = bullet_info.get('shooter_id', -1)  # Получаем ID стрелка, по умолчанию -1
        return bullet

    def get_bullets_image(self, name):
        s = {
            'awp': '\\tools\\awp\\awp_bullet.png',
            'shotgun': '\\tools\\shotgun\\shotgun_bullet.png',
            'minigun': '\\tools\\minigun\\minigun_bullet.png',
            'deagle': '\\tools\\desert_eagle\\deagle_bullet.png',
        }
        return s[name]

    def render_players(self, render_scroll):
        for player in self.players.values():
            player.render(self.display, render_scroll)

    def close(self):
        self.client.send_data({"disconnect": True})
        pygame.quit()
        sys.exit()

    def run(self):
        """Main game loop handling rendering, input, and game state updates."""
        while self.running:
            self._handle_rendering()
            self._update_game_state()
            self._process_events()
            self._update_display()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
