"""Render text to pygame surfaces (pygame.font is broken on Python 3.14)."""

from __future__ import annotations

from functools import lru_cache
from typing import Tuple

import pygame
from PIL import Image, ImageDraw, ImageFont


_FONT_PATHS = (
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


@lru_cache(maxsize=32)
def _load_font(size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_text(
    text: str,
    size: int,
    color: Tuple[int, int, int],
    *,
    bold: bool = False,
    bg: Tuple[int, int, int, int] | None = None,
    outline: Tuple[int, int, int] | None = None,
    outline_width: int = 2,
) -> pygame.Surface:
    """Render UTF-8 text into an RGBA pygame surface."""
    font = _load_font(size, bold)
    rgb = color[:3]

    if outline:
        pad = outline_width
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0] + pad * 2
        h = bbox[3] - bbox[1] + pad * 2
        img = Image.new("RGBA", (int(max(w, 1)), int(max(h, 1))), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        ox, oy = pad - bbox[0], pad - bbox[1]
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((ox + dx, oy + dy), text, font=font, fill=outline[:3] + (255,))
        draw.text((ox, oy), text, font=font, fill=rgb + (255,))
    else:
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        fill: Tuple[int, ...] = bg if bg is not None else (0, 0, 0, 0)
        img = Image.new("RGBA", (int(max(w, 1)), int(max(h, 1))), fill)
        draw = ImageDraw.Draw(img)
        draw.text((-bbox[0], -bbox[1]), text, font=font, fill=rgb + (255,))

    return pygame.image.frombuffer(img.tobytes(), img.size, "RGBA").copy()


def drone_display_number(drone_id: str) -> str:
    """Extract numeric label from ids like D1, D12."""
    if drone_id.upper().startswith("D"):
        return drone_id[1:] or drone_id
    return drone_id
