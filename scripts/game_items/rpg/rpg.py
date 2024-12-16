import pygame
import math, os
from scripts.infrustructure import load_sprite
from scripts.settings import WIDTH, HEIGHT
from scripts.game_items.guns_rotation import get_rotated_parameters
from scripts.game_items.rpg.bullet import Bullet

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class Rpg:
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.image = load_sprite(BASE_DIR + '\\assets\\sprites\\tools\\rpg\\rpg.png')
        self.scale_mult = 10
        self.key_point = (30, 30)  # Key point for rotation
        self.ticks = 0
        self.angle = 0
        self.push_power = -1
        self.is_shooting = False
        self.is_bullet_flipped = False
        self.damage = 30
        self.shooting_timeout = 60

    def get_shooting_direction(self):
        mouse_pos = pygame.mouse.get_pos()
        dx, dy = mouse_pos[0] - WIDTH / 2, mouse_pos[1] - HEIGHT / 2
        length = math.hypot(dx, dy)
        return dx / length, dy / length

    def shoot(self, direction):
        if self.ticks > self.shooting_timeout:
            self.ticks = 0
            bullet = Bullet(self.game, self.player.rect().center, direction, self.is_bullet_flipped, self.angle,
                            self.damage, knockback=self.push_power)
            self.player.bullets.append(bullet)

    def update(self, tilemap, offset=(0, 0)):
        self.ticks += 1
        if self.is_shooting:
            self.shoot(self.get_shooting_direction())

    def render(self, surface, mouse_coord, offset=(0, 0)):
        center_x, center_y = self.player.rect().center
        scaled_image = self.scale_image(self.image, self.scale_mult)
        angle = self.calculate_angle(mouse_coord)

        if mouse_coord[0] < WIDTH / 2:
            flipped_image = pygame.transform.flip(scaled_image, True, False)
            angle += 180
            origin_pos = self.get_flipped_origin()
            self.is_bullet_flipped = True
        else:
            flipped_image = scaled_image
            origin_pos = self.get_origin()
            self.is_bullet_flipped = False

        self.angle = angle
        rotated_image_params = get_rotated_parameters(flipped_image,
                                                      (center_x - offset[0], center_y - offset[1] + 4),
                                                      origin_pos,
                                                      -angle)
        surface.blit(*rotated_image_params)

    def scale_image(self, image, scale_mult):
        """Scales the image down by the given multiplier."""
        return pygame.transform.scale(image,
                                      (image.get_rect().width / scale_mult,
                                       image.get_rect().height / scale_mult))

    def calculate_angle(self, mouse_coord):
        """Calculates the angle between the center of the screen and the mouse coordinates."""
        dx = mouse_coord[0] - WIDTH / 2
        dy = mouse_coord[1] - HEIGHT / 2
        return math.degrees(math.atan2(dy, dx))

    def get_origin(self):
        """Returns the original key point for rotation."""
        return (self.key_point[0] / self.scale_mult,
                self.key_point[1] / self.scale_mult)

    def get_flipped_origin(self):
        """Returns the key point for rotation when the image is flipped."""
        return ((223 - self.key_point[0]) / self.scale_mult,
                (59 - self.key_point[1]) / self.scale_mult)