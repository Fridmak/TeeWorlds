import pygame
import math


class Hook:
    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.pos = (0, 0)
        self.velocity = [0, 0]
        self.speed = 10
        self.length = 0
        self.is_hooked = False
        self.max_length = 200
        self.is_rope_torn = True
        self.tension_coefficient = 0.1

    def shoot(self, direction):
        if self.is_rope_torn:
            self.reset_rope(direction)

    def reset_rope(self, direction):
        self.is_rope_torn = False
        self.pos = self.player.rect().center
        self.velocity = [direction[0] * self.speed, direction[1] * self.speed]
        self.length = 0

    def update(self, tilemap):
        self.check_rope_state()

        if self.is_hooked:
            self.pull_player()

        if not self.is_rope_torn and not self.is_hooked:
            self.update_position()
            self.check_collision_with_tilemap(tilemap)

    def check_rope_state(self):
        if not pygame.mouse.get_pressed()[2]:
            self.is_rope_torn = True
            self.is_hooked = False

    def update_position(self):
        self.pos = (self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1])
        player_center = self.player.rect().center
        self.length = math.dist(player_center, self.pos)
        if self.length > self.max_length:
            self.is_rope_torn = True
            self.is_hooked = False

    def check_collision_with_tilemap(self, tilemap):
        for rect in tilemap.physics_rects_around(self.pos):
            if pygame.Rect(rect).collidepoint(self.pos):
                self.is_hooked = True
                break

    def pull_player(self):
        player_pos = self.player.rect().center
        dx, dy = self.pos[0] - player_pos[0], self.pos[1] - player_pos[1]
        distance = math.hypot(dx, dy)

        if distance > self.max_length:
            self.is_rope_torn = True
            self.is_hooked = False
            return

        if distance > self.length:
            self.apply_tension(dx, dy, distance)
        else:
            self.length = distance

    def apply_tension(self, dx, dy, distance):
        force = (distance - self.length) * self.tension_coefficient
        force_x = force * (dx / distance)
        force_y = force * (dy / distance)
        self.player.velocity[0] += force_x
        self.player.velocity[1] += force_y

    def render(self, surface, scroll):
        if not self.is_rope_torn:
            pygame.draw.line(
                surface,
                (0, 0, 0),
                (self.player.rect().centerx - scroll[0], self.player.rect().centery - scroll[1]),
                (self.pos[0] - scroll[0], self.pos[1] - scroll[1]),
                2
            )