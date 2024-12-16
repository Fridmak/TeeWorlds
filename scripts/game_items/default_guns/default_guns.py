from scripts.game_items.default_guns.default_gun import DefaultGun


class Minigun(DefaultGun):
    def __init__(self, game, player):
        scale = 3
        damage = 5
        push_power = 0.1
        image = '\\tools\\minigun\\minigun.png'
        bullet_image = '\\tools\\minigun\\minigun_bullet.png'
        shooting_timeout = 5
        bullet_speed = 17
        bullet_range = 200
        spread = 4
        super().__init__(game, player, damage, push_power, scale, shooting_timeout, image, bullet_image,
                         bullet_speed, bullet_range, spread)


class DesertEagle(DefaultGun):
    def __init__(self, game, player):
        scale = 3
        damage = 7
        push_power = 1
        shooting_timeout = 30
        bullet_speed = 13
        bullet_range = 200
        spread = 6
        image = '\\tools\\desert_eagle\\deagle.png'
        bullet_image = '\\tools\\desert_eagle\\deagle_bullet.png'

        super().__init__(game, player, damage, push_power, scale, shooting_timeout, image, bullet_image,
                         bullet_speed, bullet_range, spread)


class AWP(DefaultGun):
    def __init__(self, game, player):
        scale = 3
        damage = 50
        push_power = 2.5
        shooting_timeout = 100
        bullet_speed = 18
        bullet_range = 400
        image = '\\tools\\awp\\awp.png'
        bullet_image = '\\tools\\awp\\awp_bullet.png'
        spread = 0

        super().__init__(game, player, damage, push_power, scale, shooting_timeout, image, bullet_image,
                         bullet_speed, bullet_range, spread)


class Shotgun(DefaultGun):
    def __init__(self, game, player):
        scale = 3
        damage = 20
        push_power = 0.5
        shooting_timeout = 50
        bullet_speed = 8
        bullet_range = 50
        spread = 15
        shooting_times = 5
        stability = 0.5
        image = '\\tools\\shotgun\\shotgun.png'
        bullet_image = '\\tools\\shotgun\\shotgun_bullet.png'

        super().__init__(game, player, damage, push_power, scale, shooting_timeout, image, bullet_image,
                         bullet_speed, bullet_range, spread, shooting_times, stability)
