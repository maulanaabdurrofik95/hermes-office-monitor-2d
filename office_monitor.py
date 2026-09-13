#!/usr/bin/env python
"""office_monitor.py — Hermes Office Monitor (Pygame local, 2D top-down).

Virtual office: 5 pixel-chibi agents (Dev, Frontend, Security, Design, Hermes)
sitting at desks with computers/laptops. Live-polls data/<agent>.json every
2 seconds. Click a character to open a detail panel.

Run:
    python office_monitor.py

Stdlib + pygame only.
"""

from __future__ import annotations
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "")  # allow headless override via env
import pygame

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 980, 640
FPS = 60
POLL_INTERVAL = 2.0           # seconds

FLOOR   = (244, 241, 234)     # #F4F1EA
WALL    = (216, 211, 199)
PANEL_BG= (46, 50, 60)        # detail panel background
PANEL_BG_ALT = (58, 62, 74)
TEXT    = (250, 250, 250)
TEXT_DIM= (200, 200, 200)
ACCENT  = (255, 215, 0)       # Hermes gold

AGENT_COLORS = {
    "dev":       (74, 144, 217),    # #4A90D9
    "frontend": (155, 89, 182),     # #9B59B6
    "security": (231, 76, 60),      # #E74C3C
    "design":   (243, 156, 18),     # #F39C12
    "hermes":   (255, 215, 0),      # #FFD700
}

AGENT_NAMES = {
    "dev":       "Dev",
    "frontend":  "Frontend",
    "security":  "Security",
    "design":    "Design",
    "hermes":    "Hermes",
}

AGENT_ORDER = ["hermes", "dev", "frontend", "security", "design"]

SKIN  = (244, 194, 154)   # #F4C29A
SKIN_D= (224, 169, 122)   # darker skin edge
HAIR  = (44, 62, 80)      # #2C3E50
PANTS = (60, 70, 90)

# Desk/computer colors
DESK  = (150, 110, 80)
DESK_LIGHT = (176, 132, 96)
LAPTOP_SCREEN = (120, 150, 200)
LAPTOP_KEY   = (90, 100, 110)
MONITOR_BODY = (70, 75, 90)
MONITOR_SCREEN = (40, 60, 90)
KEYBOARD   = (60, 66, 76)

STATUS_COLORS = {
    "working": (46, 204, 113),   # green
    "revisi":  (231, 76, 60),    # red
    "antre":   (241, 196, 15),   # yellow
    "queue":   (241, 196, 15),
    "idle":    (149, 165, 166),  # grey
    "done":    (46, 204, 113),   # green
    "selesai": (46, 204, 113),
}

# Canonicalise stage aliases -> canonical
STAGE_CANON = {
    "working": "working",
    "revisi":  "revisi",
    "queue":   "antre",
    "antre":   "antre",
    "idle":    "idle",
    "done":    "selesai",
    "selesai": "selesai",
    "in-review": "working",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------
class AgentData:
    def __init__(self, key: str):
        self.key = key
        self.stage = "idle"
        self.tasks: list[str] = []
        self.note = ""
        self.updated_at = ""
        self.mtime = 0.0
        self.path = os.path.join(DATA_DIR, f"{key}.json")
        self.load()

    def load(self) -> bool:
        try:
            mt = os.path.getmtime(self.path)
        except OSError:
            return False
        if mt == self.mtime:
            return False                     # unchanged
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False
        self.mtime = mt
        self.stage = STAGE_CANON.get(str(obj.get("stage", "idle")), "idle")
        self.tasks = list(obj.get("tasks", []) or [])
        self.note = str(obj.get("note", ""))
        self.updated_at = str(obj.get("updatedAt", ""))
        return True

    def stage_color(self):
        return STATUS_COLORS.get(self.stage, (149, 165, 166))

    def stage_label(self):
        return self.stage.upper()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def rect(s, color, x, y, w, h):
    pygame.draw.rect(s, color, (int(x), int(y), int(w), int(h)))


def circle(s, color, x, y, r):
    pygame.draw.circle(s, color, (int(x), int(y)), int(r))


def draw_text(s, font, text, color, x, y, center_x=False, center_y=False):
    img = font.render(text, True, color)
    r = img.get_rect()
    if center_x:
        r.centerx = int(x)
    else:
        r.x = int(x)
    if center_y:
        r.centery = int(y)
    else:
        r.y = int(y)
    s.blit(img, r)


def status_icon(s, stage, x, y, scale=1.0, bob=0.0):
    """Draw status icon above head using primitives (no emoji)."""
    c = STATUS_COLORS.get(stage, (149, 165, 166))
    y = y + bob
    r = int(6 * scale)
    if stage == "working":
        # gear
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            rect(s, c, x + dx * r - 2, y + dy * r - 2, 4, 4)
        circle(s, c, x, y, r)
        circle(s, FLOOR, x, y, int(r * 0.6))
    elif stage == "revisi":
        # triangle with !
        tri = [(x, y - r), (x - r, y + r), (x + r, y + r)]
        pygame.draw.polygon(s, c, tri)
        rect(s, TEXT, x - 1, y - r * 0.5, 2, int(r * 0.8))
        circle(s, TEXT, x, y + r * 0.35, int(r * 0.28))
    elif stage in ("antre", "queue"):
        # coffee cup
        rect(s, c, x - r, y - r, int(r * 1.6), int(r * 1.2))
        rect(s, c, x + int(r * 0.6), y - int(r * 0.7), int(r * 0.5), int(r * 0.6))
        rect(s, TEXT, x - int(r * 0.7), y - int(r * 0.5), int(r * 0.4), int(r * 0.2))
        rect(s, TEXT, x - int(r * 0.7), y - int(r * 0.1), int(r * 0.4), int(r * 0.2))
    elif stage in ("selesai", "done"):
        # check mark
        pygame.draw.lines(s, c, False, [
            (x - r, y), (x - r * 0.3, y + r * 0.6), (x + r, y - r * 0.6)
        ], max(2, int(2 * scale)))
    else:  # idle
        # relaxing cup / moon
        circle(s, c, x - int(r * 0.6), y, int(r * 0.6))
        rect(s, c, x + int(r * 0.1), y - int(r * 0.4), int(r), int(r * 0.8))
        rect(s, c, x + int(r * 0.9), y - int(r * 0.2), int(r * 0.5), int(r * 0.5))


# ---------------------------------------------------------------------------
# Character drawing
# ---------------------------------------------------------------------------
def draw_chibi(s, x, y, color, stage, blink, typing, frame,
               monitor_type="laptop"):
    """Draw a top-down-ish pixel-chibi at desk with a computer.

    x,y = desk center. Character sits "behind" (upper part of desk facing
    the computer at the bottom/center).
    """
    bob = 0
    if typing:
        bob = 1
    elif not blink:
        bob = -1

    # ---- desk (top-down: rectangle with darker edge) ----
    desk_w, desk_h = 118, 74
    dx = x - desk_w // 2
    dy = y - desk_h // 2
    # shadow
    rect(s, (200, 194, 182), dx + 4, dy + 4, desk_w, desk_h)
    rect(s, DESK, dx, dy, desk_w, desk_h)
    rect(s, DESK_LIGHT, dx, dy, desk_w, 6)
    rect(s, DESK_LIGHT, dx, dy, 6, desk_h)

    # ---- computer ----
    if monitor_type == "big":
        # large monitor + keyboard (Hermes)
        mw, mh = 56, 34
        mx = x - mw // 2
        my = dy + desk_h // 2 - 44
        # stand
        rect(s, MONITOR_BODY, x - 6, my + mh - 4, 12, 8)
        # body
        rect(s, MONITOR_BODY, mx, my, mw, mh)
        # screen
        scr = LAPTOP_SCREEN if stage == "working" else (50, 70, 105)
        rect(s, scr, mx + 3, my + 3, mw - 6, mh - 6)
        if stage == "working":
            # blinking cursor on screen
            if frame % 60 < 30:
                rect(s, TEXT, mx + 6 + (frame // 20) % 6, my + 10, 2, 5)
        # keyboard
        kb_y = my + mh + 4
        rect(s, KEYBOARD, x - 28, kb_y, 56, 8)
        for i in range(7):
            rect(s, (90, 100, 110), x - 24 + i * 7, kb_y + 2, 4, 4)
    else:
        # laptop (open, keyboard toward user)
        base_w = 60
        base_h = 9
        bx = x - base_w // 2
        by = dy + desk_h // 2 - 12
        # keyboard base
        rect(s, LAPTOP_KEY, bx, by, base_w, base_h)
        for i in range(8):
            rect(s, (110, 120, 132), bx + 3 + i * 7, by + 2, 4, 4)
        # screen tilts up (draw as taller block)
        sw, sh = 52, 26
        sx = x - sw // 2
        sy = by - sh + 2
        scr = LAPTOP_SCREEN if stage == "working" else (50, 70, 105)
        rect(s, (60, 70, 90), sx, sy, sw, sh)
        rect(s, scr, sx + 2, sy + 2, sw - 4, sh - 4)
        if stage == "working":
            if frame % 60 < 30:
                rect(s, TEXT, sx + 5, sy + 8, 2, 4)

    # ---- hands / arms depending on typing ----
    # hands come from lower-left/lower-right toward keyboard
    hand_y = dy + desk_h // 2 - 8 + bob
    if typing:
        # hands move back and forth (typing animation)
        off = int((frame // 6) % 3) * 2 - 2
        rect(s, SKIN, x - 26 + off, hand_y, 7, 6)
        rect(s, SKIN, x + 19 - off, hand_y, 7, 6)
    else:
        rect(s, SKIN, x - 26, hand_y, 7, 6)
        rect(s, SKIN, x + 19, hand_y, 7, 6)

    # ---- body (upper body / torso, drawn behind desk edge) ----
    body_w, body_h = 34, 26
    body_x = x - body_w // 2
    body_y = dy + desk_h // 2 - body_h - 14
    rect(s, (200, 194, 182), body_x + 2, body_y + body_h, body_w, 6)  # shadow
    rect(s, color, body_x, body_y, body_w, body_h)
    # shirt shading
    darker = tuple(max(0, v - 35) for v in color)
    rect(s, darker, body_x, body_y, body_w, 4)

    # ---- head ----
    hw, hh = 30, 22
    hx = x - hw // 2
    hy = body_y - hh + 4
    if blink:
        # eyes closed -> short lids
        rect(s, SKIN_D, hx, hy, hw, hh)           # outline (draw beneath)
        rect(s, SKIN, hx + 1, hy + 1, hw - 2, hh - 2)
        rect(s, HAIR, hx, hy, hw, 5)
        rect(s, HAIR, hx, hy, 4, hh)
        rect(s, HAIR, hx + hw - 4, hy, 4, hh)
        # closed eyes (lines)
        rect(s, HAIR, hx + 5, hy + 10, 6, 2)
        rect(s, HAIR, hx + hw - 11, hy + 10, 6, 2)
    else:
        rect(s, SKIN_D, hx, hy, hw, hh)
        rect(s, SKIN, hx + 1, hy + 1, hw - 2, hh - 2)
        # hair top
        rect(s, HAIR, hx, hy, hw, 6)
        rect(s, HAIR, hx, hy + 1, 5, hh)
        rect(s, HAIR, hx + hw - 5, hy + 1, 5, hh)
        # eyes
        rect(s, HAIR, hx + 6, hy + 9, 5, 5)
        rect(s, HAIR, hx + hw - 11, hy + 9, 5, 5)
        # mouth
        rect(s, SKIN_D, hx + hw // 2 - 2, hy + hh - 6, 4, 2)

    # ---- accessories per domain ----
    if color == AGENT_COLORS["dev"]:
        # headphones band + laptop headphone cups on desk
        rect(s, HAIR, hx + 2, hy - 3, hw - 4, 3)
        rect(s, HAIR, hx - 1, hy, 3, 8)
        rect(s, HAIR, hx + hw - 2, hy, 3, 8)
    elif color == AGENT_COLORS["frontend"]:
        # palette + brush on desk corner
        px, py = dx + 4, dy + desk_h - 18
        circle(s, (46, 204, 113), px + 6, py + 6, 7)
        circle(s, (231, 76, 60), px + 4, py + 4, 3)
        circle(s, (52, 152, 219), px + 9, py + 8, 3)
        rect(s, (120, 90, 50), px + 16, py + 3, 2, 12)
        rect(s, (90, 70, 40), px + 16, py + 3, 2, 4)
    elif color == AGENT_COLORS["security"]:
        # shield on desk
        sh_x, sh_y = dx + 8, dy + 8
        pts = [(sh_x + 8, sh_y), (sh_x + 16, sh_y + 3),
               (sh_x + 16, sh_y + 12), (sh_x + 8, sh_y + 18),
               (sh_x, sh_y + 12), (sh_x, sh_y + 3)]
        pygame.draw.polygon(s, (52, 152, 219), pts)
        rect(s, TEXT, sh_x + 6, sh_y + 6, 4, 6)
        rect(s, TEXT, sh_x + 6, sh_y + 6, 8, 2)
    elif color == AGENT_COLORS["design"]:
        # pencil + ruler on desk
        px, py = dx + 8, dy + desk_h - 16
        rect(s, (46, 204, 113), px, py, 16, 3)
        rect(s, (255, 255, 255), px + 14, py - 1, 2, 5)
        rect(s, (243, 156, 18), px + 16, py, 2, 3)
        rect(s, (255, 255, 255), px + 22, py - 1, 14, 4)
        for i in range(5):
            rect(s, (120, 120, 120), px + 24 + i * 2, py, 1, 2)
    elif color == AGENT_COLORS["hermes"]:
        # headset + larger monitor already handled by monitor_type big
        rect(s, HAIR, hx - 2, hy + 2, 3, 10)
        rect(s, HAIR, hx + hw - 1, hy + 2, 3, 10)
        rect(s, HAIR, hx - 2, hy + 4, hw + 4, 3)

    # ---- name plate ----
    rect(s, (255, 255, 255, 0), x - 28, dy + desk_h - 2, 56, 2)  # desk front edge


def draw_room(s, rect_, title, color, font_small, frame):
    x, y, w, h = rect_
    # floor
    rect(s, FLOOR, x, y, w, h)
    # subtle floor pattern
    for fx in range(x + 20, x + w, 40):
        rect(s, (238, 235, 227), fx, y + 8, 2, h - 16)
    for fy in range(y + 20, y + h, 40):
        rect(s, (238, 235, 227), x + 8, fy, w - 16, 2)
    # border
    pygame.draw.rect(s, WALL, rect_, 3)
    # room title tag
    tag_w = 70
    tag_h = 22
    rect(s, color, x + 8, y + 6, tag_w, tag_h)
    draw_text(s, font_small, title, TEXT, x + 8 + tag_w // 2, y + 6 + tag_h // 2,
              center_x=True, center_y=True)


def draw_hallway(s, rect_, font_small, frame):
    x, y, w, h = rect_
    rect(s, (232, 228, 219), x, y, w, h)
    # carpet stripes
    for fx in range(x, x + w, 36):
        rect(s, (225, 220, 210), fx, y, 2, h)
    pygame.draw.rect(s, WALL, rect_, 3)


def draw_detail_panel(s, agent_data: AgentData, font, font_small, font_tiny,
                      x, y, w, h, frame):
    """Right-side overlay panel with agent info."""
    rect(s, PANEL_BG, x, y, w, h)
    pygame.draw.rect(s, ACCENT, (x, y, w, 4))
    name = AGENT_NAMES.get(agent_data.key, agent_data.key)
    color = AGENT_COLORS.get(agent_data.key, (150, 150, 150))

    draw_text(s, font, name, color, x + 16, y + 18)
    draw_text(s, font_small, f"Status: {agent_data.stage_label()}",
              agent_data.stage_color(), x + 16, y + 50)
    # stage bar
    rect(s, (60, 64, 76), x + 16, y + 72, w - 32, 8)
    bar_w = int((w - 32) * 0.6)
    rect(s, agent_data.stage_color(), x + 16, y + 72, bar_w, 8)

    yy = y + 100
    # tasks
    draw_text(s, font_small, "TASKS", TEXT_DIM, x + 16, yy)
    yy += 26
    if not agent_data.tasks:
        draw_text(s, font_tiny, "- tidak ada tugas -", TEXT_DIM, x + 16, yy)
        yy += 22
    for t in agent_data.tasks:
        # bullet
        circle(s, color, x + 22, yy + 8, 4)
        # wrap text
        tw = font_tiny.size(t)[0]
        if tw > w - 60:
            # simple wrap
            mid = int(len(t) * (w - 60) / tw)
            parts = [t[:mid], t[mid:]]
        else:
            parts = [t]
        for p in parts:
            draw_text(s, font_tiny, p, TEXT, x + 36, yy)
            yy += 22
        yy += 2

    yy += 12
    # note
    draw_text(s, font_small, "NOTE", TEXT_DIM, x + 16, yy)
    yy += 24
    note = agent_data.note or "-"
    nw = font_tiny.size(note)[0]
    if nw > w - 40:
        mid = int(len(note) * (w - 40) / nw)
        for p in (note[:mid], note[mid:]):
            draw_text(s, font_tiny, p, TEXT, x + 16, yy)
            yy += 22
    else:
        draw_text(s, font_tiny, note, TEXT, x + 16, yy)
        yy += 22

    yy += 8
    draw_text(s, font_tiny, f"Updated: {agent_data.updated_at}",
              TEXT_DIM, x + 16, yy)
    draw_text(s, font_tiny, "ESC / klik X untuk tutup", (120, 130, 150),
              x + 16, y + h - 24)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Hermes Office Monitor")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    try:
        font = pygame.font.SysFont("segoeui", 30, bold=True)
        font_small = pygame.font.SysFont("segoeui", 16, bold=True)
        font_tiny = pygame.font.SysFont("segoeui", 14)
    except Exception:
        font = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 18)
        font_tiny = pygame.font.Font(None, 15)

    agents = {k: AgentData(k) for k in AGENT_ORDER}
    selected = None          # agent key
    hover = None             # agent key under mouse
    last_poll = 0.0
    frame = 0

    # room geometry (leaving center hallway for Hermes lobby)
    margin = 8
    inner_gap = 8
    top_h = 300
    mid_w = 500
    bot_h = HEIGHT - top_h - margin - 34   # reserve bottom bar
    top_h = 292
    bot_h = HEIGHT - top_h - margin - 40

    room_w = (mid_w - margin - inner_gap) // 2
    room_h = (top_h - margin - inner_gap) // 2

    # 4 corner rooms
    room_dev = (margin, margin, room_w, room_h)
    room_fe  = (margin + room_w + inner_gap, margin, room_w, room_h)
    room_sec = (margin, margin + room_h + inner_gap, room_w, room_h)
    room_dsg = (margin + room_w + inner_gap, margin + room_h + inner_gap, room_w, room_h)

    # center hallway / lobby
    hall = (room_w + margin + inner_gap + 4, margin + 4,
            mid_w - 2 * (room_w + margin + inner_gap) - 8,
            room_h * 2 + inner_gap - 8)

    # desk positions (center of each room)
    def center(r):
        return (r[0] + r[2] // 2, r[1] + r[3] // 2)

    desk_pos = {
        "dev":       center(room_dev),
        "frontend":  center(room_fe),
        "security":  center(room_sec),
        "design":    center(room_dsg),
        "hermes":    center(hall),
    }
    # Hermes desk: shift up so monitor fits in lobby
    hx, hy = desk_pos["hermes"]
    desk_pos["hermes"] = (hx, hy - 6)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        frame += 1

        # ---- poll data every 2s ----
        now = pygame.time.get_ticks() / 1000.0
        if now - last_poll >= POLL_INTERVAL:
            last_poll = now
            for a in agents.values():
                a.load()

        # ---- events ----
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    selected = None
                elif ev.key == pygame.K_j:
                    selected = AGENT_ORDER[(AGENT_ORDER.index(
                        selected if selected else "hermes") + 1) % 5]
                elif ev.key == pygame.K_k:
                    selected = AGENT_ORDER[(AGENT_ORDER.index(
                        selected if selected else "hermes") - 1) % 5]
                elif ev.key == pygame.K_l:
                    selected = AGENT_ORDER[(AGENT_ORDER.index(
                        selected if selected else "hermes") + 1) % 5]
                elif ev.key == pygame.K_m:
                    selected = AGENT_ORDER[(AGENT_ORDER.index(
                        selected if selected else "hermes") + 1) % 5]
            elif ev.type == pygame.MOUSEMOTION:
                mx, my = ev.pos
                hover = None
                for key, (cx, cy) in desk_pos.items():
                    if abs(mx - cx) < 62 and abs(my - cy) < 42:
                        hover = key
                        break
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # close button on panel
                if selected:
                    px, py, pw, ph = (WIDTH - 330, 40, 316, HEIGHT - 90)
                    if (px + pw - 30 <= mx <= px + pw - 8 and
                            py + 6 <= my <= py + 26):
                        selected = None
                        continue
                for key, (cx, cy) in desk_pos.items():
                    if abs(mx - cx) < 62 and abs(my - cy) < 42:
                        selected = key
                        break

        # ---- draw ----
        screen.fill(WALL)

        draw_room(screen, room_dev, "DEV", AGENT_COLORS["dev"], font_small, frame)
        draw_room(screen, room_fe, "FRONTEND", AGENT_COLORS["frontend"], font_small, frame)
        draw_room(screen, room_sec, "SECURITY", AGENT_COLORS["security"], font_small, frame)
        draw_room(screen, room_dsg, "DESIGN", AGENT_COLORS["design"], font_small, frame)
        draw_hallway(screen, hall, font_small, frame)

        # highlight hovered room
        if hover:
            room_map = {"dev": room_dev, "frontend": room_fe,
                        "security": room_sec, "design": room_dsg,
                        "hermes": hall}
            r = room_map[hover]
            rect(screen, (0, 0, 0), r[0] - 2, r[1] - 2, r[2] + 4, r[3] + 4)  # shadow
            pygame.draw.rect(screen, ACCENT, r, 3)

        # ---- draw characters ----
        blink = (frame // 110) % 6 == 0      # blink briefly every ~110 frames
        for key in AGENT_ORDER:
            ad = agents[key]
            cx, cy = desk_pos[key]
            typing = (ad.stage == "working") and (frame // 4) % 2 == 0
            # determine monitor type: hermes big, others laptop
            mtype = "big" if key == "hermes" else "laptop"
            draw_chibi(screen, cx, cy, AGENT_COLORS[key], ad.stage,
                       blink, typing, frame, monitor_type=mtype)
            # status icon above head
            icon_x = cx
            icon_y = cy - 78
            # bob if working
            bob = 0
            if ad.stage == "working":
                bob = int((frame // 10) % 2)
            status_icon(screen, ad.stage, icon_x, icon_y, scale=1.0, bob=bob)
            # label
            draw_text(screen, font_tiny, AGENT_NAMES[key],
                      (60, 60, 70), cx, cy + 8, center_x=True)

        # ---- bottom bar ----
        bb_y = HEIGHT - 34
        rect(screen, PANEL_BG, 0, bb_y, WIDTH, 34)
        if hover:
            ad = agents[hover]
            name = AGENT_NAMES[hover]
            draw_text(screen, font_small, f"{name} — {ad.stage_label()}",
                      AGENT_COLORS[hover], 12, bb_y + 17, center_y=True)
        else:
            draw_text(screen, font_small,
                      "Hermes Office Monitor  |  klik karakter untuk detail  |  J/K pindah fokus",
                      TEXT_DIM, 12, bb_y + 17, center_y=True)
        draw_text(screen, font_tiny, "poll 2s", (120, 130, 150),
                  WIDTH - 12, bb_y + 17, center_x=True, center_y=True)

        # ---- detail panel ----
        if selected:
            px, py, pw, ph = (WIDTH - 330, 40, 316, HEIGHT - 90)
            draw_detail_panel(screen, agents[selected], font, font_small,
                              font_tiny, px, py, pw, ph, frame)
            # close X
            rect(screen, (200, 60, 60), px + pw - 30, py + 6, 24, 20)
            draw_text(screen, font_small, "X", TEXT, px + pw - 18, py + 16,
                      center_x=True, center_y=True)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()