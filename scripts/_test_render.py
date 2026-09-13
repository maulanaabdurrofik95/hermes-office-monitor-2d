#!/usr/bin/env python
"""Headless render test: open window via dummy driver, render one frame,
save screenshot, exit. Verifies app runs without crash.
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import sys
import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# import the app module
import office_monitor as om

pygame.init()
screen = pygame.display.set_mode((om.WIDTH, om.HEIGHT))
pygame.display.set_caption("Hermes Office Monitor")
clock = pygame.time.Clock()

font = pygame.font.SysFont("segoeui", 30, bold=True)
font_small = pygame.font.SysFont("segoeui", 16, bold=True)
font_tiny = pygame.font.SysFont("segoeui", 14)

agents = {k: om.AgentData(k) for k in om.AGENT_ORDER}

# geometry (mirror main)
margin = 8
inner_gap = 8
room_w = (om.WIDTH // 2 - margin - inner_gap) // 2
top_h = 292
room_h = (top_h - margin - inner_gap) // 2

room_dev = (margin, margin, room_w, room_h)
room_fe  = (margin + room_w + inner_gap, margin, room_w, room_h)
room_sec = (margin, margin + room_h + inner_gap, room_w, room_h)
room_dsg = (margin + room_w + inner_gap, margin + room_h + inner_gap, room_w, room_h)
hall = (room_w + margin + inner_gap + 4, margin + 4,
        om.WIDTH - 2 * (room_w + margin + inner_gap) - 8,
        room_h * 2 + inner_gap - 8)

def center(r):
    return (r[0] + r[2] // 2, r[1] + r[3] // 2)

desk_pos = {
    "dev": center(room_dev),
    "frontend": center(room_fe),
    "security": center(room_sec),
    "design": center(room_dsg),
    "hermes": (center(hall)[0], center(hall)[1] - 6),
}

frame = 0
# Render several frames to exercise blink/typing animations
for frame in range(1, 250):
    screen.fill(om.WALL)
    om.draw_room(screen, room_dev, "DEV", om.AGENT_COLORS["dev"], font_small, frame)
    om.draw_room(screen, room_fe, "FRONTEND", om.AGENT_COLORS["frontend"], font_small, frame)
    om.draw_room(screen, room_sec, "SECURITY", om.AGENT_COLORS["security"], font_small, frame)
    om.draw_room(screen, room_dsg, "DESIGN", om.AGENT_COLORS["design"], font_small, frame)
    om.draw_hallway(screen, hall, font_small, frame)

    blink = (frame // 110) % 6 == 0
    for key in om.AGENT_ORDER:
        ad = agents[key]
        cx, cy = desk_pos[key]
        typing = (ad.stage == "working") and (frame // 4) % 2 == 0
        mtype = "big" if key == "hermes" else "laptop"
        om.draw_chibi(screen, cx, cy, om.AGENT_COLORS[key], ad.stage,
                      blink, typing, frame, monitor_type=mtype)
        icon_x, icon_y = cx, cy - 78
        bob = int((frame // 10) % 2) if ad.stage == "working" else 0
        om.status_icon(screen, ad.stage, icon_x, icon_y, scale=1.0, bob=bob)
        om.draw_text(screen, font_tiny, om.AGENT_NAMES[key],
                     (60, 60, 70), cx, cy + 8, center_x=True)

    # bottom bar
    om.draw_text(screen, font_small,
                 "Hermes Office Monitor — headless test frame " + str(frame),
                 om.TEXT_DIM, 12, om.HEIGHT - 17, center_y=True)

    clock.tick(om.FPS)

# detail panel test
om.draw_detail_panel(screen, agents["dev"], font, font_small, font_tiny,
                     om.WIDTH - 330, 40, 316, om.HEIGHT - 90, frame)

# save screenshot
os.makedirs("screenshots", exist_ok=True)
pygame.image.save(screen, "screenshots/preview.png")
print("OK: screenshot saved to screenshots/preview.png")
pygame.quit()
