import pygame


def load_sprite(path):
    sprite = pygame.image.load(path).convert()
    sprite.set_colorkey((0, 0, 0))
    return sprite
