import pygame
import sys
import os
import json
from typing import Dict, Set, Tuple, Optional
from dataclasses import dataclass
from scripts.infrustructure import load_sprite
from scripts.blocks.block_button import BlockButton
from scripts.blocks.blockmap import Blockmap

# Constants
WINDOW_DIMENSIONS = WINDOW_WIDTH, WINDOW_HEIGHT = 1100, 800
DISPLAY_DIMENSIONS = DISPLAY_WIDTH, DISPLAY_HEIGHT = 550, 400
block_SIZE = 16
GRID_COLS, GRID_ROWS = 50, 50
BUTTON_START_X, BUTTON_START_Y, BUTTON_SPACING = 0, 300, 32
BUTTONS_PER_ROW = 3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))


@dataclass
class ScrollState:
    """Represents the scroll state of the editor view."""
    horizontal: Tuple[bool, bool]  # (Left, Right)
    vertical: Tuple[bool, bool]  # (Up, Down)
    offset: Tuple[int, int]  # (X, Y) offset


class Editor:
    """Level editor for creating and modifying game maps."""

    def __init__(self):
        """Initialize the level editor."""
        self._init_pygame()
        self._init_game_state()
        self._load_assets()
        self._create_buttons()
        self._load_map()

    def _init_pygame(self) -> None:
        """Initialize Pygame and setup display."""
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW_DIMENSIONS)
        self.display = pygame.Surface(DISPLAY_DIMENSIONS)
        pygame.display.set_caption('Level Editor')

    def _init_game_state(self) -> None:
        """Initialize editor state variables."""
        self.scroll = ScrollState(horizontal=(False, False), vertical=(False, False), offset=(0, 0))
        self.current_block: Optional[str] = None
        self.is_left_hold = False
        self.is_right_hold = False
        self.spawnpoints: Set[str] = set()

    def _load_assets(self) -> None:
        """Load and store all block assets."""
        paths = self.load_block_paths('blocks')
        self.assets: Dict[str, pygame.Surface] = {name: load_sprite(path) for name, path in paths.items()}

    def load_block_paths(self, directory):
        block_paths = {}
        for filename in os.listdir(BASE_DIR + '\\assets\\sprites\\' + directory):
            if filename.endswith('.png'):
                name_without_extension = filename.rsplit('.', 1)[0]
                block_paths[name_without_extension] = os.path.join(BASE_DIR + '\\assets\\sprites\\', directory, filename)
        return block_paths

    def add_text_helper(self):
        font = pygame.font.Font(None, 34)
        text1 = font.render('Это утилита для', True, (0, 0, 0))
        text2 = font.render('создания карт в игре', True, (0, 0, 0))
        text3 = font.render('TeeWords', True, (0, 0, 0))
        text4 = font.render('ЛКМ - поставить', True, (255, 0, 0))
        text5 = font.render('ПКМ - удалить', True, (255, 0, 0))
        text6 = font.render('C - сохранить карту', True, (255, 0, 0))

        self.screen.blit(text1, (860, 10))
        self.screen.blit(text2, (820, 50))
        self.screen.blit(text3, (900, 90))
        self.screen.blit(text4, (820, 150))
        self.screen.blit(text5, (820, 200))
        self.screen.blit(text6, (820, 250))

    def _create_buttons(self) -> None:
        """Create block selection buttons."""
        self.buttons: Dict[str, BlockButton] = {}
        buttons_exceptions = []
        for i, (block_type, sprite) in enumerate(self.assets.items()):
            if block_type == 'bush' or block_type == 'big_wall' or block_type == 'closed_door':
                buttons_exceptions.append((block_type, sprite))
            else:
                x = BUTTON_START_X + ((i - len(buttons_exceptions)) // BUTTONS_PER_ROW) * BUTTON_SPACING + 16
                y = BUTTON_START_Y + ((i - len(buttons_exceptions)) % BUTTONS_PER_ROW) * BUTTON_SPACING
                self.buttons[block_type] = BlockButton(x, y, sprite, 1.5)

        for i, (block_type, sprite) in enumerate(buttons_exceptions):
            x = 420
            y = 200 + i * 70
            self.buttons[block_type] = BlockButton(x, y, sprite, 1.5)

    def _load_map(self) -> None:
        """Load existing map from file."""
        self.blockmap = Blockmap(self)
        try:
            with open(BASE_DIR + 'maps/save.json', 'r', encoding='utf-8') as file:
                self.blockmap.blockmap = json.load(file)
                self.spawnpoints = {key for key, value in self.blockmap.blockmap.items() if
                                    value.get('type') == 'spawnpoint'}
        except FileNotFoundError:
            print("No existing map found. Using empty map.")
            self.blockmap.blockmap = {}

    def draw_grid(self) -> None:
        """Draw the editor grid."""
        for col in range(GRID_COLS + 1):
            x = col * block_SIZE - self.scroll.offset[0]
            pygame.draw.line(self.display, 'white', (x, 0), (x, DISPLAY_HEIGHT))

        for row in range(GRID_ROWS):
            y = row * block_SIZE - self.scroll.offset[1]
            pygame.draw.line(self.display, 'white', (0, y), (DISPLAY_WIDTH - 150, y))

    def place_block(self, remove_block: bool = False) -> None:
        """Place or remove a block at the mouse position."""
        if not self.current_block:
            return

        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] >= 801 or mouse_pos[1] >= 601:
            return

        block_pos = ((mouse_pos[0] + 2 * self.scroll.offset[0]) // 32, (mouse_pos[1] + 2 * self.scroll.offset[1]) // 32)
        blockmap_key = f"{block_pos[0]};{block_pos[1]}"

        if remove_block:
            self._remove_block(blockmap_key)
        else:
            self._add_block(blockmap_key, block_pos)

    def _remove_block(self, blockmap_key: str) -> None:
        """Remove a block from the blockmap."""
        if blockmap_key in self.blockmap.blockmap:
            if self.blockmap.blockmap[blockmap_key].get('type') == 'spawnpoint':
                self.spawnpoints.discard(blockmap_key)
            self.blockmap.blockmap.pop(blockmap_key)

    def _add_block(self, blockmap_key: str, block_pos: Tuple[int, int]) -> None:
        """Add a block to the blockmap."""
        block_data = {'type': self.current_block, 'pos': block_pos}

        # Handle special blocks
        if self.current_block == 'spawnpoint':
            self.spawnpoints.add(blockmap_key)
        elif self.current_block == 'bush':
            block_data.update({'hide': True, 'size': (48, 32)})
        elif self.current_block == 'big_wall':
            block_data.update({'hide': True, 'size': (48, 48)})

        self.blockmap.blockmap[blockmap_key] = block_data

    def _handle_input(self) -> bool:
        """Handle user input. Returns False if the editor should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouseup(event)

        return True

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle keyboard key press events."""
        actions = {
            pygame.K_a: lambda: self._set_scroll('horizontal', True, 0),
            pygame.K_d: lambda: self._set_scroll('horizontal', True, 1),
            pygame.K_w: lambda: self._set_scroll('vertical', True, 0),
            pygame.K_s: lambda: self._set_scroll('vertical', True, 1),
            pygame.K_c: self._save_map
        }
        if event.key in actions:
            actions[event.key]()

    def _handle_keyup(self, event: pygame.event.Event) -> None:
        """Handle keyboard key release events."""
        actions = {
            pygame.K_a: lambda: self._set_scroll('horizontal', False, 0),
            pygame.K_d: lambda: self._set_scroll('horizontal', False, 1),
            pygame.K_w: lambda: self._set_scroll('vertical', False, 0),
            pygame.K_s: lambda: self._set_scroll('vertical', False, 1)
        }
        if event.key in actions:
            actions[event.key]()

    def _set_scroll(self, axis: str, value: bool, index: int) -> None:
        """Set the scroll state for a specified axis."""
        setattr(
            self.scroll, axis,
            tuple(
                value if i == index else getattr(self.scroll, axis)[i]
                for i in range(2)
            )
        )

    def _handle_mousedown(self, event: pygame.event.Event) -> None:
        """Handle mouse button press events."""
        if event.button == 1:  # Left click
            self.is_left_hold = True
        elif event.button == 3:  # Right click
            self.is_right_hold = True

    def _handle_mouseup(self, event: pygame.event.Event) -> None:
        """Handle mouse button release events."""
        if event.button == 1:  # Left click
            self.is_left_hold = False
        elif event.button == 3:  # Right click
            self.is_right_hold = False

    def _update_scroll(self) -> None:
        """Update scroll position based on input."""
        x_offset, y_offset = self.scroll.offset
        x_offset = max(
            min(x_offset + (1 if self.scroll.horizontal[1] else -1 if self.scroll.horizontal[0] else 0), 400), 0)
        y_offset = max(min(y_offset + (1 if self.scroll.vertical[1] else -1 if self.scroll.vertical[0] else 0), 400), 0)
        self.scroll.offset = (x_offset, y_offset)

    def _save_map(self) -> None:
        """Save the current map to file."""
        if not self.spawnpoints:
            print('Cannot save map without spawn points')
            return

        try:
            with open('maps/save.json', 'w', encoding='utf-8') as file:
                json.dump(self.blockmap.blockmap, file)
            print('Map saved successfully')
        except Exception as e:
            print(f'Error saving map: {e}')

    def _update_buttons(self) -> None:
        """Update button states and handle selection."""
        for block_type, button in self.buttons.items():
            button.draw(self.display)
            if button.clicked:
                self.current_block = block_type

        if self.current_block:
            pygame.draw.rect(self.display, 'red', self.buttons[self.current_block].rect, 1)

    def run(self) -> None:
        """Main editor loop."""
        try:
            while True:
                self.display.fill((233, 245, 80))

                self.draw_grid()
                self.blockmap.render(self.display, True, self.scroll.offset)
                self.blockmap.render_hiding_block(self.display, self.scroll.offset)

                pygame.draw.rect(self.display, 'gray', pygame.Rect(0, 304, 400, 100))
                pygame.draw.rect(self.display, 'gray', pygame.Rect(400, 0, 150, 450))

                self._update_buttons()
                if not self._handle_input():
                    break

                if self.is_left_hold:
                    self.place_block()
                if self.is_right_hold:
                    self.place_block(remove_block=True)

                self._update_scroll()

                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
                self.add_text_helper()
                pygame.display.update()

        except Exception as e:
            print(f"Error in editor: {e}")
        finally:
            pygame.quit()
            sys.exit()


editor = Editor()
editor.run()
