import pygame

NEIGHBOUR_OFFSETS = [(-1, 1), (0, 1), (1, 1),
                     (-1, 0), (0, 0), (1, 0),
                     (-1, -1), (0, -1), (1, -1)]

PHYSICS_blockS = {'grass',
                 'left_grass',
                 'right_grass',
                 'left_ground_wall',
                 'ground',
                 'right_ground_wall',
                 'left_bottom_ground',
                 'bottom_ground',
                 'right_bottom_ground',
                 'top_brick',
                 'top_left_brick',
                 'top_right_brick',
                 'left_brick',
                 'mid_brick',
                 'right_brick',
                 'bottom_brick',
                 'bottom_left_brick',
                 'bottom_right_brick',
                 'closed_door',
                 'closed_gray_door',
                 'glass',
                 'wood',
                 'gray_block'}

HIDING_blockS = {'bush',
                'big_wall'}


class Blockmap:
    def __init__(self, game, block_size=(16, 16)):
        self.game = game
        self.block_size = block_size
        self.blockmap = {}
        self.spawnpoint_positions = list()
        self.heal_positions = list()
        self.random_potion_positions = list()
        self.hiding_blocks_positions = list()
        self.door_positions = list()

    def find_spawnpoints(self):
        for block in self.blockmap.values():
            if block['type'] == 'spawnpoint':
                self.spawnpoint_positions.append(block['pos'])

    def find_heal_positions(self):
        for block in self.blockmap.values():
            if block['type'] == 'heal':
                self.heal_positions.append(block['pos'])

    def find_random_potion_positions(self):
        for block in self.blockmap.values():
            if block['type'] == 'random_potion':
                self.random_potion_positions.append(block['pos'])

    def find_hiding_blocks_positions(self):
        for block in self.blockmap.values():
            if 'hide' in block:
                rect = pygame.Rect(block['pos'][0] * self.block_size[0],
                                   block['pos'][1] * self.block_size[1],
                                   block['size'][0], block['size'][1])
                self.hiding_blocks_positions.append(rect)

    def find_door_positions(self):
        for block in self.blockmap.values():
            if block['type'] == 'closed_door' or block['type'] == 'closed_gray_door':
                self.door_positions.append(block['pos'])

    def blocks_around(self, pos):
        """Возвращает blocks из blockmap вокруг pos"""
        blocks = list()
        block_pos = (
        int(pos[0] // self.block_size[0]), int(pos[1] // self.block_size[1]))
        for offset in NEIGHBOUR_OFFSETS:
            check_pos = str(block_pos[0] + offset[0]) + ';' + str(
                block_pos[1] + offset[1])
            if check_pos in self.blockmap:
                blocks.append(self.blockmap[check_pos])
        return blocks

    def physics_rects_around(self, pos):
        """Возвращает Rects от физических blocks из blockmap вокруг pos"""
        block_size = self.block_size
        rects = list()
        for block in self.blocks_around(pos):
            if block['type'] in PHYSICS_blockS:
                if block['type'] == 'closed_door' or block['type'] == 'closed_gray_door':
                    block_size = (16, 32)
                rect = pygame.Rect(block['pos'][0] * self.block_size[0],
                                   block['pos'][1] * self.block_size[1],
                                   block_size[0], block_size[1])
                rects.append(rect)
        return rects

    def render(self, surface, is_editor=False, offset=(0, 0)):
        for block in self.blockmap.values():
            if (self.game.assets[block['type']] is None or
                    (block['type'] in ("heal", "random_potion", "opened_door", "closed_door", "opened_gray_door", "closed_gray_door")
                     and not is_editor) or
                    'hide' in block):
                continue
            block_pos = (block['pos'][0] * self.block_size[0],
                        block['pos'][1] * self.block_size[1])
            surface.blit(self.game.assets[block['type']],
                         (block_pos[0] - offset[0], block_pos[1] - offset[1]))

    def render_hiding_block(self, surface, offset=(0, 0)):
        for block in self.blockmap.values():
            if 'hide' in block:
                block_pos = (block['pos'][0] * self.block_size[0],
                            block['pos'][1] * self.block_size[1])
                surface.blit(self.game.assets[block['type']],
                             (block_pos[0] - offset[0], block_pos[1] - offset[1]))
