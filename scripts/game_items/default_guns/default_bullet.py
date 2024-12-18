import random

import pygame
import math, os
from scripts.infrustructure import load_sprite

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'

class Bullet:
    def __init__(self, game, pos, direction, damage, image, max_range=200, speed=10, spread = 0, stability = 0):
        self.game = game
        self.direction = direction
        self.image = self._load_and_scale_sprite(BASE_DIR + image)
        self._rotate_bullet()
        self.name = self.get_name(image)
        self.start_pos = pos[:]
        self.pos = list(pos)
        self.range = random.uniform(max_range*(1-stability), max_range*(1+stability)) #stability is (0, 1)
        self.velocity = self._apply_spread(direction, speed, spread)
        self.size = (10, 10)
        self.is_exist = True
        self.damage = damage
        self.is_damaged = False
        self.damaged_player = -1
        self.shooter_id = game.player.id
        self.ticks, self.max_ticks_rotation = 0, 5

    @staticmethod
    def _load_and_scale_sprite(filepath):
        image = load_sprite(filepath)
        return pygame.transform.scale(image, (image.get_rect().width // 10, image.get_rect().height // 10))

    def _apply_spread(self, direction, speed, spread):
        spread_angle = random.uniform(-spread, spread)

        angle = math.atan2(direction[1], direction[0]) + math.radians(spread_angle)

        return [math.cos(angle) * speed, math.sin(angle) * speed]

    def update(self, tilemap, _, is_enemy=False):
        if not self.is_exist:
            return

        self._move_bullet()
        if self._has_exceeded_range():
            self.is_exist = False
            return

        self._check_collision_with_players()
        self._check_collision_with_walls(tilemap)


    def _move_bullet(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

    def _has_exceeded_range(self):
        length = math.dist(self.pos, self.start_pos)
        return length > self.range

    def _check_collision_with_players(self):
        bullet_rect = self.rect()

        for player in self.game.players.values():
            if bullet_rect.colliderect(player.rect()) :

                if self.shooter_id == self.game.player.id:
                    player.take_damage(self.damage)
                    self.is_exist = False
                    self.damaged_player = player.id
                    self.is_damaged = True
                    break


        if bullet_rect.colliderect(self.game.player.rect()):

            if self.shooter_id != self.game.player.id:
                self.game.player.take_damage(self.damage)
                self.is_exist = False
                self.damaged_player = self.game.player.id
                self.is_damaged = True

    def _check_collisions_smart(self, player):
        bullet_current_pos = self.pos
        bullet_next_pos = [self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1]]

        player_rect = player.rect()
        player_center = [player_rect.centerx, player_rect.centery]

        distance = self._point_to_line_distance(bullet_current_pos, bullet_next_pos, player_center)

        radius_threshold = max(player_rect.width, player_rect.height) / 2
        if distance <= radius_threshold:
            return True

        return False

    def _point_to_line_distance(self, start, end, point):
        line_dx = end[0] - start[0]
        line_dy = end[1] - start[1]

        if line_dx == 0 and line_dy == 0:
            return math.dist(start, point)

        t = ((point[0] - start[0]) * line_dx + (point[1] - start[1]) * line_dy) / (line_dx ** 2 + line_dy ** 2)
        t = max(0, min(1, t))

        proj_x = start[0] + t * line_dx
        proj_y = start[1] + t * line_dy
        dist = math.dist([proj_x, proj_y], point)

        return dist

    def _check_collision_with_walls(self, tilemap):
        bullet_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if bullet_rect.colliderect(rect):
                self.is_exist = False
                break

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], *self.image.get_rect().size)

    def render(self, surface, offset=(0, 0)):
        if self.is_exist:
            surface.blit(self.image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))

    def get_name(self, image):
        name = image.split('\\')[-1][:-4]
        return name

    def _rotate_bullet(self):
        self.image = pygame.transform.rotate(self.image, random.uniform(0, 360))

    def serialize(self):
        return {
            'pos': self.pos,
            'direction': self.direction,
            'bullet_type': self.name,
            'damage': self.damage,
            'damaged_player': self.damaged_player,
            'is_exist': self.is_exist,
            'is_damaged': self.is_damaged,
            'shooter_id': self.shooter_id,
        }