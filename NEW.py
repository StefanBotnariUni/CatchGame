import pygame
import sys
import random
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# --------------------- init ---------------------
pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Polutio")

# Virtual game resolution
VIRTUAL_W, VIRTUAL_H = 1920, 1080
TOP_BAR_H = 96

# Real screen in fullscreen
def make_fullscreen():
    info = pygame.display.Info()
    return pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)

SCREEN = make_fullscreen()
SCREEN_W, SCREEN_H = SCREEN.get_size()

# We render everything to this surface, then scale to the real screen
GAME_SURF = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert_alpha()
CLOCK = pygame.time.Clock()
FPS = 60

# --------------------- fonts ---------------------
def font(size): return pygame.font.SysFont(None, size)
FONT_XL = font(96)
FONT_BIG = font(56)
FONT_MED = font(36)
FONT_SM = font(28)
FONT_TINY = font(20)

# --------------------- colors ---------------------
WHITE = (255, 255, 255)
BLACK = (12, 12, 12)
GRAY = (60, 60, 60)
GREEN = (60, 200, 90)
RED = (230, 70, 70)
YELLOW = (255, 210, 60)
BLUE = (80, 140, 255)
CYAN = (90, 230, 230)
MAGENTA = (220, 90, 220)
ORANGE = (255, 160, 60)
PURPLE = (150, 100, 220)
GOLD = (255, 215, 0)

# --------------------- powerups ---------------------
PU_MORE_TIME = "More time"
PU_LESS_TIME = "Less time"
PU_BIGGER_BASKET = "Bigger basket"
PU_LESS_PCT = "less percentage"
PU_MORE_PCT = "more percentage"
PU_DOUBLE_PCT = "double percentage"
PU_MAGNET = "magnet"
PU_STOPWATCH = "stop watch"

INSTANT_PUS = {PU_MORE_TIME, PU_LESS_TIME, PU_LESS_PCT, PU_MORE_PCT}
TIMED_PUS = {PU_BIGGER_BASKET, PU_DOUBLE_PCT, PU_MAGNET, PU_STOPWATCH}

POWERUP_ICONS: Dict[str, str] = {
    PU_MORE_TIME:      "pu_more_time.png",
    PU_LESS_TIME:      "pu_less_time.png",
    PU_BIGGER_BASKET:  "pu_bigger_basket.png",
    PU_LESS_PCT:       "pu_less_pct.png",
    PU_MORE_PCT:       "pu_more_pct.png",
    PU_DOUBLE_PCT:     "pu_double_pct.png",
    PU_MAGNET:         "pu_magnet.png",
    PU_STOPWATCH:      "pu_stopwatch.png",
}

# Printer image file, drawn below the top bar
PRINTER_IMAGE = "printer.png"
PRINTER_SIZE = (180, 140)

# --------------------- item assets (5 good + 5 bad) ---------------------
GOOD_ITEM_FILES = ["good1.png", "good2.png", "good3.png", "good4.png", "good5.png"]
BAD_ITEM_FILES  = ["bad1.png",  "bad2.png",  "bad3.png",  "bad4.png",  "bad5.png"]


_ITEM_IMG_CACHE: Dict[Tuple[str, Tuple[int,int]], Optional[pygame.Surface]] = {}

def get_item_image(path: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
    key = (path, size)
    if key in _ITEM_IMG_CACHE:
        return _ITEM_IMG_CACHE[key]
    if not path or not os.path.isfile(path):
        _ITEM_IMG_CACHE[key] = None
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        _ITEM_IMG_CACHE[key] = img
        return img
    except:
        _ITEM_IMG_CACHE[key] = None
        return None

# --------------------- utils ---------------------
def draw_text_center(text, font_obj, color, surf, cx, cy):
    img = font_obj.render(text, True, color)
    surf.blit(img, img.get_rect(center=(cx, cy)))

def load_image(path: str, size: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
    if not path or not os.path.isfile(path): return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.smoothscale(img, size)
        return img
    except:
        return None

# main menu background
MAIN_MENU_BG = "menu_bg.png"  # drop a 1920x1080 png next to the script
MAIN_MENU_BG_IMG = load_image(MAIN_MENU_BG, (VIRTUAL_W, VIRTUAL_H))

def safe_music_load_and_play(path: Optional[str]):
    try:
        if path and os.path.isfile(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.stop()
    except:
        pygame.mixer.music.stop()

def mouse_pos_virtual():
    mx, my = pygame.mouse.get_pos()
    vx = int(mx * VIRTUAL_W / SCREEN_W)
    vy = int(my * VIRTUAL_H / SCREEN_H)
    return vx, vy

# --------------------- data classes ---------------------
@dataclass
class BgStage:
    image_path: Optional[str] = None
    sound_path: Optional[str] = None
    fallback_color: Tuple[int, int, int] = (24, 24, 28)

@dataclass
class LevelConfig:
    name: str
    spawn_interval_ms: int
    fall_speed_range: Tuple[float, float]
    printer_speed: float
    good_prob: float
    max_items: int
    girl_speed: float
    item_size: Tuple[int, int]
    backgrounds: List[BgStage]
    time_limit_s: int = 60
    powerup_interval_ms: int = 2400
    powerup_drop_prob: float = 0.55
    powerup_duration_s: float = 6.0
    slowmo_factor: float = 0.45
    basket_expand_px: int = 120
    fall_scale_k: float = 1.0

# --------------------- levels ---------------------
LEVELS: List[LevelConfig] = [
    LevelConfig(
        name="Level 1 • Starter",
        spawn_interval_ms=650,
        fall_speed_range=(220, 360),
        printer_speed=360,
        good_prob=0.62,
        max_items=14,
        girl_speed=900,
        item_size=(50, 50),
        backgrounds=[
            BgStage("bg_0.png", "bg_40.mp3", (30, 30, 40)),
            BgStage("bg_20.png",  "bg_40.mp3",  (35,45,70)),
            BgStage("bg_40.png",  "bg_40.mp3",  (40,70,80)),
            BgStage("bg_60.png",  "bg_60.mp3",  (50,80,60)),
            BgStage("bg_80.png",  "bg_80.mp3",  (70,85,50)),
            BgStage("bg_100.png", "bg_100.mp3", (100,100,100)),
        ],
        time_limit_s=60,
        fall_scale_k=1.0
    ),
    LevelConfig(
        name="Level 2 • Rush",
        spawn_interval_ms=420,
        fall_speed_range=(320, 520),
        printer_speed=520,
        good_prob=0.5,
        max_items=18,
        girl_speed=1100,
        item_size=(50, 50),
        backgrounds=[
            BgStage("l2_bg_0.png",   "bg_40.mp3",   (28,20,28)),
            BgStage("l2_bg_20.png",  "bg_40.mp3",  (38,28,52)),
            BgStage("l2_bg_40.png",  "bg_40.mp3",  (52,38,70)),
            BgStage("l2_bg_60.png",  "bg_60.mp3",  (40,70,60)),
            BgStage("l2_bg_80.png",  "bg_80.mp3",  (60,88,40)),
            BgStage("l2_bg_100.png","bg_100.mp3", (110,110,110)),
        ],
        time_limit_s=75,
        powerup_interval_ms=2000,
        fall_scale_k=1.2
    ),
    # New Level 3
    LevelConfig(
        name="Level 3 • Storm",
        spawn_interval_ms=360,
        fall_speed_range=(360, 560),
        printer_speed=600,
        good_prob=0.5,
        max_items=20,
        girl_speed=1200,
        item_size=(50, 50),
        backgrounds=[
            BgStage("l3_bg_0.png",   "bg_40.mp3",   (22,26,34)),
            BgStage("l3_bg_20.png",  "bg_40.mp3",  (30,34,62)),
            BgStage("l3_bg_40.png",  "bg_40.mp3",  (44,54,82)),
            BgStage("l3_bg_60.png",  "bg_60.mp3",  (40,72,70)),
            BgStage("l3_bg_80.png",  "bg_80.mp3",  (70,90,52)),
            BgStage("l3_bg_100.png", "bg_100.mp3", (120,120,120)),
        ],
        time_limit_s=80,
        powerup_interval_ms=1900,
        fall_scale_k=1.3
    ),
    # New Level 4
    LevelConfig(
        name="Level 4 • Frenzy",
        spawn_interval_ms=300,
        fall_speed_range=(380, 640),
        printer_speed=720,
        good_prob=0.48,
        max_items=22,
        girl_speed=1300,
        item_size=(50, 50),
        backgrounds=[
            BgStage("l4_bg_0.png",   "bg_40.mp3",   (16,18,28)),
            BgStage("l4_bg_20.png",  "bg_40.mp3",  (28,26,58)),
            BgStage("l4_bg_40.png",  "bg_40.mp3",  (46,36,70)),
            BgStage("l4_bg_60.png",  "bg_60.mp3",  (44,70,66)),
            BgStage("l4_bg_80.png",  "bg_80.mp3",  (68,92,56)),
            BgStage("l4_bg_100.png", "bg_100.mp3", (140,140,140)),
        ],
        time_limit_s=85,
        powerup_interval_ms=1800,
        fall_scale_k=1.4
    ),
    # New Level 5
    LevelConfig(
        name="Level 5 • Overdrive",
        spawn_interval_ms=260,
        fall_speed_range=(420, 720),
        printer_speed=820,
        good_prob=0.46,
        max_items=24,
        girl_speed=1400,
        item_size=(50, 50),
        backgrounds=[
            BgStage("l5_bg_0.png",   "bg_40.mp3",   (12,12,22)),
            BgStage("l5_bg_20.png",  "bg_40.mp3",  (24,22,48)),
            BgStage("l5_bg_40.png",  "bg_40.mp3",  (40,30,66)),
            BgStage("l5_bg_60.png",  "bg_60.mp3",  (36,68,66)),
            BgStage("l5_bg_80.png",  "bg_80.mp3",  (66,94,60)),
            BgStage("l5_bg_100.png", "bg_100.mp3", (160,160,160)),
        ],
        time_limit_s=90,
        powerup_interval_ms=1700,
        fall_scale_k=1.5
    ),
    # Level 6: SPECIAL LEVEL (Fruit Ninja style)
    LevelConfig(
        name="SPECIAL LEVEL",
        spawn_interval_ms=950,                 # used differently
        fall_speed_range=(600, 900),           # used as base for throw
        printer_speed=0,                       # not used
        good_prob=0.5,
        max_items=8,
        girl_speed=1100,                       # not used
        item_size=(70, 70),                    # visual scaling for special
        backgrounds=[
            BgStage("special_bg_0.png",   "bg_40.mp3",   (16,16,20)),
            BgStage("special_bg_20.png",  "bg_40.mp3",  (24,28,44)),
            BgStage("special_bg_40.png",  "bg_40.mp3",  (36,40,60)),
            BgStage("special_bg_80.png", "bg_60.mp3", (42, 64, 60)),
            BgStage("special_bg_80.png",  "bg_80.mp3",  (56,84,58)),
            BgStage("special_bg_100.png", "bg_100.mp3", (120,120,120)),
        ],
        time_limit_s=60,
        powerup_interval_ms=0,
        fall_scale_k=0.0
    ),
]

# --------------------- entities ---------------------
class Girl:
    def __init__(self, y):
        self.w, self.h = 96, 192  # keep your chosen size
        self.x = VIRTUAL_W // 2 - self.w // 2
        self.y = y
        self.speed = 800
        self.frames: List[pygame.Surface] = []
        self.frames_big: List[pygame.Surface] = []
        self.use_big = False
        self.frame_index = 0
        self.anim_timer = 0.0
        self.anim_rate = 0.12
        self.facing_left = False
        self._load_frames()

    def _load_frames(self):
        def fallback_pair(w, h, shade=BLUE):
            s1 = pygame.Surface((w, h), pygame.SRCALPHA)
            s2 = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s1, shade, s1.get_rect(), border_radius=16)
            pygame.draw.rect(s2, shade, s2.get_rect(), border_radius=16)
            pygame.draw.rect(s1, WHITE, pygame.Rect(16, h//2-6, w-32, 12), border_radius=6)
            pygame.draw.rect(s2, WHITE, pygame.Rect(22, h//2-6, w-44, 12), border_radius=6)
            return [s1, s2]

        a = load_image("girl_walk1.png", (self.w, self.h))
        b = load_image("girl_walk2.png", (self.w, self.h))
        self.frames = [a, b] if a and b else fallback_pair(self.w, self.h, BLUE)

        big_w, big_h = 96, 192
        a2 = load_image("girl_big_walk1.png", (big_w, big_h))
        b2 = load_image("girl_big_walk2.png", (big_w, big_h))
        self.frames_big = [a2, b2] if a2 and b2 else fallback_pair(big_w, big_h, (70, 110, 255))

    def set_speed(self, v): self.speed = v

    def set_big_model(self, on: bool):
        if on == self.use_big: return
        self.use_big = on
        old_bottom = self.rect().bottom
        if on:
            self.w, self.h = self.frames_big[0].get_width(), self.frames_big[0].get_height()
        else:
            self.w, self.h = self.frames[0].get_width(), self.frames[0].get_height()
        self.y = old_bottom - self.h
        self.x = max(0, min(VIRTUAL_W - self.w, self.x))

    def update(self, dt, keys):
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if dx < 0: self.facing_left = True
        elif dx > 0: self.facing_left = False
        self.x += dx * self.speed * dt
        self.x = max(0, min(VIRTUAL_W - self.w, self.x))
        if dx != 0:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_rate:
                self.anim_timer = 0.0
                self.frame_index = (self.frame_index + 1) % 2
        else:
            self.frame_index = 0
            self.anim_timer = 0.0

    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def catch_rect(self, extra_width: int = 0):
        r = self.rect().copy()
        if extra_width > 0:
            r.x -= extra_width // 2
            r.w += extra_width
            r.x = max(0, r.x)
            r.w = min(VIRTUAL_W - r.x, r.w)
        return r

    def draw(self, surf):
        frame = (self.frames_big if self.use_big else self.frames)[self.frame_index]
        if self.facing_left: frame = pygame.transform.flip(frame, True, False)
        surf.blit(frame, (int(self.x), int(self.y)))

class Printer:
    def __init__(self, y, speed):
        self.base_speed = speed
        self.speed = speed
        self.dir = random.choice([-1, 1])
        self.image = load_image(PRINTER_IMAGE, PRINTER_SIZE)
        self.w, self.h = PRINTER_SIZE if self.image is None else (self.image.get_width(), self.image.get_height())
        self.x = VIRTUAL_W // 2 - self.w // 2
        self.y = y  # under the top bar
        if self.image is None:
            self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            pygame.draw.rect(self.surface, GRAY, self.surface.get_rect(), border_radius=16)
        else:
            self.surface = None

    def set_speed(self, v): self.base_speed = v; self.speed = v
    def apply_slowmo(self, factor: float): self.speed = self.base_speed * factor
    def clear_slowmo(self): self.speed = self.base_speed

    def update(self, dt):
        self.x += self.dir * self.speed * dt
        if self.x <= 0: self.x, self.dir = 0, 1
        if self.x + self.w >= VIRTUAL_W: self.x, self.dir = VIRTUAL_W - self.w, -1
        if random.random() < 0.004: self.dir *= -1

    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    def centerx(self): return self.x + self.w * 0.5
    def slot_y(self): return self.y + self.h
    def draw(self, surf):
        if self.image: surf.blit(self.image, (int(self.x), int(self.y)))
        else: surf.blit(self.surface, (int(self.x), int(self.y)))

class Item:
    def __init__(self, x, y, vy, size, good: bool, image: Optional[pygame.Surface] = None):
        self.x, self.y = x, y
        self.base_vy = vy
        self.vy = vy
        self.w, self.h = size
        self.good = good
        self.color = GREEN if good else RED
        self.image = image

    def apply_slowmo(self, factor: float): self.vy = self.base_vy * factor
    def clear_slowmo(self): self.vy = self.base_vy
    def apply_progress_scale(self, scale: float): self.vy = self.base_vy * scale

    def update(self, dt, magnet_to_x: Optional[float] = None, magnet_power: float = 0.0):
        if magnet_to_x is not None and magnet_power > 0.0:
            dx = magnet_to_x - self.x
            self.x += dx * magnet_power * dt
        self.y += self.vy * dt

    def rect(self): return pygame.Rect(int(self.x - self.w//2), int(self.y - self.h//2), self.w, self.h)

    def draw(self, surf):
        r = self.rect()
        if self.image:
            surf.blit(self.image, r.topleft)
        else:
            pygame.draw.rect(surf, self.color, r, border_radius=10)
            if self.good:
                pygame.draw.line(surf, WHITE, (r.left+8, r.centery), (r.centerx-2, r.bottom-8), 4)
                pygame.draw.line(surf, WHITE, (r.centerx-2, r.bottom-8), (r.right-8, r.top+8), 4)
            else:
                pygame.draw.line(surf, WHITE, (r.left+8, r.top+8), (r.right-8, r.bottom-8), 4)
                pygame.draw.line(surf, WHITE, (r.right-8, r.top+8), (r.left-8+r.w, r.bottom-8), 4)

# --------------------- special level entities ---------------------
class FlyingItem:
    def __init__(self, img: Optional[pygame.Surface], x: float, y: float, vx: float, vy: float, good: bool):
        self.img = img
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.good = good
        self.alive = True
        if img:
            self.w, self.h = img.get_size()
            self.radius = max(self.w, self.h) * 0.5
        else:
            self.w = self.h = 40
            self.radius = 22

    def update(self, dt):
        self.vy += 1400 * dt  # gravity
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y > VIRTUAL_H + 200:
            self.alive = False

    def draw(self, surf):
        if self.img:
            surf.blit(self.img, (int(self.x - self.w/2), int(self.y - self.h/2)))
        else:
            pygame.draw.circle(surf, WHITE if self.good else RED, (int(self.x), int(self.y)), int(self.radius), 2)

class SlicedPiece:
    def __init__(self, surf: pygame.Surface, cx: float, cy: float, vx: float, vy: float):
        self.surf = surf
        self.cx = cx
        self.cy = cy
        self.vx = vx
        self.vy = vy
        self.ang = 0.0
        self.ang_vel = random.uniform(-220, 220)
        self.alive = True

    def update(self, dt: float):
        self.vy += 1400 * dt
        self.cx += self.vx * dt
        self.cy += self.vy * dt
        self.ang += self.ang_vel * dt
        if self.cy > VIRTUAL_H + 200:
            self.alive = False

    def draw(self, surf: pygame.Surface):
        img = pygame.transform.rotate(self.surf, self.ang)
        rect = img.get_rect(center=(int(self.cx), int(self.cy)))
        surf.blit(img, rect.topleft)

# --------------------- game core ---------------------
class Game:
    def __init__(self):
        self.state = "MAIN_MENU"
        self.level_index = 0
        self.level = LEVELS[0]

        self.progress = 50
        self.time_left = self.level.time_limit_s
        self.items: List[Item] = []
        self.powerups: List[PowerUpDrop] = []
        self.active_timers: Dict[str, float] = {}
        self.double_gain = False
        self.magnet = False
        self.slowmo = False

        self.spawn_timer = 0.0
        self.powerup_timer = 0.0

        self.girl = Girl(VIRTUAL_H - 160)
        self.girl.set_speed(self.level.girl_speed)
        self.printer = Printer(TOP_BAR_H + 8, self.level.printer_speed)

        self.caught_good = 0
        self.caught_bad = 0
        self.result_text = ""
        self.mouse_down_last = False

        # background caching
        self.bg_images: List[Optional[pygame.Surface]] = [None]*6
        self.bg_stage_index = -1
        self.load_bg_assets()
        self.update_bg_stage(force=True)

        # --- special level runtime ---
        self.special_items: List[FlyingItem] = []
        self.special_spawn_timer = 0.0
        self.slice_points: List[Tuple[float, float, float]] = []  # (x,y,time)
        self.special_pieces: List[SlicedPiece] = []

    # ---------- backgrounds ----------
    def load_bg_assets(self):
        self.bg_images = []
        for stage in self.level.backgrounds:
            img = load_image(stage.image_path, (VIRTUAL_W, VIRTUAL_H)) if stage.image_path else None
            self.bg_images.append(img)

    def get_stage_index_for_progress(self) -> int:
        thresholds = [0, 20, 40, 60, 80, 100]
        idx = 0
        for i, t in enumerate(thresholds):
            if self.progress >= t: idx = i
        return idx

    def update_bg_stage(self, force=False):
        idx = self.get_stage_index_for_progress()
        if force or idx != self.bg_stage_index:
            self.bg_stage_index = idx
            stage = self.level.backgrounds[idx]
            safe_music_load_and_play(stage.sound_path)

    def draw_background(self, surf):
        idx = self.get_stage_index_for_progress()
        img = self.bg_images[idx]
        if img:
            surf.blit(img, (0, 0))
        else:
            surf.fill(self.level.backgrounds[idx].fallback_color)

    # ---------- helpers ----------
    def reset_level_runtime(self):
        self.progress = 50
        self.time_left = self.level.time_limit_s
        self.items.clear()
        self.powerups.clear()
        self.active_timers.clear()
        self.double_gain = False
        self.magnet = False
        self.slowmo = False
        self.spawn_timer = 0.0
        self.powerup_timer = 0.0
        self.girl = Girl(VIRTUAL_H - 160)
        self.girl.set_speed(self.level.girl_speed)
        self.girl.set_big_model(False)
        self.printer = Printer(TOP_BAR_H + 8, self.level.printer_speed)
        self.caught_good = 0
        self.caught_bad = 0
        self.result_text = ""
        self.load_bg_assets()
        self.bg_stage_index = -1
        self.update_bg_stage(force=True)

        # special reset
        self.special_items.clear()
        self.special_spawn_timer = 0.0
        self.slice_points.clear()
        self.special_pieces.clear()

    def progress_fall_scale(self) -> float:
        k = self.level.fall_scale_k
        return 1.0 + k * (max(0, min(100, self.progress)) / 100.0)

    def _activate(self, kind: str, duration: float):
        self.active_timers[kind] = duration
        if kind == PU_DOUBLE_PCT:
            self.double_gain = True
        elif kind == PU_BIGGER_BASKET:
            self.girl.set_big_model(True)
        elif kind == PU_MAGNET:
            self.magnet = True
        elif kind == PU_STOPWATCH:
            self.slowmo = True
            self._apply_slowmo(True)

    def _deactivate(self, kind: str):
        if kind in self.active_timers: del self.active_timers[kind]
        if kind == PU_DOUBLE_PCT:
            self.double_gain = False
        elif kind == PU_BIGGER_BASKET:
            self.girl.set_big_model(False)
        elif kind == PU_MAGNET:
            self.magnet = False
        elif kind == PU_STOPWATCH:
            self.slowmo = False
            self._apply_slowmo(False)

    def _apply_slowmo(self, on: bool):
        if on:
            factor = self.level.slowmo_factor
            self.printer.apply_slowmo(factor)
            for it in self.items: it.apply_slowmo(factor)
        else:
            self.printer.clear_slowmo()
            for it in self.items: it.clear_slowmo()

    # ---------- spawning (normal) ----------
    def spawn_item(self):
        if len(self.items) >= self.level.max_items: return
        good = random.random() < self.level.good_prob
        base_vy = random.uniform(*self.level.fall_speed_range)
        vy = base_vy * self.progress_fall_scale()
        if self.slowmo: vy *= self.level.slowmo_factor
        x = self.printer.centerx()
        y = self.printer.slot_y()
        # yeah
        # pick sprite from shared lists
        if good and GOOD_ITEM_FILES:
            sprite_path = random.choice(GOOD_ITEM_FILES)
        elif not good and BAD_ITEM_FILES:
            sprite_path = random.choice(BAD_ITEM_FILES)
        else:
            sprite_path = ""
        sprite_img = get_item_image(sprite_path, self.level.item_size)

        it = Item(x, y+10, vy, self.level.item_size, good, sprite_img)
        it.base_vy = base_vy
        it.apply_progress_scale(self.progress_fall_scale() * (self.level.slowmo_factor if self.slowmo else 1.0))
        self.items.append(it)

    def spawn_powerup(self):
        kinds = [PU_MORE_TIME, PU_LESS_TIME, PU_BIGGER_BASKET, PU_LESS_PCT, PU_MORE_PCT, PU_DOUBLE_PCT, PU_MAGNET, PU_STOPWATCH]
        base_vy = random.uniform(*self.level.fall_speed_range) * 0.9
        vy = base_vy * self.progress_fall_scale()
        if self.slowmo: vy *= self.level.slowmo_factor
        x = self.printer.centerx()
        y = self.printer.slot_y()
        self.powerups.append(PowerUpDrop(x, y+12, vy, random.choice(kinds)))

    # ---------- powerup apply ----------
    def apply_powerup(self, kind: str):
        dur = float(self.level.powerup_duration_s)
        if kind == PU_MORE_TIME:
            self.time_left += 5.0
            self.active_timers[kind] = 1.0
        elif kind == PU_LESS_TIME:
            self.time_left = max(0.0, self.time_left - 5.0)
            self.active_timers[kind] = 1.0
        elif kind == PU_BIGGER_BASKET:
            self._activate(PU_BIGGER_BASKET, dur)
        elif kind == PU_LESS_PCT:
            self.progress = max(0, self.progress - 2)
            self.active_timers[kind] = 1.0
        elif kind == PU_MORE_PCT:
            self.progress = min(100, self.progress + 5)
            self.active_timers[kind] = 1.0
        elif kind == PU_DOUBLE_PCT:
            self._activate(PU_DOUBLE_PCT, 5.0)
        elif kind == PU_MAGNET:
            self._activate(PU_MAGNET, dur)
        elif kind == PU_STOPWATCH:
            self._activate(PU_STOPWATCH, dur)

    # ---------- input ----------
    def handle_click(self, rects_with_actions):
        mouse = mouse_pos_virtual()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        clicked = False
        if self.mouse_down_last and not mouse_pressed:
            for r, action in rects_with_actions:
                if r.collidepoint(mouse):
                    action(); clicked = True; break
        self.mouse_down_last = mouse_pressed
        return clicked

    # ---------- UI drawing ----------
    def draw_top_bar(self, surf):
        pygame.draw.rect(surf, BLACK, pygame.Rect(0, 0, VIRTUAL_W, TOP_BAR_H))

        # progress bar
        bar_w, bar_h = 700, 28
        x = 24; y = (TOP_BAR_H - bar_h)//2
        pygame.draw.rect(surf, WHITE, pygame.Rect(x-2, y-2, bar_w+4, bar_h+4), border_radius=12)
        pct = max(0, min(100, self.progress)) / 100.0
        fill_w = int(bar_w * pct)
        fill_col = GREEN if self.progress >= 50 else YELLOW
        pygame.draw.rect(surf, fill_col, pygame.Rect(x, y, fill_w, bar_h), border_radius=12)
        draw_text_center(f"{self.progress}%", FONT_SM, BLACK, surf, x + bar_w//2, y + bar_h//2)

        # timer
        t = max(0, int(self.time_left))
        mins, secs = t // 60, t % 60
        draw_text_center(f"{mins:01d}:{secs:02d}", FONT_BIG, WHITE, surf, x + bar_w + 180, TOP_BAR_H//2)

        # powerup badges right
        badge_x = VIRTUAL_W - 16
        for kind, seconds in sorted(self.active_timers.items()):
            if kind in INSTANT_PUS and seconds <= 0: continue
            w, h = 44, 44
            r = pygame.Rect(badge_x - w, TOP_BAR_H//2 - h//2, w, h)
            icon = load_image(POWERUP_ICONS.get(kind, ""), (w, h))
            if icon: surf.blit(icon, r.topleft)
            else:
                col = {
                    PU_MORE_TIME: GREEN, PU_LESS_TIME: RED, PU_BIGGER_BASKET: GOLD,
                    PU_LESS_PCT: MAGENTA, PU_MORE_PCT: CYAN, PU_DOUBLE_PCT: ORANGE,
                    PU_MAGNET: (100, 200, 255), PU_STOPWATCH: PURPLE
                }.get(kind, YELLOW)
                pygame.draw.rect(surf, col, r, border_radius=10)
                short = {
                    PU_MORE_TIME: "+5s", PU_LESS_TIME: "-5s", PU_BIGGER_BASKET: "B",
                    PU_LESS_PCT: "-2", PU_MORE_PCT: "+5", PU_DOUBLE_PCT: "x2",
                    PU_MAGNET: "M", PU_STOPWATCH: "S"
                }.get(kind, "?")
                draw_text_center(short, FONT_SM, BLACK, surf, r.centerx, r.centery)
            label = f"{seconds:.1f}s" if kind in TIMED_PUS else f"{seconds:.1f}s"
            txt = FONT_TINY.render(label, True, WHITE)
            surf.blit(txt, (r.centerx - txt.get_width()//2, r.bottom + 2))
            badge_x -= w + 10

    # ---------- core loop: normal playing ----------
    def update_playing(self, dt):
        # timer
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.result_text = "Time up"
            self.state = "GAME_OVER"
            return

        # stage change by progress
        self.update_bg_stage(force=False)

        # tick powerups
        expired = []
        for kind in list(self.active_timers.keys()):
            self.active_timers[kind] -= dt
            if self.active_timers[kind] <= 0: expired.append(kind)
        for k in expired: self._deactivate(k)

        keys = pygame.key.get_pressed()
        self.girl.update(dt, keys)
        self.printer.update(dt)

        # spawn
        self.spawn_timer += dt * 1000
        if self.spawn_timer >= self.level.spawn_interval_ms:
            self.spawn_timer = 0
            self.spawn_item()

        self.powerup_timer += dt * 1000
        if self.powerup_timer >= self.level.powerup_interval_ms:
            self.powerup_timer = 0
            if random.random() < self.level.powerup_drop_prob:
                self.spawn_powerup()

        # rescale item velocities with current progress and slowmo
        scale_now = self.progress_fall_scale() * (self.level.slowmo_factor if self.slowmo else 1.0)
        for it in self.items:
            it.apply_progress_scale(scale_now)

        # collisions
        extra = self.level.basket_expand_px if self.girl.use_big else 0
        catch_rect = self.girl.catch_rect(extra)
        magnet_target_x = self.girl.rect().centerx if self.magnet else None
        magnet_power = 4.5 if self.magnet else 0.0

        # items
        for it in list(self.items):
            it.update(dt, magnet_target_x, magnet_power)
            if it.rect().colliderect(catch_rect):
                if it.good:
                    gain = 1
                    if self.double_gain: gain *= 2
                    self.progress = min(100, self.progress + gain)
                    self.caught_good += 1
                else:
                    self.progress = max(0, self.progress - 1)
                    self.caught_bad += 1
                self.items.remove(it)
            elif it.y - it.h > VIRTUAL_H:
                if it.good:
                    self.progress = max(0, self.progress - 1)  # penalty for missed good fruit
                self.items.remove(it)

        # powerups
        for pu in list(self.powerups):
            pu.update(dt)
            if pu.rect().colliderect(catch_rect):
                self.apply_powerup(pu.kind)
                self.powerups.remove(pu)
            elif pu.y - pu.h > VIRTUAL_H:
                self.powerups.remove(pu)

        # percent win or lose
        if self.progress <= 0:
            self.result_text = "Level failed, hit 0%"
            self.state = "GAME_OVER"
        elif self.progress >= 100:
            self.result_text = "Level complete, hit 100%"
            self.state = "GAME_OVER"

    # ---------- special level ----------
    def special_spawn(self):
        # choose asset from the shared pools
        good = random.random() < self.level.good_prob
        file_list = GOOD_ITEM_FILES if good else BAD_ITEM_FILES
        path = random.choice(file_list) if file_list else ""
        img = get_item_image(path, self.level.item_size)

        # launch from bottom with a tall arc
        x = random.uniform(VIRTUAL_W * 0.18, VIRTUAL_W * 0.82)
        y = VIRTUAL_H + 40
        # yeet higher so apex is mid/top screen (gravity ~1400, vy ~ -1400 to -1750)
        vy = -random.uniform(1350, 1750)
        vx = random.uniform(-520, 520)

        self.special_items.append(FlyingItem(img, x, y, vx, vy, good))

    def update_playing_special(self, dt):
        # timer
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.result_text = "Time up"
            self.state = "GAME_OVER"
            return

        # stage change by progress
        self.update_bg_stage(force=False)

        # spawn arcs bursty
        self.special_spawn_timer += dt * 1000
        if self.special_spawn_timer >= max(250, self.level.spawn_interval_ms - 100):
            self.special_spawn_timer = 0
            for _ in range(random.randint(1, 3)):
                if len(self.special_items) < self.level.max_items:
                    self.special_spawn()

        # update items
        for it in list(self.special_items):
            it.update(dt)
            if not it.alive:
                if it.good and it.y > VIRTUAL_H and self.progress > 0:
                    self.progress = max(0, self.progress - 1)
                self.special_items.remove(it)

        # update sliced halves
        for sp in list(self.special_pieces):
            sp.update(dt)
            if not sp.alive:
                self.special_pieces.remove(sp)

        # record slice path
        mx, my = mouse_pos_virtual()
        if pygame.mouse.get_pressed()[0]:
            self.slice_points.append((mx, my, pygame.time.get_ticks() / 1000.0))
        # keep last ~0.18s
        now = pygame.time.get_ticks() / 1000.0
        self.slice_points = [(x, y, t) for (x, y, t) in self.slice_points if now - t <= 0.18]

        # check slice collisions vs trail segments
        if len(self.slice_points) >= 2:
            pts = self.slice_points
            for it in list(self.special_items):
                if not it.alive: continue
                cx, cy, r = it.x, it.y, it.radius
                sliced = False
                swipe_dx = 0.0
                swipe_dy = 0.0
                for i in range(len(pts) - 1):
                    x1, y1, _ = pts[i]
                    x2, y2, _ = pts[i+1]
                    dx, dy = x2 - x1, y2 - y1
                    if dx == 0 and dy == 0: continue
                    # distance from center to segment
                    tproj = max(0, min(1, ((cx - x1)*dx + (cy - y1)*dy) / (dx*dx + dy*dy)))
                    px = x1 + tproj * dx
                    py = y1 + tproj * dy
                    dist2 = (px - cx)**2 + (py - cy)**2
                    if dist2 <= (r*r):
                        sliced = True
                        swipe_dx, swipe_dy = dx, dy
                if sliced:
                    it.alive = False
                    self.special_items.remove(it)
                    if it.good:
                        self.progress = min(100, self.progress + 1)
                    else:
                        self.progress = max(0, self.progress - 1)

                    if it.img:
                        w, h = it.img.get_size()
                        if abs(swipe_dx) >= abs(swipe_dy):
                            # horizontal swipe → horizontal cut (top/bottom)
                            top_rect = pygame.Rect(0, 0, w, h // 2)
                            bot_rect = pygame.Rect(0, h // 2, w, h - h // 2)
                            top_surf = it.img.subsurface(top_rect).copy()
                            bot_surf = it.img.subsurface(bot_rect).copy()
                            top_cx, top_cy = it.x, it.y - h * 0.25
                            bot_cx, bot_cy = it.x, it.y + h * 0.25
                            sep = 360
                            side = 1 if swipe_dx >= 0 else -1
                            self.special_pieces.append(SlicedPiece(top_surf, top_cx, top_cy, 120 * side, it.vy - sep))
                            self.special_pieces.append(SlicedPiece(bot_surf, bot_cx, bot_cy, -120 * side, it.vy + sep))
                        else:
                            # vertical swipe → vertical cut (left/right)
                            left_rect  = pygame.Rect(0, 0, w // 2, h)
                            right_rect = pygame.Rect(w // 2, 0, w - w // 2, h)
                            left_surf  = it.img.subsurface(left_rect).copy()
                            right_surf = it.img.subsurface(right_rect).copy()
                            left_cx, left_cy   = it.x - w * 0.25, it.y
                            right_cx, right_cy = it.x + w * 0.25, it.y
                            sep = 360
                            side = 1 if swipe_dy >= 0 else -1
                            self.special_pieces.append(SlicedPiece(left_surf,  left_cx,  left_cy,  it.vx - sep,  120 * side))
                            self.special_pieces.append(SlicedPiece(right_surf, right_cx, right_cy, it.vx + sep, -120 * side))

        # win/lose
        if self.progress <= 0:
            self.result_text = "Level failed, hit 0%"
            self.state = "GAME_OVER"
        elif self.progress >= 100:
            self.result_text = "Level complete, hit 100%"
            self.state = "GAME_OVER"

    # ---------- screens ----------
    def draw_playing(self, surf):
        self.draw_background(surf)
        self.draw_top_bar(surf)
        self.printer.draw(surf)
        for it in self.items: it.draw(surf)
        for pu in self.powerups: pu.draw(surf)
        self.girl.draw(surf)

        hud = f"Good {self.caught_good}  Bad {self.caught_bad}  Level {self.level.name}"
        txt = FONT_SM.render(hud, True, WHITE)
        surf.blit(txt, (24, VIRTUAL_H - 48))

        # Quit button
        back_rect = pygame.Rect(VIRTUAL_W - 160, VIRTUAL_H - 64, 136, 44)
        pygame.draw.rect(surf, BLACK, back_rect, border_radius=12)
        draw_text_center("Quit", FONT_MED, WHITE, surf, back_rect.centerx, back_rect.centery)
        self.handle_click([(back_rect, self.to_level_select)])

    def draw_playing_special(self, surf):
        self.draw_background(surf)
        self.draw_top_bar(surf)

        # flying items
        for it in self.special_items:
            it.draw(surf)
        # sliced halves on top
        for sp in self.special_pieces:
            sp.draw(surf)

        # slice trail
        if len(self.slice_points) >= 2:
            pts = [(int(x), int(y)) for (x, y, _) in self.slice_points]
            pygame.draw.lines(surf, CYAN, False, pts, 4)

        # footer HUD
        hud = f"SPECIAL LEVEL"
        txt = FONT_SM.render(hud, True, WHITE)
        surf.blit(txt, (24, VIRTUAL_H - 48))

        # Quit button
        back_rect = pygame.Rect(VIRTUAL_W - 160, VIRTUAL_H - 64, 136, 44)
        pygame.draw.rect(surf, BLACK, back_rect, border_radius=12)
        draw_text_center("Quit", FONT_MED, WHITE, surf, back_rect.centerx, back_rect.centery)
        self.handle_click([(back_rect, self.to_level_select)])

    def to_level_select(self):
        self.state = "LEVEL_SELECT"
        self.items.clear()
        self.powerups.clear()
        self.active_timers.clear()
        self._apply_slowmo(False)
        pygame.mixer.music.stop()
        self.special_items.clear()
        self.slice_points.clear()
        self.special_pieces.clear()

    def to_main_menu(self):
        self.state = "MAIN_MENU"
        pygame.mixer.music.stop()

    def start_level(self, idx):
        self.level_index = idx
        self.level = LEVELS[idx]
        self.reset_level_runtime()
        if self.level.name == "SPECIAL LEVEL":
            self.state = "PLAYING_SPECIAL"
        else:
            self.state = "PLAYING"

    def draw_main_menu(self, surf):
        if MAIN_MENU_BG_IMG:
            surf.blit(MAIN_MENU_BG_IMG, (0, 0))
        else:
            surf.fill((24, 24, 28))  # fallback color if file missing
        play_rect = pygame.Rect(VIRTUAL_W//2 - 180, VIRTUAL_H//2 - 40, 360, 84)
        quit_rect = pygame.Rect(VIRTUAL_W//2 - 180, VIRTUAL_H//2 + 70, 360, 70)
        pygame.draw.rect(surf, GREEN, play_rect, border_radius=18)
        pygame.draw.rect(surf, RED, quit_rect, border_radius=18)
        draw_text_center("Play", FONT_BIG, BLACK, surf, play_rect.centerx, play_rect.centery)
        draw_text_center("Quit", FONT_MED, WHITE, surf, quit_rect.centerx, quit_rect.centery)
        def go_play(): self.state = "LEVEL_SELECT"
        def go_quit(): pygame.quit(); sys.exit(0)
        self.handle_click([(play_rect, go_play), (quit_rect, go_quit)])
        draw_text_center("Move with arrows or A D • Hold mouse to slice in SPECIAL LEVEL", FONT_MED, WHITE, surf, VIRTUAL_W//2, VIRTUAL_H - 60)

    def draw_level_select(self, surf):
        surf.fill((18, 20, 28))
        draw_text_center("Select Level", FONT_XL, WHITE, surf, VIRTUAL_W//2, 140)
        back_rect = pygame.Rect(40, 40, 200, 64)
        pygame.draw.rect(surf, GRAY, back_rect, border_radius=14)
        draw_text_center("Back", FONT_MED, WHITE, surf, back_rect.centerx, back_rect.centery)
        start_y, gap = 260, 22
        btn_w, btn_h = 1100, 96
        rects = [(back_rect, self.to_main_menu)]
        for i, lvl in enumerate(LEVELS):
            r = pygame.Rect(VIRTUAL_W//2 - btn_w//2, start_y + i*(btn_h + gap), btn_w, btn_h)
            pygame.draw.rect(surf, YELLOW if lvl.name != "SPECIAL LEVEL" else ORANGE, r, border_radius=18)
            label = f"{i+1}. {lvl.name} • time {lvl.time_limit_s}s • good {int(lvl.good_prob*100)}%"
            draw_text_center(label, FONT_MED, BLACK, surf, r.centerx, r.centery)
            rects.append((r, lambda idx=i: self.start_level(idx)))
        self.handle_click(rects)

    def draw_game_over(self, surf):
        surf.fill((14, 14, 20))
        draw_text_center(self.result_text, FONT_XL, WHITE, surf, VIRTUAL_W//2, VIRTUAL_H//2 - 180)
        stats = f"Final {self.progress}%"
        draw_text_center(stats, FONT_BIG, WHITE, surf, VIRTUAL_W//2, VIRTUAL_H//2 - 60)
        again_rect = pygame.Rect(VIRTUAL_W//2 - 380, VIRTUAL_H//2 + 20, 320, 84)
        menu_rect = pygame.Rect(VIRTUAL_W//2 + 60, VIRTUAL_H//2 + 20, 320, 84)
        pygame.draw.rect(surf, GREEN, again_rect, border_radius=18)
        pygame.draw.rect(surf, YELLOW, menu_rect, border_radius=18)
        draw_text_center("Retry", FONT_BIG, BLACK, surf, again_rect.centerx, again_rect.centery)
        draw_text_center("Level Select", FONT_BIG, BLACK, surf, menu_rect.centerx, menu_rect.centery)
        def retry(): self.start_level(self.level_index)
        def to_menu(): self.state = "LEVEL_SELECT"
        self.handle_click([(again_rect, retry), (menu_rect, to_menu)])

    # ---------- main run ----------
    def run(self):
        global SCREEN, SCREEN_W, SCREEN_H
        while True:
            dt = CLOCK.tick(FPS) / 1000.0
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.state in ("PLAYING", "PLAYING_SPECIAL"):
                            self.state = "LEVEL_SELECT"; pygame.mixer.music.stop()
                        elif self.state == "LEVEL_SELECT":
                            self.state = "MAIN_MENU"
                        elif self.state == "GAME_OVER":
                            self.state = "LEVEL_SELECT"
                    if e.key == pygame.K_F11:
                        flags = SCREEN.get_flags()
                        if flags & pygame.FULLSCREEN:
                            SCREEN = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                        else:
                            SCREEN = make_fullscreen()
                        SCREEN_W, SCREEN_H = SCREEN.get_size()

            GAME_SURF.fill((0, 0, 0, 0))
            if self.state == "MAIN_MENU":
                self.draw_main_menu(GAME_SURF)
            elif self.state == "LEVEL_SELECT":
                self.draw_level_select(GAME_SURF)
            elif self.state == "PLAYING":
                self.update_playing(dt)
                self.draw_playing(GAME_SURF)
            elif self.state == "PLAYING_SPECIAL":
                self.update_playing_special(dt)
                self.draw_playing_special(GAME_SURF)
            elif self.state == "GAME_OVER":
                self.draw_game_over(GAME_SURF)

            pygame.transform.smoothscale(GAME_SURF, (SCREEN_W, SCREEN_H), SCREEN)
            pygame.display.flip()

# --------------------- PowerUpDrop (kept same spot to avoid renaming) ---------------------
class PowerUpDrop:
    ICON_SIZE = (40, 40)
    def __init__(self, x, y, vy, kind: str):
        self.x, self.y, self.vy = x, y, vy
        self.kind = kind
        self.w, self.h = 44, 44
        self.icon = load_image(POWERUP_ICONS.get(kind, ""), self.ICON_SIZE)

    def update(self, dt): self.y += self.vy * dt
    def rect(self): return pygame.Rect(int(self.x - self.w//2), int(self.y - self.h//2), self.w, self.h)

    def draw(self, surf):
        r = self.rect()
        if self.icon:
            surf.blit(self.icon, (r.x + (r.w - self.ICON_SIZE[0])//2, r.y + (r.h - self.ICON_SIZE[1])//2))
        else:
            col = {
                PU_MORE_TIME: GREEN, PU_LESS_TIME: RED, PU_BIGGER_BASKET: GOLD,
                PU_LESS_PCT: MAGENTA, PU_MORE_PCT: CYAN, PU_DOUBLE_PCT: ORANGE,
                PU_MAGNET: (100, 200, 255), PU_STOPWATCH: PURPLE
            }.get(self.kind, YELLOW)
            pygame.draw.rect(surf, col, r, border_radius=10)
            short = {
                PU_MORE_TIME: "+5s", PU_LESS_TIME: "-5s", PU_BIGGER_BASKET: "B",
                PU_LESS_PCT: "-2%", PU_MORE_PCT: "+5%", PU_DOUBLE_PCT: "x2",
                PU_MAGNET: "M", PU_STOPWATCH: "S"
            }.get(self.kind, "?")
            draw_text_center(short, FONT_TINY, BLACK, surf, r.centerx, r.centery)

# --------------------- entry ---------------------
if __name__ == "__main__":
    Game().run()
