from typing import Dict, Tuple, Optional

import pygame

from src.models.network import Network
from src.models.zone import ZoneType

class Visualizer:
    def __init__(self, network: Network) -> None:
        self.network = network
        self.WIDTH = 720
        self.HEIGHT = 1280
        self.BACKGROUND_COLOR = (0, 0, 0)
        self.HUB_RADIUS = 30
        self.DEFAULT_HUB_COLOR = (100, 200, 255)

        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Fly-in")
        self.clock = pygame.time.Clock()

        # Calculate bounds for scaling
        self._calculate_bounds()

        # Draw the initial frame.
        self.render()

    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color string to RGB tuple."""
        try:
            hex_color = hex_color.lstrip("#")
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, TypeError):
            pass
        return None

    def _get_hub_color(self, zone) -> Tuple[int, int, int]:
        """Get hub color from zone metadata or use default."""
        if zone.color:
            rgb = self._hex_to_rgb(zone.color)
            if rgb:
                return rgb
        return self.DEFAULT_HUB_COLOR

    def _calculate_bounds(self) -> None:
        """Calculate min/max coordinates to scale zones to screen."""
        if not self.network.zones:
            self.min_x = self.min_y = 0
            self.max_x = self.max_y = 1
            return

        xs = [z.x for z in self.network.zones.values()]
        ys = [z.y for z in self.network.zones.values()]
        self.min_x = min(xs)
        self.max_x = max(xs)
        self.min_y = min(ys)
        self.max_y = max(ys)

        # Add padding
        self.range_x = max(self.max_x - self.min_x, 1)
        self.range_y = max(self.max_y - self.min_y, 1)

    def _screen_coords(self, x: int, y: int) -> tuple:
        """Convert zone coordinates to screen coordinates."""
        padding = 50
        screen_x = padding + (x - self.min_x) / self.range_x * (self.WIDTH - 2 * padding)
        screen_y = padding + (y - self.min_y) / self.range_y * (self.HEIGHT - 2 * padding)
        return (int(screen_x), int(screen_y))

    def render(self) -> None:
        """Renders the current state with hubs as circles."""
        self.screen.fill(self.BACKGROUND_COLOR)

        # Draw all hubs as circles
        for zone in self.network.zones.values():
            screen_x, screen_y = self._screen_coords(zone.x, zone.y)
            color = self._get_hub_color(zone)
            pygame.draw.circle(self.screen, color, (screen_x, screen_y), self.HUB_RADIUS)

        pygame.display.flip()

    def update(self, drone_positions: Dict[str, str]) -> None:
        """Renders the current state of the simulation."""
        _ = drone_positions

        # Handle events to keep the window responsive.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        self.render()
        self.clock.tick(60)  # 60 FPS

