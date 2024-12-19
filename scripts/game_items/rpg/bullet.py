import random

import pygame
import math, os

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
        self.spread = 3
        self.velocity = self._apply_spread(direction, speed, self.spread)
        self.exploding_radius = 50
        self.exploded = False
        self.is_exist = True
        self.angle = angle
        self.is_bullet_flipped = is_bullet_flipped
        self.explosion_group = pygame.sprite.Group()
        self.offset = (0, 0)
        self.damage = damage
        self.is_damaged = False
        self.damaged_player = []
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

    def _apply_spread(self, direction, speed, spread):
        spread_angle = random.uniform(-spread, spread)

        angle = math.atan2(direction[1], direction[0]) + math.radians(spread_angle)

        return [math.cos(angle) * speed, math.sin(angle) * speed]

    def check_collisions(self, is_enemy):
        bullet_rect = self.rect()
        if self.game.player.id in self.damaged_player:
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
                    self._handle_bullet_penetration(bullet_rect, rect)
                    normal_vector = self.calculate_normal(self.rect(), rect)
                    self.reflect(normal_vector)
                    return False
                self.damage_nearby_players()
                return True
        return False

    def _calculate_penetration_depth(self, bullet_rect, block_rect):
        if bullet_rect.centerx < block_rect.centerx:
            x_depth = bullet_rect.right - block_rect.left
        else:
            x_depth = block_rect.right - bullet_rect.left

        if bullet_rect.centery < block_rect.centery:
            y_depth = bullet_rect.bottom - block_rect.top
        else:
            y_depth = block_rect.bottom - bullet_rect.top

        return x_depth, y_depth

    def _calculate_rollback_step(self, velocity, penetration):
        # Вычисляем шаг отката на основе скорости и глубины проникновения
        speed = math.sqrt(velocity[0] ** 2 + velocity[1] ** 2)
        if speed == 0:
            return 0.1  # дефолтный шаг

        # Чем больше скорость и глубина, тем больше шаг
        penetration_magnitude = math.sqrt(penetration[0] ** 2 + penetration[1] ** 2)
        return min(0.2, max(0.05, penetration_magnitude / speed))

    def _handle_bullet_penetration(self, bullet_rect, rect):
        prev_pos = self.pos[:]
        test_rect = bullet_rect.copy()
        max_iterations = 20
        iterations = 0
        min_step = 0.01

        while test_rect.colliderect(rect) and iterations < max_iterations:
            x_depth, y_depth = self._calculate_penetration_depth(test_rect, rect)
            step = self._calculate_rollback_step(self.velocity, (x_depth, y_depth))

            if step < min_step:
                break

            prev_pos = [
                prev_pos[0] - self.velocity[0] * step,
                prev_pos[1] - self.velocity[1] * step
            ]
            test_rect.x = prev_pos[0] - self.offset[0]
            test_rect.y = prev_pos[1] - self.offset[1]
            iterations += 1

        self.pos = prev_pos[:]

    def _get_collision_point(self, bullet_rect, object_rect):
        return (
            max(object_rect.left, min(bullet_rect.centerx, object_rect.right)),
            max(object_rect.top, min(bullet_rect.centery, object_rect.bottom))
        )

    def _get_distances_to_sides(self, collision_point, object_rect):
        x, y = collision_point
        return {
            'left': (abs(x - object_rect.left), (-1, 0)),
            'right': (abs(x - object_rect.right), (1, 0)),
            'top': (abs(y - object_rect.top), (0, -1)),
            'bottom': (abs(y - object_rect.bottom), (0, 1))
        }

    def _get_normal_from_velocity(self, distances):
        conditions = [
            (distances['left'][0], self.velocity[0] > 0, distances['left'][1]),
            (distances['right'][0], self.velocity[0] < 0, distances['right'][1]),
            (distances['top'][0], self.velocity[1] > 0, distances['top'][1]),
            (distances['bottom'][0], self.velocity[1] < 0, distances['bottom'][1])
        ]

        min_dist = min(dist for dist, _, _ in conditions)
        for dist, velocity_check, normal in conditions:
            if dist == min_dist and velocity_check:
                return normal
        return None

    def _get_normal_from_center(self, collision_point, object_rect):
        center_x = (object_rect.left + object_rect.right) / 2
        center_y = (object_rect.top + object_rect.bottom) / 2
        dx = collision_point[0] - center_x
        dy = collision_point[1] - center_y

        length = math.sqrt(dx * dx + dy * dy)
        return (1, 0) if length == 0 else (dx / length, dy / length)

    def calculate_normal(self, bullet_rect, object_rect):
        collision_point = self._get_collision_point(bullet_rect, object_rect)
        distances = self._get_distances_to_sides(collision_point, object_rect)

        normal = self._get_normal_from_velocity(distances)
        if normal is None:
            normal = self._get_normal_from_center(collision_point, object_rect)

        return normal

    def _calculate_reflection_vector(self, velocity, normal):
        dot_product = sum(v * n for v, n in zip(velocity, normal))
        return [
            (velocity[0] - 2 * dot_product * normal[0]) * DUMPING,
            (velocity[1] - 2 * dot_product * normal[1]) * DUMPING
        ]

    def _update_direction_and_angle(self):
        current_speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
        if current_speed < MIN_SPEED:
            return False

        self.direction = [
            self.velocity[0] / current_speed,
            self.velocity[1] / current_speed
        ]
        self.angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0]))
        return True

    def reflect(self, normal_vector):
        self.velocity = self._calculate_reflection_vector(self.velocity, normal_vector)
        if not self._update_direction_and_angle():
            self.start_explode()

    def check_range(self):
        if self.distance_traveled() > self.range:
            self.is_exist = False

    def distance_traveled(self):
        return self.distance_to(self.start_pos)

    def mark_for_damage(self, player):
        self.damaged_player.append(player.id)
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
            'damaged_player': self.damaged_player,
            'is_damaged': self.is_damaged,
        }
