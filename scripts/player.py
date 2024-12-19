import random
import pygame
import os
from scripts.settings import WIDTH
from scripts.game_items.rpg.rpg import Rpg
from scripts.game_items.default_guns.default_guns import *
from scripts.game_items.hook import Hook

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class Player:
    def __init__(self, game, pos, size):
        # Player basic attributes
        self.game = game
        self.name = ''
        self.pos = list(pos)
        self.size = size
        self.mouse_pos = [0, 0]
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.no_jump_limits = False
        self.gravity = 0.03
        self.jumps = 0
        self.direction = 'right'

        # Player health
        self.max_hp = 100
        self.hp = self.max_hp

        # Weapons and hook
        self.setup_weapons()
        self.hook = Hook(self.game, self)
        self.bullets = []
        self.other_bullets = []

        # Player status
        self.immortality_time = 120
        self.is_immortal = False
        self.is_hiding = False
        self.is_e_active = False
        self.id = random.randint(1, 10000)
        self.max_velocity = 2

    def setup_weapons(self):
        """Initialize weapon objects and set current weapon."""
        self.rpg = Rpg(self.game, self)
        self.minigun = Minigun(self.game, self)
        self.deagle = DesertEagle(self.game, self)
        self.awp = AWP(self.game, self)
        self.shotgun = Shotgun(self.game, self)
        self.weapons = [self.rpg, self.minigun, self.deagle, self.awp, self.shotgun]
        self.current_weapon = self.weapons[0]

    def update(self, blockmap, movement=(0, 0)):
        self.handle_hiding(blockmap)
        self.update_immortality()
        self.update_mouse_position()
        self.update_bullets(blockmap)
        self.hook.update(self.game.blockmap)
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.update_movement(movement)
        self.apply_gravity()
        self.update_direction()

    def handle_hiding(self, blockmap):
        """Check if the player is hiding."""
        self.is_hiding = False
        entity_rect = self.rect()
        for rect in blockmap.hiding_blocks_positions:
            if entity_rect.colliderect(rect):
                self.is_hiding = True

    def update_immortality(self):
        """Decrease immortality cooldown timer."""
        if self.immortality_time > 0:
            self.immortality_time -= 1

    def update_mouse_position(self):
        """Track the current mouse position."""
        self.mouse_pos = pygame.mouse.get_pos()

    def update_bullets(self, blockmap):
        """Update bullets and remove None references."""
        self.bullets = [bullet for bullet in self.bullets if bullet and bullet.is_exist]
        self.other_bullets = [bullet for bullet in self.other_bullets if bullet and bullet.is_exist]

        self.current_weapon.update(self.game.blockmap, self.game.render_scroll)
        for bullet in self.bullets + self.other_bullets:
            bullet.update(blockmap, self.game.render_scroll)

    def update_movement(self, movement):
        """Update player position based on movement and handle collisions."""
        # Horizontal movement
        self.update_horizontal_movement(movement)
        self.check_horizontal_collisions()

        # Vertical movement
        self.update_vertical_movement()
        self.check_vertical_collisions()

    def update_horizontal_movement(self, movement):
        """Apply horizontal movement input."""
        if movement[0] < 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, -self.max_velocity)
        elif movement[0] > 0:
            self.velocity[0] = min(self.velocity[0] + 0.1, self.max_velocity)

    def check_horizontal_collisions(self):
        """Handle collisions with blocks horizontally."""
        self.pos[0] += self.velocity[0]
        entity_rect = self.rect()
        for rect in self.game.blockmap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                elif self.velocity[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

    def update_vertical_movement(self):
        """Update vertical position."""
        self.pos[1] += self.velocity[1]

    def check_vertical_collisions(self):
        """Handle collisions with blocks vertically."""
        entity_rect = self.rect()
        for rect in self.game.blockmap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                    self.jumps = 2
                elif self.velocity[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        self.handle_ground_friction()

    def handle_ground_friction(self):
        """Apply friction on the ground."""
        if self.collisions['down']:
            if abs(self.velocity[0]) < 0.2:
                self.velocity[0] = 0
            elif self.velocity[0] > 0:
                self.velocity[0] -= 0.2
            else:
                self.velocity[0] += 0.2
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

    def apply_gravity(self):
        """Apply gravity to vertical velocity."""
        self.velocity[1] = min(5, self.velocity[1] + self.gravity)

    def update_direction(self):
        """Set player direction based on mouse position."""
        self.direction = 'right' if pygame.mouse.get_pos()[0] > WIDTH // 2 else 'left'

    def rect(self):
        """Return player bounding box."""
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def render(self, surface, offset=(0, 0)):
        if self.hp < 1:
            return

        self.render_character(surface, offset)
        self.render_bullets(surface, offset)
        self.render_health_and_name(surface, offset)

    def render_character(self, surface, offset):
        """Render the player and their current weapon."""
        if not self.is_hiding:
            image = self.game.assets['player']
            if self.direction == 'right':
                image = pygame.transform.flip(image, True, False)
            surface.blit(image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))
            self.current_weapon.render(self.game.display, self.mouse_pos, self.game.render_scroll)

        self.hook.render(self.game.display, self.game.render_scroll)

    def render_bullets(self, surface, offset):
        """Render all bullets."""
        for bullet in self.bullets + self.other_bullets:
            bullet.render(surface, offset)

    def render_health_and_name(self, surface, offset):
        """Render health bar and player name."""
        if not self.is_hiding:
            self.render_health_bar(surface, offset)
            self.render_name(surface, offset)

    def render_health_bar(self, surface, offset):
        """Render the player's health bar."""
        bar_width, bar_height = 20, 5
        health_ratio = self.hp / self.max_hp
        health_bar_width = int(bar_width * health_ratio)

        health_bar_rect = pygame.Rect(
            self.pos[0] - offset[0] - (bar_width - self.size[0]) / 2,
            self.pos[1] - offset[1] - 10 + 3, bar_width, bar_height
        )
        current_health_rect = pygame.Rect(
            self.pos[0] - offset[0] - (bar_width - self.size[0]) / 2,
            self.pos[1] - offset[1] - 10 + 3, health_bar_width, bar_height
        )

        pygame.draw.rect(surface, (255, 0, 0), health_bar_rect)
        pygame.draw.rect(surface, (0, 255, 0), current_health_rect)

    def render_name(self, surface, offset):
        """Render the player's name."""
        render_name = pygame.font.Font(None, 16).render(self.name, True, (0, 0, 0))
        text_rect = render_name.get_rect(
            center=(self.pos[0] + 5 - offset[0], self.pos[1] - 15 - offset[1])
        )
        surface.blit(render_name, text_rect)

    def jump(self):
        """Handle player's jump."""
        if self.jumps:
            self.velocity[1] = -2
            if not self.no_jump_limits:
                self.jumps -= 1

    def take_damage(self, amount):
        """Reduce player's health by the given amount."""
        if self.immortality_time > 0 or self.is_immortal:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def switch_weapon(self, direction):
        """Switch to another weapon in the given direction."""
        current_index = self.weapons.index(self.current_weapon)
        new_index = (current_index + direction) % len(self.weapons)
        self.current_weapon = self.weapons[new_index]

    def die(self):
        """Handle player's death and respawn."""
        spawn_point = random.choice(self.game.blockmap.spawnpoint_positions)
        self.pos = [spawn_point[0] * 16, spawn_point[1] * 16]
        self.hp = self.max_hp
        self.velocity = [0, 0]
        self.immortality_time = 120
        # Запрашиваем актуальное состояние карты
        self.game.client.send_data({'request_map': True})