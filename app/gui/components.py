"""
Các thành phần UI cơ bản
"""

import pygame
from typing import Tuple

from .config import COLORS


class Button:
    """Nút bấm UI"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, color: Tuple[int, int, int], 
                 hover_color: Tuple[int, int, int] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.base_color = color
        self.hover_color = hover_color or tuple(min(c + 30, 255) for c in color)
        self.is_hovered = False
        self.enabled = True
    
    def set_position(self, x: int, y: int):
        """Cập nhật vị trí nút"""
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Vẽ nút lên màn hình"""
        color = self.hover_color if self.is_hovered and self.enabled else self.color
        if not self.enabled:
            color = COLORS['GRAY']
        
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, COLORS['BLACK'], self.rect, 2, border_radius=6)
        
        text_color = COLORS['WHITE'] if self.enabled else COLORS['DARK_GRAY']
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Xử lý sự kiện
        
        Returns:
            True nếu nút được click
        """
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.enabled:
                return True
        return False
