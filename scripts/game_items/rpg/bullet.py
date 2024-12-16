import random

import pygame
import math, os

from dateutil.rrule import DAILY

from scripts.game_items.rpg.explosion import Explosion
from scripts.infrustructure import load_sprite

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'

MIN_SPEED = 1
DUMPING = 0.7


class Bullet:
    def __init__(self, game, pos, direction, is_bullet_flipped, angle, damage, range_shoot=200, speed=5, knockback=-1,
                 rickochet=False):
        self.game = game
        self.direction = direction
        self.image = self.load_and_scale_image(BASE_DIR + '\\tools\\rpg\\bullet_rpg.png')
        self.start_pos = list(pos)
        self.pos = self.start_pos[:]
        self.range = range_shoot
        self.velocity = [direction[0] * speed, direction[1] * speed]
        self.exploding_radius = 50
        self.exploded = False
        self.is_exist = True
        self.angle = angle
        self.is_bullet_flipped = is_bullet_flipped
        self.explosion_group = pygame.sprite.Group()
        self.offset = (0, 0)
        self.damage = damage
        self.is_damaged = False
        self.damaged_players = []
        self.knockback = knockback
        self.rickochet = rickochet
        self.flaught_away = False

    def load_and_scale_image(self, path):
        image = load_sprite(path)
        return pygame.transform.scale(image, (image.get_rect().width // 10, image.get_rect().height // 10))

    def update(self, blockmap, offset=(0, 0), is_enemy=False):
        if self.exploded:
            return

        self.offset = offset
        if self.check_collisions(is_enemy):
            return

        self.update_position()
        if not self.rickochet:
            self.check_range()

    def check_collisions(self, is_enemy):
        bullet_rect = self.rect()
        if self.game.player.id in self.damaged_players:
            if is_enemy:
                self.deal_damage_to_player(self.game.player)
            else:
                self.deal_damage_to_player(self.game.player, 0.7)
            return True
        else:
            if self.is_damaged:
                self.start_explode()
                return True
            self.check_damage_to_players(bullet_rect)
        return self.check_block_collisions(bullet_rect, is_enemy)

    def check_damage_to_players(self, bullet_rect):
        for player in self.game.players.values():
            if bullet_rect.colliderect(player.rect()):
                self.mark_for_damage(player)
        if bullet_rect.colliderect(self.game.player.rect()):
            if self.flaught_away:
                self.mark_for_damage(self.game.player)
        else:
            self.flaught_away = True

    def check_block_collisions(self, bullet_rect, is_enemy):
        for rect in self.game.blockmap.physics_rects_around(self.pos):
            if bullet_rect.colliderect(rect):
                if is_enemy:
                    self.start_explode()
                    return True
                if self.rickochet:
                    prev_pos = [
                        self.pos[0] - self.velocity[0],
                        self.pos[1] - self.velocity[1]
                    ]
                    self.pos = prev_pos
                    normal_vector = self.calculate_normal(self.rect(), rect)
                    self.reflect(normal_vector)
                    return False
                self.damage_nearby_players()
                return True
        return False

    def reflect(self, normal_vector):
        dot_product = sum(v * n for v, n in zip(self.velocity, normal_vector))

        # v₂ = v₁ - 2(v₁·n)n
        self.velocity = [
            (self.velocity[0] - 2 * dot_product * normal_vector[0]) * DUMPING,
            (self.velocity[1] - 2 * dot_product * normal_vector[1]) * DUMPING
        ]

        current_speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
        if current_speed < MIN_SPEED:
            self.start_explode()
            return

        self.direction = [
            self.velocity[0] / current_speed,
            self.velocity[1] / current_speed
        ]

        self.angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0]))

    def calculate_normal(self, bullet_rect, object_rect):
        collision_x = max(object_rect.left, min(bullet_rect.centerx, object_rect.right))
        collision_y = max(object_rect.top, min(bullet_rect.centery, object_rect.bottom))

        if collision_x == object_rect.left:
            return (-1, 0)
        elif collision_x == object_rect.right:
            return (1, 0)
        elif collision_y == object_rect.top:
            return (0, -1)
        else:
            return (0, 1)

    def check_range(self):
        if self.distance_traveled() > self.range:
            self.is_exist = False

    def distance_traveled(self):
        return self.distance_to(self.start_pos)

    def mark_for_damage(self, player):
        self.damaged_players.append(player.id)
        self.is_damaged = True

    def damage_nearby_players(self):
        for player in self.game.players.values():
            if self.is_within_exploding_radius(player.rect().center):
                self.mark_for_damage(player)
        if self.is_within_exploding_radius(self.game.player.rect().center):
            self.apply_explosion_force(self.game.player)
            self.mark_for_damage(self.game.player)
        self.is_damaged = True

    def is_within_exploding_radius(self, point):
        return self.distance_to(point) <= self.exploding_radius

    def update_position(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

    def deal_damage_to_player(self, player, k: float = 1):
        player.take_damage(self.damage * k)
        self.apply_explosion_force(player)
        self.start_explode()

    def apply_explosion_force(self, player):
        if self.game.player.id == player.id and self.knockback == 0:
            return

        if player.immortality_time > 0:
            return

        dx, dy, distance = self.calculate_distance_vector(player.rect().center)

        force = self.calculate_force(distance)

        angle = math.atan2(-dy, -dx)

        player.velocity[0] -= force * math.cos(angle)
        player.velocity[1] -= force * math.sin(angle)

    def calculate_distance_vector(self, target_pos):
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        distance = max(math.sqrt(dx ** 2 + dy ** 2), 2)  # Avoid division by zero
        return dx, dy, distance

    def calculate_force(self, distance):
        return max(10 / distance, 2)

    def distance_to(self, point):
        return math.sqrt((self.pos[0] - point[0]) ** 2 + (self.pos[1] - point[1]) ** 2)

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], *self.image.get_rect().size)

    def start_explode(self):
        self.exploded = True
        self.explosion_group.add(Explosion(self.pos[0] - self.offset[0], self.pos[1] - self.offset[1], self))

    def render(self, surface, offset=(0, 0)):
        self.offset = offset
        if self.is_exist:
            if not self.exploded:
                self.render_bullet(surface)
            else:
                self.render_explosion(surface)

    def render_bullet(self, surface):
        image = pygame.transform.flip(self.image, True, False) if self.is_bullet_flipped else self.image
        surface.blit(pygame.transform.rotate(image, -self.angle),
                     (self.pos[0] - self.offset[0], self.pos[1] - self.offset[1]))

    def render_explosion(self, surface):
        self.explosion_group.draw(surface)
        self.explosion_group.update()

    def serialize(self):
        return {
            'pos': self.pos,
            'direction': self.direction,
            'is_bullet_flipped': self.is_bullet_flipped,
            'angle': self.angle,
            'is_exploded': self.exploded,
            'bullet_type': 'rpg',
            'damage': self.damage,
            'damaged_players': self.damaged_players,
            'is_damaged': self.is_damaged,
        }
