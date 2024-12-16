import pygame, os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')) + '\\assets\\sprites\\'

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, bullet):
        super().__init__()
        self.bullet = bullet
        self.images = self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.counter = 0
        self.explosion_speed = 2

    def load_images(self):
        images = []
        for num in range(1, 6):
            image_path = BASE_DIR + f"\\tools\\rpg\\exploding\\exp{num}.png"
            img = pygame.image.load(image_path)
            img = pygame.transform.scale(img, (40, 40))
            images.append(img)
        return images

    def update(self):
        self.counter += 1
        if self.counter >= self.explosion_speed:
            self.counter = 0
            self.index += 1
            if self.index < len(self.images):
                self.image = self.images[self.index]
            else:
                self.end_explosion()

    def end_explosion(self):
        self.kill()
        self.bullet.is_exist = False