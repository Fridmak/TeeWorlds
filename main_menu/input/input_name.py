"""
Input Name Menu Implementation

This module implements the name input interface for the Teeworlds game.
"""

import sys, os
import pygame

from main_menu.buttons import ImageButton
from main_menu.input.input_box import InputBox
from scripts.settings import WIDTH, HEIGHT

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class InputNameMenu:
    """Menu for inputting player name."""

    # Button configuration
    BUTTON_WIDTH: int = 252
    BUTTON_HEIGHT: int = 74
    BUTTON_X: int = WIDTH // 2 - 126
    BUTTON_Y: int = HEIGHT - 150
    
    # Input box configuration
    INPUT_BOX_WIDTH: int = 400
    INPUT_BOX_HEIGHT: int = 50
    INPUT_BOX_X: int = WIDTH // 2 - 200
    INPUT_BOX_Y: int = HEIGHT // 2
    
    # Text configuration
    TITLE_TEXT: str = "Enter your name"
    TITLE_SIZE: int = 64
    TITLE_COLOR: tuple[int, int, int] = (0, 0, 0)
    TITLE_Y: int = HEIGHT // 3

    def __init__(self, screen: pygame.Surface):
        """
        Initialize the input name menu.
        
        Args:
            screen: Pygame surface to render the menu on
        """
        self.screen = screen
        self.button: ImageButton
        self.input_box: InputBox
        self.main_background: list[pygame.Surface] = []
        self.text_surface: pygame.Surface
        self.text_rect: pygame.Rect
        
        self._load_background()
        self._create_title()
        self._create_button()
        self._create_input_box()

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

    def _create_button(self) -> None:
        """Create the submit button."""
        self.button = ImageButton(
            x=self.BUTTON_X,
            y=self.BUTTON_Y,
            width=self.BUTTON_WIDTH,
            height=self.BUTTON_HEIGHT,
            text='',
            image_path=BASE_DIR + "\\assets\\default\\start_button.png"
        )

    def _create_input_box(self) -> None:
        """Create the input box for name entry."""
        self.input_box = InputBox(
            x=self.INPUT_BOX_X,
            y=self.INPUT_BOX_Y,
            width=self.INPUT_BOX_WIDTH,
            height=self.INPUT_BOX_HEIGHT,
            screen=self.screen
        )

    def _handle_events(self) -> str | None:
        """
        Handle pygame events.
        
        Returns:
            Player name if submitted, None if should continue running
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.USEREVENT and event.button == self.button:
                if len(self.input_box.text) > 0:
                    return self.input_box.text

            self.button.handle_event(event)
            self.input_box.handle_event(event)

        return None

    def _draw(self) -> None:
        """Draw all menu components."""
        # Draw background
        self.screen.fill((0, 0, 0))
        for bg in self.main_background:
            self.screen.blit(bg, (0, 0))

        # Draw components
        self.screen.blit(self.text_surface, self.text_rect)
        mouse_pos = pygame.mouse.get_pos()
        self.button.check_hover(mouse_pos)
        self.button.draw(self.screen)
        self.input_box.draw()
        pygame.display.flip()

    def run(self) -> str:
        """
        Run the input name menu loop.
        
        Returns:
            Player name when submitted
        """
        while True:
            result = self._handle_events()
            if result is not None:
                return result

            self._draw()
