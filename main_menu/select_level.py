"""
Level Selection Menu Implementation

This module implements the level selection interface for the Teeworlds game.
"""
import subprocess
import sys
import threading

import pygame
import os

from main_menu.buttons import ImageButton
from scripts.settings import WIDTH, HEIGHT

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class LevelMenu:
    """Menu for selecting game levels."""
    
    # Button configuration
    BUTTON_WIDTH: int = 252
    BUTTON_HEIGHT: int = 74
    BUTTON_X: int = WIDTH // 2 - 126
    BUTTON_SPACING: int = 100
    FIRST_BUTTON_Y: int = 200
    
    # Text configuration
    TITLE_TEXT: str = "Select Level"
    TITLE_SIZE: int = 64
    TITLE_COLOR: tuple[int, int, int] = (0, 0, 0)
    TITLE_Y: int = 120
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the level selection menu.
        
        Args:
            screen: Pygame surface to render the menu on
        """
        self.screen = screen
        self.buttons: dict[str, ImageButton] = {}
        self.main_background: list[pygame.Surface] = []
        self.text_surface: pygame.Surface
        self.text_rect: pygame.Rect
        
        self._create_buttons()
        self._create_title()
        self._load_background()
        
    def _create_buttons(self) -> None:
        """Create and position level selection buttons."""
        self.buttons = {
            'map1': ImageButton(
                x=self.BUTTON_X,
                y=self.FIRST_BUTTON_Y,
                width=self.BUTTON_WIDTH,
                height=self.BUTTON_HEIGHT,
                text='',
                image_path= BASE_DIR + "\\assets\\default\\level_buttons\\World.png"
            ),
            'map2': ImageButton(
                x=self.BUTTON_X,
                y=self.FIRST_BUTTON_Y + self.BUTTON_SPACING,
                width=self.BUTTON_WIDTH,
                height=self.BUTTON_HEIGHT,
                text='',
                image_path=BASE_DIR + "\\assets\\default\\level_buttons\\FarLands.png"
            ),
            'save': ImageButton(
                x=self.BUTTON_X,
                y=self.FIRST_BUTTON_Y + (self.BUTTON_SPACING * 2),
                width=self.BUTTON_WIDTH,
                height=self.BUTTON_HEIGHT,
                text='',
                image_path=BASE_DIR + "\\assets\\default\\level_buttons\\Your.png"
            ),
            'create new': ImageButton(
                x=self.BUTTON_X,
                y=self.FIRST_BUTTON_Y + (self.BUTTON_SPACING * 3),
                width=self.BUTTON_WIDTH,
                height=self.BUTTON_HEIGHT,
                text='',
                image_path=BASE_DIR + "\\assets\\default\\level_buttons\\new_level_button.png"
            ),

        }
        
    def _create_title(self) -> None:
        """Create the blocks text surface."""
        try:
            font = pygame.font.Font(BASE_DIR + '\\fonts\\JapanBentoDemoVersionRegular-nRWAJ.otf', self.TITLE_SIZE)
            self.text_surface = font.render(
                self.TITLE_TEXT,
                True,
                self.TITLE_COLOR
            )
            self.text_rect = self.text_surface.get_rect(
                center=(WIDTH // 2, self.TITLE_Y)
            )
        except pygame.error as e:
            print(f"Error creating blocks text: {e}")
            
    def _load_background(self) -> None:
        """Load and scale background images."""
        try:
            self.main_background = [
                pygame.transform.scale(
                    pygame.image.load(BASE_DIR + f"\\assets\\default\\background\\{i + 1}.png"),
                    (WIDTH, HEIGHT)
                ) for i in range(4)
            ]
        except pygame.error as e:
            print(f"Error loading background images: {e}")
            # Create a simple gradient background as fallback
            self.main_background = [pygame.Surface((WIDTH, HEIGHT))]
            self.main_background[0].fill((50, 50, 100))
            
    def _handle_button_click(self, button: ImageButton) -> str | None:
        """
        Handle button click events.
        
        Args:
            button: The button that was clicked
            
        Returns:
            Map name if a level was selected, None otherwise
        """
        c = self.buttons['create new']
        if self.buttons['create new'] == button:
            threading.Thread(target=self._open_creator).start()
            return "creator_opened"

        button_map = {
            self.buttons['map1']: 'map1',
            self.buttons['map2']: 'map2',
            self.buttons['save']: 'save'
        }
        return button_map.get(button)

    def _open_creator(self):
        base_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        script_path = os.path.join(base_directory, "create_map.py")
        python_executable = sys.executable

        subprocess.run([python_executable, script_path])

            
    def _handle_events(self) -> str | None:
        """
        Handle pygame events.
        
        Returns:
            Map name if selected, None if should continue running
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.USEREVENT:
                result = self._handle_button_click(event.button)
                if result:
                    return result
                    
            for button in self.buttons.values():
                button.handle_event(event)
                
        return None
        
    def _draw(self) -> None:
        """Draw all menu components."""
        # Draw background
        self.screen.fill((0, 0, 0))
        for bg in self.main_background:
            self.screen.blit(bg, (0, 0))
            
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.check_hover(mouse_pos)
            button.draw(self.screen)
            
        # Draw blocks
        self.screen.blit(self.text_surface, self.text_rect)
        pygame.display.flip()

    def run(self) -> str:
        """
        Run the level selection menu loop.
        
        Returns:
            Selected map name
        """
        while True:
            result = self._handle_events()
            if result is not None:
                return result
                
            self._draw()
