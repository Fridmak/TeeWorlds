"""
Input Box Implementation

This module provides a customizable text input box for the game's UI.
"""

import pygame, os
from dataclasses import dataclass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

@dataclass
class InputBoxStyle:
    """Style configuration for input boxes."""
    font_size: int = 64
    padding: int = 5
    border_width: int = 2
    max_length: int = 10
    active_color: tuple[int, int, int] = (100, 100, 100)
    inactive_color: tuple[int, int, int] = (200, 200, 200)
    text_color: tuple[int, int, int] = (0, 0, 0)


class InputBox:
    """A customizable text input box for user input."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 screen: pygame.Surface, active_color: tuple[int, int, int] | pygame.Color = (100, 100, 100),
                 inactive_color: tuple[int, int, int] | pygame.Color = (200, 200, 200),
                 text: str = '', style: InputBoxStyle | None = None) -> None:
        """
        Initialize an input box.
        
        Args:
            x: X coordinate of box's top-left corner
            y: Y coordinate of box's top-left corner
            width: Box width in pixels
            height: Box height in pixels
            screen: Pygame surface to render on
            active_color: Color when box is active
            inactive_color: Color when box is inactive
            text: Initial text content
            style: Optional style configuration
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.screen = screen
        self.text: str = text
        
        # Colors
        if style is None:
            style = InputBoxStyle()
            if isinstance(active_color, (tuple, pygame.Color)):
                style.active_color = tuple(active_color)
            if isinstance(inactive_color, (tuple, pygame.Color)):
                style.inactive_color = tuple(inactive_color)
                
        self.style = style
        self.active_color = self.style.active_color
        self.inactive_color = self.style.inactive_color
        self.current_color = self.active_color
        self.text_color = self.style.text_color
        
        # State
        self.is_enter_pressed: bool = False
        
        self._create_font()
        self._update_text_surface()
        
    def _create_font(self) -> None:
        """Create the font for rendering text."""
        self.font = pygame.font.Font(None, self.style.font_size)
            
    def _update_text_surface(self) -> None:
        """Update the rendered text surface."""
        try:
            self.txt_surface = self.font.render(
                self.text,
                True,
                self.text_color
            )
        except pygame.error as e:
            print(f"Error rendering text: {e}")
            # Create empty surface as fallback
            self.txt_surface = pygame.Surface((0, 0))
            
    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """
        Handle keyboard input events.
        
        Args:
            event: Pygame keyboard event
        """
        if event.key == pygame.K_RETURN:
            self.is_enter_pressed = True
            
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            
        elif event.key == 96:  # Backtick key
            return
            
        elif len(self.text) < self.style.max_length:
            self.text += event.unicode
            
        self._update_text_surface()

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle pygame events for the input box.
        
        Args:
            event: Pygame event to handle
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.current_color = (self.active_color if self.rect.collidepoint(event.pos) 
                                  else self.inactive_color)
            
        elif event.type == pygame.KEYDOWN and self.current_color == self.active_color:
            self._handle_keydown(event)

    def update(self) -> None:
        """Update the input box state and dimensions."""
        # Adjust width to fit text with padding
        width = max(
            self.width,
            self.txt_surface.get_width() + (self.style.padding * 2)
        )
        self.rect.w = width

    def draw(self) -> None:
        """Draw the input box and its text content."""
        # Draw text
        text_x = self.rect.x + self.style.padding
        text_y = self.rect.y + self.style.padding
        self.screen.blit(self.txt_surface, (text_x, text_y))
        
        # Draw border
        pygame.draw.rect(
            self.screen,
            self.current_color,
            self.rect,
            self.style.border_width
        )
