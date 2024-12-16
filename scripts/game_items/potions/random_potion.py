import pygame, os
from random import choice
from scripts.infrustructure import load_sprite


class BuffType:
    SPEED_UP = "speed_up"
    IMMORTALITY = "immortality"
    DAMAGE_UP = "damage_up"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'


class RandomPotion:
    def __init__(self, pos, game):
        self.position = pos
        self.game = game
        self.is_active = True
        self.spawn_timer = 0
        self.spawn_timer_max = 600
        self.image = pygame.transform.scale(load_sprite(BASE_DIR + '\\blocks\\random_potion.png'), (16, 16))

        self.buffs = {
            BuffType.SPEED_UP: "Скорость увеличена",
            BuffType.IMMORTALITY: "Временная неуязвимость",
            BuffType.DAMAGE_UP: "Урон увеличен"
        }
        self.current_buff = choice(list(self.buffs.keys()))
        self.buff_timer = 0
        self.buff_timer_max = 300
        self.is_buff_active = False
        self.is_text_active = False
        self.text = ""
        self.text_color = tuple(choice(range(255)) for _ in range(3))

    def update(self):
        self._update_timers()
        if self.is_buff_active:
            self._update_buff()
        elif self._is_colliding_with_player():
            self._activate_buff()

    def _update_timers(self):
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_timer_max:
            self.is_active = True
            self.current_buff = choice(list(self.buffs.keys()))

    def _update_buff(self):
        self.buff_timer += 1
        if self.buff_timer >= self.buff_timer_max // 2:
            self.is_text_active = False
        if self.buff_timer >= self.buff_timer_max:
            self._deactivate_buff()

    def _is_colliding_with_player(self):
        potion_rect = self.rect()
        if any(potion_rect.colliderect(player.rect()) for player in self.game.players.values()):
            return True
        return potion_rect.colliderect(self.game.player.rect())

    def _activate_buff(self):
        self.is_active = False
        self.spawn_timer = 0
        self.buff_timer = 0
        self.is_buff_active = True
        self.text = self.buffs[self.current_buff]
        self.is_text_active = True

        if self.current_buff == BuffType.SPEED_UP:
            self.game.player.max_velocity = 4
        elif self.current_buff == BuffType.IMMORTALITY:
            self.game.player.immortality_time = 10 ** 5
        elif self.current_buff == BuffType.DAMAGE_UP:
            self.game.player.rpg.damage *= 2
            self.game.player.minigun.damage *= 2

    def _deactivate_buff(self):
        self.is_buff_active = False
        if self.current_buff == BuffType.SPEED_UP:
            self.game.player.max_velocity = 2
        elif self.current_buff == BuffType.IMMORTALITY:
            self.game.player.immortality_time = 0
        elif self.current_buff == BuffType.DAMAGE_UP:
            self.game.player.rpg.damage //= 2
            self.game.player.minigun.damage //= 2

    def rect(self):
        return pygame.Rect(self.position[0], self.position[1], *self.image.get_rect().size)

    def render(self, surface, offset=(0, 0)):
        if self.is_active:
            surface.blit(self.image, (self.position[0] - offset[0], self.position[1] - offset[1]))
        if self.is_text_active:
            text_surface = pygame.font.Font(None, 28).render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.position[0] + 5, self.position[1] - 40))
            text_rect.x -= offset[0]
            text_rect.y -= offset[1]
            surface.blit(text_surface, text_rect)