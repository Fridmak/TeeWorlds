"""
Button Components for Main Menu

This module provides button implementations for the game's main menu interface.
"""

import pygame, os
from dataclasses import dataclass


@dataclass
class ButtonStyle:
    """Style configuration for buttons."""
    FONT_SIZE: int = 36
    PADDING: int = 5
    HOVER_SCALE: float = 1.1
    TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
    BUTTON_COLOR: tuple[int, int, int] = (100, 100, 100)
    HOVER_COLOR: tuple[int, int, int] = (150, 150, 150)

class ImageButton:
    """A button with background image and text overlay."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, image_path: str, style: ButtonStyle | None = None):
        """
        Initialize an image button.
        
        Args:
            x: X coordinate of button's top-left corner
            y: Y coordinate of button's top-left corner
            width: Button width in pixels
            height: Button height in pixels
            text: Text to display on button
            image_path: Path to button's background image
            style: Optional button style configuration
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.style = style or ButtonStyle()
        self.text_surface = None
        self.text_rect = None
        self.image = None
        self.hover_image = None
        self.rect = pygame.Rect(x, y, width, height)
        self.is_hovered = False
        
        self._load_image(image_path)
        self._init_text()
        
    def _init_text(self) -> None:
        """Initialize the button's text surface and rectangle."""
        if self.text:
            try:
                font = pygame.font.Font(None, self.style.FONT_SIZE)
                self.text_surface = font.render(
                    self.text,
                    True,
                    self.style.TEXT_COLOR
                )
                self.text_rect = self.text_surface.get_rect(
                    center=self.rect.center
                )
            except pygame.error as e:
                print(f"Error creating button text: {e}")
                self.text_surface = None
                self.text_rect = None
        
    def _load_image(self, image_path: str) -> None:
        """Load and scale the button's background image."""
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            
            # Create hover image (slightly larger)
            hover_width = int(self.width * self.style.HOVER_SCALE)
            hover_height = int(self.height * self.style.HOVER_SCALE)
            self.hover_image = pygame.transform.scale(self.image, (hover_width, hover_height))
        except pygame.error as e:
            print(f"Error loading button image '{image_path}': {e}")
            # Create a default colored rectangle as fallback
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(self.style.BUTTON_COLOR)
            self.hover_image = pygame.Surface(
                (int(self.width * self.style.HOVER_SCALE),
                 int(self.height * self.style.HOVER_SCALE))
            )
            self.hover_image.fill(self.style.HOVER_COLOR)

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the button on the screen.
        
        Args:
            screen: Pygame surface to draw the button on
        """
        if not self.image or not self.hover_image:
            self._load_image("..assets/sprites/button_default.png")  # Fallback image path
            
        # Draw the appropriate image based on hover state
        current_image = self.hover_image if self.is_hovered else self.image
        image_rect = current_image.get_rect()
        
        # Center the image on the button's position if hovering
        if self.is_hovered:
            image_rect.center = self.rect.center
        else:
            image_rect.topleft = self.rect.topleft
            
        screen.blit(current_image, image_rect)
        
        # Draw text if initialized
        if self.text_surface is None and self.text:
            self._init_text()
            
        if self.text_surface and self.text_rect:
            screen.blit(self.text_surface, self.text_rect)

    def check_hover(self, mouse_pos: tuple[int, int]) -> None:
        """
        Update hover state based on mouse position.
        
        Args:
            mouse_pos: Current mouse position (x, y)
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle pygame events for the button.
        
        Args:
            event: Pygame event to handle
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            # Post a custom event when button is clicked
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, button=self))

    def __str__(self) -> str:
        return (f"ImageButton("
                f"x={self.x}, y={self.y}, width={self.width}, height={self.height}, "
                f"text='{self.text}', image='{self.image}', hovered={self.is_hovered})")

    def __eq__(self, other) -> bool:
        if not isinstance(other, ImageButton):
            return NotImplemented
        first = str(self)
        second = str(other)
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.width, self.height, self.text, self.image))

