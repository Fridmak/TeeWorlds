import random

import pygame
import math, os
from scripts.game_items.rpg.explosion import Explosion
from scripts.infrustructure import load_sprite

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'


class Bullet:
    def __init__(self, game, pos, direction, is_bullet_flipped, angle, damage, range_shoot=200, speed=5, knockback=-1, rickochet = False):
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
        self.distance_flaught = 0
        self.rickochet = rickochet

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
        self.update_range()
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

    def check_block_collisions(self, bullet_rect, is_enemy):
        for rect in self.game.blockmap.physics_rects_around(self.pos):
            if bullet_rect.colliderect(rect):
                if is_enemy:
                    self.start_explode()
                    return True
                if self.rickochet:
                    normal_vector = self.calculate_normal(bullet_rect, rect)
                    self.reflect(normal_vector)
                    return False
                self.damage_nearby_players()
                return True
        return False

    def reflect(self, normal_vector):
        dot_product = sum(p * n for p, n in zip(self.velocity, normal_vector))
        self.velocity = [
            (self.velocity[0] - 2 * dot_product * normal_vector[0]) * 0.9,
            (self.velocity[1] - 2 * dot_product * normal_vector[1]) * 0.9
        ]
        self.direction = [
            self.velocity[0] / math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2),
            self.velocity[1] / math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
        ]
        self.angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0]))

    def calculate_normal(self, bullet_rect, object_rect):
        if abs(bullet_rect.left - object_rect.right) < abs(bullet_rect.right - object_rect.left):
            return (-1, 0)
        elif abs(bullet_rect.right - object_rect.left) < abs(bullet_rect.left - object_rect.right):
            return (1, 0)
        elif abs(bullet_rect.top - object_rect.bottom) < abs(bullet_rect.bottom - object_rect.top):
            return (0, -1)
        else:
            return (0, 1)

    def update_range(self):
        self.distance_flaught = self.distance_traveled()
        self.start_pos = self.pos

    def check_range(self):
        if self.distance_traveled() > self.range:
            self.is_exist = False

    def distance_traveled(self):
        return self.distance_to(self.start_pos) + self.distance_flaught

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
