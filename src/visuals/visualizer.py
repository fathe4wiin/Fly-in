from __future__ import annotations

import math
import sys
from typing import Dict, List, Optional, Tuple

import pygame

from src.models.network import Network
from src.models.zone import ZoneType
from src.visuals.text_render import drone_display_number, render_text

# Flip this to True/False to control whether the per-zone F cost overlay
# (heuristic turns-to-goal, shown next to "max N") is visible when the
# visualizer window first opens. Can still be toggled at runtime with the
# "C" key regardless of this default.
SHOW_F_COST_ON_START: bool = True


class _Button:
    def __init__(self, rect: pygame.Rect, action: str, tooltip: str) -> None:
        self.rect = rect
        self.action = action
        self.tooltip = tooltip
        self.hovered = False


class Visualizer:
    CONTROL_BAR_HEIGHT = 72
    BTN_SIZE = 44
    BTN_GAP = 12

    def __init__(self, network: Network) -> None:
        self.network = network
        self.WIDTH = 1920
        self.HEIGHT = 1080
        self.PADDING = 60
        self.graph_height = self.HEIGHT - self.CONTROL_BAR_HEIGHT

        self.BG_COLOR = (15, 15, 25)
        self.CONN_COLOR = (60, 60, 80)
        self.TEXT_COLOR = (220, 220, 230)
        self.DRONE_FILL = (255, 200, 0)
        self.DRONE_RING = (40, 30, 10)
        self.DEFAULT_HUB_COLOR = (100, 150, 240)
        self.BAR_COLOR = (28, 28, 40)
        self.BTN_COLOR = (65, 70, 95)
        self.BTN_ACTIVE = (120, 140, 200)
        self.ACCENT = (100, 180, 255)

        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Fly-in Simulation")
        self.clock = pygame.time.Clock()

        self._calculate_bounds()
        self.drone_positions: Dict[str, str] = {}
        self.frames: List[Dict[str, str]] = []
        self.turn_events: Dict[int, List[str]] = {}
        self.current_turn = 0
        self.max_turn = 0
        self._buttons: List[_Button] = []
        self._running = True
        self._build_buttons()

        # Per-zone F cost (heuristic turns-to-goal) overlay. Starting state
        # comes from SHOW_F_COST_ON_START at the top of this file; toggle at
        # runtime with the "C" key. Populated via set_zone_costs().
        self.zone_costs: Dict[str, float] = {}
        self.show_cost_overlay: bool = SHOW_F_COST_ON_START

    def set_zone_costs(self, zone_costs: Dict[str, float]) -> None:
        """Provide the per-zone F cost values shown by the cost overlay."""
        self.zone_costs = zone_costs

    def _blit_text(
        self,
        text: str,
        pos: Tuple[int, int],
        size: int,
        color: Tuple[int, int, int],
        *,
        bold: bool = False,
        center: bool = False,
        outline: Tuple[int, int, int] | None = None,
        outline_width: int = 2,
    ) -> None:
        surf = render_text(
            text, size, color, bold=bold, outline=outline, outline_width=outline_width
        )
        x, y = pos
        if center:
            x -= surf.get_width() // 2
            y -= surf.get_height() // 2
        self.screen.blit(surf, (x, y))

    def _build_buttons(self) -> None:
        labels = [
            ("first", "Go to start (Home)"),
            ("prev", "Step back"),
            ("next", "Step forward"),
            ("last", "Go to end (End)"),
        ]
        total_w = len(labels) * self.BTN_SIZE + (len(labels) - 1) * self.BTN_GAP
        start_x = (self.WIDTH - total_w) // 2
        y = self.HEIGHT - self.CONTROL_BAR_HEIGHT + (self.CONTROL_BAR_HEIGHT - self.BTN_SIZE) // 2
        self._buttons = []
        x = start_x
        for action, tip in labels:
            rect = pygame.Rect(x, y, self.BTN_SIZE, self.BTN_SIZE)
            self._buttons.append(_Button(rect, action, tip))
            x += self.BTN_SIZE + self.BTN_GAP

    def load_playback(
        self,
        frames: List[Dict[str, str]],
        turn_events: Dict[int, List[str]],
        max_turn: int,
    ) -> None:
        self.frames = frames
        self.turn_events = turn_events
        self.max_turn = max_turn
        self.current_turn = 0
        if self.frames:
            self.drone_positions = dict(self.frames[0])

    def run_playback(self) -> None:
        while self._running:
            if self.frames:
                idx = min(self.current_turn, len(self.frames) - 1)
                self.drone_positions = dict(self.frames[idx])
            self._process_events()
            self.render()
            self.clock.tick(60)

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._on_click(event.pos)

    def _on_key(self, key: int) -> None:
        if key in (pygame.K_RIGHT, pygame.K_SPACE):
            self._step_forward()
        elif key == pygame.K_LEFT:
            self._step_back()
        elif key == pygame.K_HOME:
            self._go_first()
        elif key == pygame.K_END:
            self._go_last()
        elif key == pygame.K_c:
            self._toggle_cost_overlay()

    def _toggle_cost_overlay(self) -> None:
        self.show_cost_overlay = not self.show_cost_overlay

    def _on_click(self, pos: Tuple[int, int]) -> None:
        for btn in self._buttons:
            if btn.rect.collidepoint(pos):
                if btn.action == "first":
                    self._go_first()
                elif btn.action == "prev":
                    self._step_back()
                elif btn.action == "next":
                    self._step_forward()
                elif btn.action == "last":
                    self._go_last()
                return

    def _go_first(self) -> None:
        self.current_turn = 0

    def _go_last(self) -> None:
        self.current_turn = self.max_turn

    def _step_back(self) -> None:
        self.current_turn = max(0, self.current_turn - 1)

    def _step_forward(self) -> None:
        self.current_turn = min(self.max_turn, self.current_turn + 1)

    def _quit(self) -> None:
        self._running = False
        pygame.quit()
        sys.exit(0)

    def _calculate_bounds(self) -> None:
        if not self.network.zones:
            self.min_x = self.min_y = 0
            self.range_x = self.range_y = 1
            self.scale = 1.0
            return

        xs = [z.x for z in self.network.zones.values()]
        ys = [z.y for z in self.network.zones.values()]
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)

        self.range_x = max(self.max_x - self.min_x, 1)
        self.range_y = max(self.max_y - self.min_y, 1)

        draw_w = self.WIDTH - 2 * self.PADDING
        draw_h = self.graph_height - 2 * self.PADDING
        self.scale = min(draw_w / self.range_x, draw_h / self.range_y)

    def _to_screen(self, x: int, y: int) -> Tuple[int, int]:
        screen_x = self.PADDING + (x - self.min_x) * self.scale
        screen_y = self.PADDING + (y - self.min_y) * self.scale
        return (int(screen_x), int(screen_y))

    def _connection_midpoint(self, conn_label: str) -> Optional[Tuple[int, int]]:
        if "-" not in conn_label:
            return None
        parts = conn_label.split("-", 1)
        if len(parts) != 2:
            return None
        z0, z1 = parts[0], parts[1]
        if z0 not in self.network.zones or z1 not in self.network.zones:
            return None
        a = self.network.zones[z0]
        b = self.network.zones[z1]
        ax, ay = self._to_screen(a.x, a.y)
        bx, by = self._to_screen(b.x, b.y)
        return ((ax + bx) // 2, (ay + by) // 2)

    def _draw_connections(self) -> None:
        for conn in self.network.connections:
            start = self._to_screen(conn.zone_a.x, conn.zone_a.y)
            end = self._to_screen(conn.zone_b.x, conn.zone_b.y)
            pygame.draw.line(self.screen, self.CONN_COLOR, start, end, 2)

            if conn.max_link_capacity > 1:
                mid_x, mid_y = (start[0] + end[0]) // 2, (start[1] + end[1]) // 2
                self._blit_text(
                    f"C:{conn.max_link_capacity}",
                    (mid_x, mid_y),
                    13,
                    self.TEXT_COLOR,
                    center=True,
                )

    def _draw_hubs(self) -> None:
        for zone in self.network.zones.values():
            pos = self._to_screen(zone.x, zone.y)

            color: Tuple[int, int, int] | pygame.Color = self.DEFAULT_HUB_COLOR
            if zone.color:
                try:
                    color = pygame.Color(zone.color)
                except ValueError:
                    pass

            radius = 20
            if zone.z_type == ZoneType.RESTRICTED:
                pygame.draw.circle(self.screen, (255, 50, 50), pos, radius + 4, 2)
            elif zone.z_type == ZoneType.PRIORITY:
                pygame.draw.circle(self.screen, (50, 255, 50), pos, radius + 4, 2)

            pygame.draw.circle(self.screen, color, pos, radius)

            self._blit_text(zone.name, (pos[0], pos[1] + 28), 14,
                            self.TEXT_COLOR, bold=True, center=True)

            # Stack optional overlay labels above the hub, closest first, so
            # they never sit on top of each other regardless of which are on.
            overlay_y = pos[1] - 36
            if zone.max_drones > 1:
                self._blit_text(
                    f"max {zone.max_drones}",
                    (pos[0], overlay_y),
                    12,
                    (180, 180, 200),
                    center=True,
                )
                overlay_y -= 16

            if self.show_cost_overlay and zone.name in self.zone_costs:
                cost = self.zone_costs[zone.name]
                cost_text = "inf" if cost == float("inf") else f"F:{cost:g}"
                self._blit_text(
                    cost_text,
                    (pos[0], overlay_y),
                    12,
                    (255, 210, 120),
                    bold=True,
                    center=True,
                )

    def _drone_cluster_radius(self, count: int) -> int:
        """Shrink drone radius as more drones stack on the same hub/connection.

        Keeps large clusters (e.g. 25 drones sharing a start/end hub) visually
        bounded instead of growing without limit.
        """
        if count <= 6:
            return 16
        if count <= 12:
            return 12
        if count <= 20:
            return 9
        return 7

    def _cluster_offsets(self, count: int, spacing: int) -> List[Tuple[int, int]]:
        """Bounded grid layout (roughly square) centered on the hub position.

        Replaces a naive single-column vertical stack, which pushes drones
        off-screen once more than ~9 of them share the same location (e.g.
        the challenger map's 25-drone start/end hubs).
        """
        cols = max(1, math.ceil(math.sqrt(count)))
        rows = math.ceil(count / cols)
        offsets = []
        for i in range(count):
            row, col = divmod(i, cols)
            offset_x = (col - (cols - 1) / 2) * spacing
            offset_y = (row - (rows - 1) / 2) * spacing
            offsets.append((int(offset_x), int(offset_y)))
        return offsets

    def _draw_drones(self) -> None:
        groups: Dict[str, List[str]] = {}
        for d_id, location in self.drone_positions.items():
            groups.setdefault(location, []).append(d_id)

        for location, d_ids in groups.items():
            if location in self.network.zones:
                zone = self.network.zones[location]
                pos = self._to_screen(zone.x, zone.y)
            else:
                mid = self._connection_midpoint(location)
                if mid is None:
                    continue
                pos = mid

            count = len(d_ids)
            radius = self._drone_cluster_radius(count)
            spacing = radius * 2 + 3
            offsets = self._cluster_offsets(count, spacing)

            for d_id, (dx, dy) in zip(d_ids, offsets):
                cx, cy = pos[0] + dx, pos[1] + dy

                pygame.draw.circle(self.screen, self.DRONE_RING, (cx, cy), radius + 2)
                pygame.draw.circle(self.screen, self.DRONE_FILL, (cx, cy), radius)
                pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), radius, width=2)

                number = drone_display_number(d_id)
                font_size = min(20 if len(number) <= 2 else 16, radius + 4)
                self._blit_text(
                    number,
                    (cx, cy),
                    font_size,
                    (20, 20, 30),
                    bold=True,
                    center=True,
                    outline=(255, 255, 255),
                    outline_width=2,
                )

    def _draw_button_icon(self, btn: _Button) -> None:
        color = self.BTN_ACTIVE if btn.hovered else self.BTN_COLOR
        pygame.draw.rect(self.screen, color, btn.rect, border_radius=8)
        pygame.draw.rect(self.screen, self.ACCENT, btn.rect, width=2, border_radius=8)

        cx, cy = btn.rect.centerx, btn.rect.centery
        s = 10
        if btn.action == "first":
            left = btn.rect.left
            pygame.draw.polygon(
                self.screen,
                self.TEXT_COLOR,
                [(left + 14, cy), (left + 14 + s, cy - s), (left + 14 + s, cy + s)],
            )
            pygame.draw.polygon(
                self.screen,
                self.TEXT_COLOR,
                [(left + 26, cy), (left + 26 + s, cy - s), (left + 26 + s, cy + s)],
            )
            pygame.draw.rect(self.screen, self.TEXT_COLOR, (left + 12, cy - 2, 4, 4))
        elif btn.action == "prev":
            pygame.draw.polygon(
                self.screen,
                self.TEXT_COLOR,
                [(cx - s // 2, cy), (cx + s // 2, cy - s), (cx + s // 2, cy + s)],
            )
        elif btn.action == "next":
            pygame.draw.polygon(
                self.screen,
                self.TEXT_COLOR,
                [(cx + s // 2, cy), (cx - s // 2, cy - s), (cx - s // 2, cy + s)],
            )
        elif btn.action == "last":
            right = btn.rect.right
            pygame.draw.polygon(
                self.screen,
                self.TEXT_COLOR,
                [(right - 14, cy), (right - 14 - s, cy - s), (right - 14 - s, cy + s)],
            )
            pygame.draw.polygon(
                self.screen,
                self.TEXT_COLOR,
                [(right - 26, cy), (right - 26 - s, cy - s), (right - 26 - s, cy + s)],
            )
            pygame.draw.rect(self.screen, self.TEXT_COLOR, (right - 16, cy - 2, 4, 4))

    def _draw_control_bar(self) -> None:
        bar = pygame.Rect(0, self.graph_height, self.WIDTH, self.CONTROL_BAR_HEIGHT)
        pygame.draw.rect(self.screen, self.BAR_COLOR, bar)
        pygame.draw.line(self.screen, self.ACCENT, (0, self.graph_height),
                         (self.WIDTH, self.graph_height), 2)

        mx, my = pygame.mouse.get_pos()
        for btn in self._buttons:
            btn.hovered = btn.rect.collidepoint(mx, my)
            self._draw_button_icon(btn)

        self._blit_text(
            f"Turn {self.current_turn} / {self.max_turn}",
            (24, self.graph_height + 10),
            16,
            self.TEXT_COLOR,
            bold=True,
        )

        events = self.turn_events.get(self.current_turn, [])
        if events:
            move_text = "  ".join(events)
        elif self.current_turn == 0:
            move_text = "(initial positions)"
        else:
            move_text = "(no movement this turn)"
        self._blit_text(move_text[:90], (24, self.graph_height + 34), 13, (160, 170, 190))

        if self.max_turn > 0:
            progress = self.current_turn / self.max_turn
            track = pygame.Rect(24, self.HEIGHT - 14, self.WIDTH - 48, 6)
            fill = pygame.Rect(track.x, track.y, int(track.w * progress), track.h)
            pygame.draw.rect(self.screen, (50, 50, 70), track, border_radius=3)
            pygame.draw.rect(self.screen, self.ACCENT, fill, border_radius=3)

        hint = "← → step   Home/End   Space = forward   C = toggle F cost"
        hint_surf = render_text(hint, 12, (120, 130, 150))
        self.screen.blit(
            hint_surf,
            (self.WIDTH -
             hint_surf.get_width() -
             24,
             self.graph_height +
             10))

        cost_state = "ON" if self.show_cost_overlay else "OFF"
        cost_color = (255, 210, 120) if self.show_cost_overlay else (120, 130, 150)
        self._blit_text(
            f"F cost: {cost_state}",
            (self.WIDTH - 140, self.graph_height + 34),
            13,
            cost_color,
            bold=self.show_cost_overlay,
        )

    def render(self) -> None:
        graph_rect = pygame.Rect(0, 0, self.WIDTH, self.graph_height)
        self.screen.set_clip(graph_rect)
        self.screen.fill(self.BG_COLOR)
        self._draw_connections()
        self._draw_hubs()
        self._draw_drones()
        self.screen.set_clip(None)

        self._draw_control_bar()
        pygame.display.flip()

    def update(self, drone_positions: Dict[str, str]) -> None:
        self.drone_positions = drone_positions
        self._process_events()
        self.render()
