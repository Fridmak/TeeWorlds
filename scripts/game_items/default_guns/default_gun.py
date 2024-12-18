import math
import pygame, os
from scripts.infrustructure import load_sprite
from scripts.settings import WIDTH, HEIGHT
from scripts.game_items.guns_rotation import get_rotated_parameters
from scripts.game_items.default_guns.default_bullet import Bullet

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'


class DefaultGun:
    def __init__(self, game, player, damage, push_power, scale, shooting_timeout, image, bullet_image, bullet_speed=10,
                 bullet_range=200, spread=2, shooting_times = 1, stability = 0):
        self.game = game
        self.player = player
        self.image = load_sprite(BASE_DIR + image)
        self.scale_mult = scale
        self.key_point = (30, 30)  # Coordinates of the key point relative to the top-left corner
        self.ticks = 0
        self.is_shooting = False
        self.angle = 0
        self.push_power = push_power
        self.damage = damage
        self.shooting_timeout = shooting_timeout
        self.bullet_image = bullet_image
        self.bullet_speed = bullet_speed
        self.bullet_range = bullet_range
        self.spread = spread
        self.shooting_times = shooting_times
        self.stability = stability


    def shoot(self, direction):
        if self.ticks > self.shooting_timeout:
            self.ticks = 0
            for i in range (self.shooting_times):
                bullet = Bullet(self.game, self.player.rect().center, direction, self.damage, self.bullet_image,
                                self.bullet_range, self.bullet_speed, self.spread, self.stability)
                self.give_player_impulse(direction)
                self.player.bullets.append(bullet)

    def get_shooting_direction(self):
        mouse_pos = pygame.mouse.get_pos()
        dx, dy = mouse_pos[0] - WIDTH / 2, mouse_pos[1] - HEIGHT / 2
        length = math.hypot(dx, dy)
        return dx / length, dy / length

    def get_bullet_start_position(self, direction):
        offset_x = self.image.get_rect().width / 2 * direction[0]
        offset_y = self.image.get_rect().height / 2 * direction[1]
        return (self.player.rect().center[0] + offset_x, self.player.rect().center[1] + offset_y)

    def update(self, tilemap, _):
        self.ticks += 1
        if self.is_shooting:
            direction = self.get_shooting_direction()
            self.shoot(direction)

    def give_player_impulse(self, direction):
        self.player.velocity[0] -= self.push_power * direction[0]
        self.player.velocity[1] -= self.push_power * direction[1]

    def render(self, surface, mouse_coord, offset=(0, 0)):
        center_x, center_y = self.player.rect().center
        scaled_image_size = (
            self.image.get_rect().width // self.scale_mult, self.image.get_rect().height // self.scale_mult)
        scaled_image = pygame.transform.scale(self.image, scaled_image_size)

        dx, dy = mouse_coord[0] - WIDTH / 2, mouse_coord[1] - HEIGHT / 2
        self.angle = math.degrees(math.atan2(dy, dx))
        draw_image, origin_pos, angle_correction = self.get_image_orientation_and_positions(scaled_image, mouse_coord)

        angle_to_render = self.angle - angle_correction
        surface.blit(*get_rotated_parameters(draw_image, (center_x - offset[0], center_y - offset[1] + 4), origin_pos,
                                             -angle_to_render))

    def get_image_orientation_and_positions(self, scaled_image, mouse_coord):
        angle_correction = 0
        if mouse_coord[0] < WIDTH / 2:
            flipped_image = pygame.transform.flip(scaled_image, True, False)
            origin_pos = ((223 - self.key_point[0]) / self.scale_mult, (59 - self.key_point[1]) / self.scale_mult)
            angle_correction = 180
        else:
            flipped_image = scaled_image
            origin_pos = (self.key_point[0] / self.scale_mult, self.key_point[1] / self.scale_mult)

        return flipped_image, origin_pos, angle_correction

    def __str__(self):
        return "DEFAULT_GUN"
