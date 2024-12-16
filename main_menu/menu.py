"""
Main Menu Implementation

This module implements the main menu interface for the Teeworlds game.
"""

import sys,os
import pygame

from scripts.settings import WIDTH, HEIGHT
from main_menu.buttons import ImageButton
from main_menu.input.input_name import InputNameMenu
from main_menu.select_level import LevelMenu

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class MainMenu:
    """Main menu interface for the game."""
    
    TITLE_TEXT = "TEEWORLDS"
    TITLE_COLOR = (255, 0, 0)
    TITLE_SIZE = 72
    TITLE_Y_POS = 100
    
    BUTTON_WIDTH = 252
    BUTTON_HEIGHT = 74
    BUTTON_SPACING = 100
    FIRST_BUTTON_Y = 250
    
    def __init__(self, screen: pygame.Surface, show_choose_level: bool, game_instance=None):
        """
        Initialize the main menu.
        
        Args:
            screen: Pygame surface to render the menu on
            show_choose_level: Whether to show the level selection menu
            game_instance: Reference to the main game instance for accessing assets
        """
        self.screen = screen
        self.show_choose_level = show_choose_level
        self.map = ''
        self.game = game_instance
        
        self._load_background()
        self._create_buttons()
        
    def _load_background(self) -> None:
        """Load background images from pre-loaded game assets."""
        if self.game:
            self.main_background = [
                self.game.assets[f'menu_bg_{i + 1}']
                for i in range(4)
            ]
        else:
            # Fallback for backwards compatibility
            self.main_background = [
                pygame.transform.scale(
                    pygame.image.load(f"assets/default/background/{i + 1}.png"),
                    (WIDTH, HEIGHT)
                ) for i in range(4)
            ]
            
    def _create_buttons(self) -> None:
        """Create and position menu buttons."""
        button_x = WIDTH/2 - (self.BUTTON_WIDTH/2)
        
        self.buttons = {
            'start': ImageButton(
                button_x, self.FIRST_BUTTON_Y,
                self.BUTTON_WIDTH, self.BUTTON_HEIGHT,
                "", BASE_DIR + "\\assets\\default\\start_button.png"
            ),
            'exit': ImageButton(
                button_x, self.FIRST_BUTTON_Y + self.BUTTON_SPACING,
                self.BUTTON_WIDTH, self.BUTTON_HEIGHT,
                "", BASE_DIR + "\\assets\\default\\exit_button.png"
            )
        }
        
    def _draw_title(self) -> None:
        """Draw the game blocks."""
        try:
            font = pygame.font.Font(BASE_DIR + '\\fonts\\JapanBentoDemoVersionRegular-nRWAJ.otf', self.TITLE_SIZE)
            text_surface = font.render(self.TITLE_TEXT, True, self.TITLE_COLOR)
            text_rect = text_surface.get_rect(center=(WIDTH/2, self.TITLE_Y_POS))
            self.screen.blit(text_surface, text_rect)
        except pygame.error as e:
            print(f"Error rendering blocks text: {e}")
            
    def _handle_button_click(self, button: ImageButton) -> tuple[str, str] | None:
        """
        Handle button click events.
        
        Args:
            button: The button that was clicked
            
        Returns:
            Tuple of (player_name, map_name) if game should start,
            None if menu should continue running
        """
        if button == self.buttons['exit']:
            pygame.quit()
            sys.exit()
            
        if button == self.buttons['start']:
            if self.show_choose_level:
                self.map = LevelMenu(self.screen).run()
                if self.map == "creator_opened":
                    self.game.close()
            name = InputNameMenu(self.screen).run()
            
            if name == "ENDofTHEprogramGG":
                pygame.quit()
                sys.exit()
            return name, self.map
            
        return None

    def main_menu(self) -> tuple[str, str]:
        """
        Run the main menu loop.
        
        Returns:
            Tuple of (player_name, map_name) when game should start
        """
        while True:
            # Draw background
            self.screen.fill((0, 0, 0))
            for bg in self.main_background:
                self.screen.blit(bg, (0, 0))
                
            self._draw_title()
            
            # Handle events
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
            
            # Update and draw buttons
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons.values():
                button.check_hover(mouse_pos)
                button.draw(self.screen)
                
            pygame.display.flip()
