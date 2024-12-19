import pygame, os
from scripts.infrustructure import load_sprite

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'

class HealPotion:
    def __init__(self, pos, game, heal_power=40, active_timer=300, size=(16, 16)):
        self.pos = pos
        self.game = game
        self.is_active = True
        self.timer = 0
        self.active_timer = active_timer
        self.image = load_sprite(BASE_DIR + '\\blocks\\heal.png')
        self.image = pygame.transform.scale(self.image, size)
        self.heal_power = heal_power

    def update(self):
        if not self.is_active:
            self._increment_timer()

        if self.is_active:
            self._check_player_collisions()

    def _increment_timer(self):
        self.timer += 1
        if self.timer >= self.active_timer:
            self.is_active = True

    def _check_player_collisions(self):
        for player in self._get_all_players():
            if self._collides_with(player) and player.hp < player.max_hp:
                player.hp = min(player.max_hp, player.hp + self.heal_power)
                self._disable()

    def _get_all_players(self):
        return list(self.game.players.values()) + [self.game.player]

    def _collides_with(self, player):
        return self.rect().colliderect(player.rect())

    def _disable(self):
        self.is_active = False
        self.timer = 0

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], *self.image.get_rect().size)

    def render(self, surface, offset=(0, 0)):
        if self.is_active:
            surface.blit(self.image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))