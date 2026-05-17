import pygame
import sys
import math

W, H = 800, 600

# ── Classes ───────────────────────────────────────────────────────────────────

class Player:
    def __init__(self):
        self.speed = 5
        self.jump_power = -18
        self.col = (85, 153, 255)
        self.rect = pygame.Rect(0, 0, 28, 36)
        self.y_vel = 0
        self.on_ground = False
        self.facing_right = True

    def move(self):
        if overlay_timer > 0:
            return
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            dx -= self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            dx += self.speed
            self.facing_right = True
        if keys[pygame.K_UP] and self.on_ground:
            self.y_vel = self.jump_power
            snd_jump.play()

        self.on_ground = False
        if self.y_vel < 10:
            self.y_vel += 1
        dy += self.y_vel

        for p in platforms:
            ny = pygame.Rect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height)
            if ny.colliderect(p.rect):
                if self.y_vel > 0:
                    dy = p.rect.top - self.rect.bottom
                    self.y_vel = 0
                    self.on_ground = True
                elif self.y_vel < 0:
                    dy = p.rect.bottom - self.rect.top
                    self.y_vel = 0
            nx = pygame.Rect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height)
            if nx.colliderect(p.rect):
                dx = 0

        self.rect.x += dx
        self.rect.y += dy
        self.rect.x = max(-500, min(self.rect.x, WORLD_W - self.rect.width))

        if self.rect.y > WORLD_H:
            self.reset()

    def draw(self, cx, cy):
        pygame.draw.rect(screen, self.col,
            (self.rect.x-cx, self.rect.y-cy, self.rect.width, self.rect.height), border_radius=5)
        if self.facing_right:
            pygame.draw.ellipse(screen, (255,255,255), (self.rect.x-cx+13, self.rect.y-cy+6,  12,14))
            pygame.draw.circle(screen, (17,17,17),    (self.rect.x-cx+21,  self.rect.y-cy+13), 3)
        else:
            pygame.draw.ellipse(screen, (255,255,255), (self.rect.x-cx+5,  self.rect.y-cy+6,  12,14))
            pygame.draw.circle(screen, (17,17,17),    (self.rect.x-cx+7,   self.rect.y-cy+13), 3)

    def reset(self):
        self.rect.x = spawn_x
        self.rect.y = spawn_y
        self.y_vel = 0
        self.on_ground = False
        self.facing_right = True


class Platform:
    def __init__(self, x, y, w, h, col=(100, 80, 60)):
        self.rect = pygame.Rect(x, y, w, h)
        self.col = col

    def draw(self, cx, cy):
        pygame.draw.rect(screen, self.col,
            (self.rect.x-cx, self.rect.y-cy, self.rect.width, self.rect.height), border_radius=3)
        r = min(self.col[0]+30, 255)
        g = min(self.col[1]+30, 255)
        b = min(self.col[2]+30, 255)
        pygame.draw.line(screen, (r,g,b),
            (self.rect.x-cx,                  self.rect.y-cy),
            (self.rect.x-cx+self.rect.width-1, self.rect.y-cy))


class Spike:
    def __init__(self, x, y, hidden=False):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.hidden = hidden

    def draw(self, cx, cy):
        if self.hidden:
            return
        sx, sy = self.rect.x-cx, self.rect.y-cy
        pygame.draw.polygon(screen, (220,50,50),
            [(sx+10,sy),(sx+20,sy+20),(sx,sy+20)])

    def check_collision(self, player):
        return self.rect.colliderect(player.rect)


class BigDecorSpike:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self, cx, cy):
        sx, sy = self.x-cx, self.y-cy
        pygame.draw.polygon(screen, (200, 40, 40), [
            (sx + self.w//2, sy),
            (sx + self.w,    sy + self.h),
            (sx,             sy + self.h),
        ])
        pygame.draw.polygon(screen, (240, 80, 80), [
            (sx + self.w//2, sy),
            (sx + self.w//2 + 6, sy + self.h//3),
            (sx + self.w//2 - 6, sy + self.h//3),
        ])


class Liquid:
    def __init__(self, x, y, w, h, col=(70, 200, 100)):
        self.rect = pygame.Rect(x, y, w, h)
        self.col = col
        self.t = 0

    def draw(self, cx, cy):
        sx, sy = self.rect.x-cx, self.rect.y-cy
        pygame.draw.rect(screen, self.col, (sx, sy, self.rect.width, self.rect.height), border_radius=3)
        hi = (min(self.col[0]+30,255), min(self.col[1]+30,255), min(self.col[2]+30,255))
        pygame.draw.line(screen, hi, (sx, sy), (sx+self.rect.width-1, sy))

    def check_collision(self, player):
        return self.rect.colliderect(player.rect)


class JumpPad:
    def __init__(self, x, y, boost=-24):
        self.rect = pygame.Rect(x, y, 40, 10)
        self.boost = boost
        self.flash = 0

    def draw(self, cx, cy):
        sx, sy = self.rect.x-cx, self.rect.y-cy
        col = (90,255,130) if self.flash > 0 else (60,200,90)
        pygame.draw.rect(screen, col, (sx, sy, 40, 10), border_radius=4)
        pygame.draw.rect(screen, (40,140,60), (sx, sy+8, 40, 4), border_radius=2)
        if self.flash > 0:
            self.flash -= 1

    def check_collision(self, player):
        if self.rect.colliderect(player.rect) and player.y_vel >= 0:
            player.y_vel = self.boost
            self.flash = 8
            return True
        return False


class Swing:
    def __init__(self, ax, ay, length=150, speed=1.5, max_angle=60, time_offset=0):
        self.ax = ax
        self.ay = ay
        self.length = length
        self.speed = speed
        self.max_angle = math.radians(max_angle)
        self.time = time_offset
        self.ball_radius = 15
        self.bx = ax
        self.by = ay + length

    def move(self):
        self.time += 0.03 * self.speed
        a = self.max_angle * math.sin(self.time)
        self.bx = int(self.ax + self.length * math.sin(a))
        self.by = int(self.ay + self.length * math.cos(a))

    def draw(self, cx, cy):
        for i in range(13):
            t = i / 12
            lx = int(self.ax + t*(self.bx-self.ax))
            ly = int(self.ay + t*(self.by-self.ay))
            pygame.draw.circle(screen, (160,160,160), (lx-cx, ly-cy), 4)
        pygame.draw.circle(screen, (80,80,80), (self.bx-cx, self.by-cy), self.ball_radius)
        for i in range(8):
            a = (2*math.pi/8)*i
            sx = int(self.bx + (self.ball_radius+7)*math.cos(a))
            sy = int(self.by + (self.ball_radius+7)*math.sin(a))
            pygame.draw.circle(screen, (110,110,110), (sx-cx, sy-cy), 5)
        pygame.draw.circle(screen, (120,120,120), (self.ax-cx, self.ay-cy), 7)

    def check_collision(self, player):
        return math.hypot(self.bx-player.rect.centerx, self.by-player.rect.centery) < self.ball_radius+14


class Coin:
    def __init__(self, x, y, trap=None):
        self.rect = pygame.Rect(x-8, y-8, 16, 16)
        self.collected = False
        self.trap = trap

    def draw(self, cx, cy):
        if self.collected:
            return
        px, py = self.rect.centerx-cx, self.rect.centery-cy
        pygame.draw.circle(screen, (255,215,0),   (px, py), 8)
        pygame.draw.circle(screen, (255,245,120), (px-2, py-3), 3)

    def check_collision(self, player):
        if not self.collected and self.rect.colliderect(player.rect):
            self.collected = True
            if self.trap:
                self.trap()
            return True
        return False


class Goal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 36, 52)

    def draw(self, cx, cy):
        sx, sy = self.rect.x-cx, self.rect.y-cy
        pygame.draw.rect(screen, (40,180,70),  (sx,sy,self.rect.width,self.rect.height), border_radius=4)
        pygame.draw.rect(screen, (80,255,120), (sx,sy,self.rect.width,self.rect.height), 2, border_radius=4)
        pygame.draw.circle(screen, (255,215,0), (sx+28, sy+26), 3)

    def check_collision(self, player):
        return self.rect.colliderect(player.rect)


class Checkpoint:
    def __init__(self, x, y, trap=None, fake=False):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 14, 40)
        self.active = False
        self.trap = trap
        self.fake = fake

    def draw(self, cx, cy):
        sx, sy = self.x-cx, self.y-cy
        pygame.draw.rect(screen, (90,70,40), (sx+5, sy, 4, 40))
        flag_col = (60,200,90) if self.active else (140,140,140)
        pts = [(sx+9, sy+2),(sx+30, sy+8),(sx+9, sy+18)]
        pygame.draw.polygon(screen, flag_col, pts)

    def check_collision(self, player):
        if not self.active and self.rect.colliderect(player.rect):
            self.active = True
            if self.trap:
                self.trap()
            return not self.fake
        return False


class Enemy:
    def __init__(self, x, y, left, right, speed=1.5):
        self.rect = pygame.Rect(x, y, 28, 24)
        self.left = left
        self.right = right
        self.vx = speed
        self.alive = True

    def move(self):
        if not self.alive:
            return
        self.rect.x += self.vx
        if self.rect.left < self.left:
            self.rect.left = self.left
            self.vx = abs(self.vx)
        elif self.rect.right > self.right:
            self.rect.right = self.right
            self.vx = -abs(self.vx)

    def draw(self, cx, cy):
        if not self.alive:
            return
        sx, sy = self.rect.x-cx, self.rect.y-cy
        pygame.draw.rect(screen, (200,55,55), (sx, sy, self.rect.width, self.rect.height), border_radius=6)
        pygame.draw.circle(screen, (255,255,255), (sx+8,  sy+9), 3)
        pygame.draw.circle(screen, (255,255,255), (sx+20, sy+9), 3)
        pygame.draw.circle(screen, (20,20,20),    (sx+8,  sy+9), 1)
        pygame.draw.circle(screen, (20,20,20),    (sx+20, sy+9), 1)

    def check_collision(self, player):
        if not self.alive or not self.rect.colliderect(player.rect):
            return None
        if player.y_vel > 0 and player.rect.bottom - player.y_vel <= self.rect.top + 6:
            self.alive = False
            player.y_vel = -12
            return 'stomp'
        return 'hit'


class Sign:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text

    def draw(self, cx, cy, font):
        sx, sy = self.x-cx, self.y-cy
        pygame.draw.rect(screen, (120,80,30), (sx+16, sy+22, 4, 40))
        pts = [(sx,sy),(sx+32,sy),(sx+44,sy+11),(sx+32,sy+22),(sx,sy+22)]
        pygame.draw.polygon(screen, (240,200,40), pts)
        pygame.draw.polygon(screen, (160,120,10), pts, 2)
        screen.blit(font.render(self.text, True, (30,20,10)), (sx+3, sy+5))


class Label:
    def __init__(self, x, y, text, col=(190,220,190)):
        self.x = x
        self.y = y
        self.text = text
        self.col = col

    def draw(self, cx, cy, font):
        screen.blit(font.render(self.text, True, self.col), (self.x-cx, self.y-cy))


class TrollZone:
    def __init__(self, x, y, w, h, message, next_scene):
        self.rect = pygame.Rect(x, y, w, h)
        self.message = message
        self.next_scene = next_scene

    def check_collision(self, player):
        return self.rect.colliderect(player.rect)


# ── Scene globals ─────────────────────────────────────────────────────────────

WORLD_W, WORLD_H = 1600, 1200
spawn_x, spawn_y = 20, 100
scene = 'tutorial_1'

platforms   = []
spikes      = []
swings      = []
coins       = []
signs       = []
goals       = []
checkpoints = []
enemies     = []
troll_zones = []
labels      = []
liquids     = []
jumppads    = []
decor       = []

overlay_lines = []
overlay_timer = 0
overlay_next  = ''
toast_text    = ''
idle_frames   = 0
idle_target   = 0
idle_reveal   = False


def show_overlay(lines, duration, next_scene):
    global overlay_lines, overlay_timer, overlay_next
    overlay_lines = lines
    overlay_timer = duration
    overlay_next  = next_scene


def load_scene(name):
    global scene, toast_text, idle_frames, idle_target, idle_reveal
    scene = name
    toast_text = ''
    idle_frames = 0
    idle_target = 0
    idle_reveal = False
    for lst in (platforms, spikes, swings, coins, signs, goals, checkpoints,
                enemies, troll_zones, labels, liquids, jumppads, decor):
        lst.clear()

    if   name == 'tutorial_1': _tutorial_1()
    elif name == 'tutorial_2': _tutorial_2()
    elif name == 'tutorial_3': _tutorial_3()
    elif name == 'tutorial_4': _tutorial_4()
    elif name == 'level_1a':   _level_1a()
    elif name == 'level_2':    _level_2()
    elif name == 'level_3':    _level_3()
    elif name == 'level_4':    _level_4()
    elif name == 'level_5':    _level_5()

    player.reset()


# ── Scene definitions ─────────────────────────────────────────────────────────

# Tutorial 1: Movement + coins. Habit: right = forward, coins = reward.
def _tutorial_1():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 1300, 600
    spawn_x, spawn_y = 60, 524

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0, 560, WORLD_W, 40, FC))
    platforms.append(Platform(260, 490, 120, 14, PC))
    platforms.append(Platform(470, 440, 120, 14, PC))
    platforms.append(Platform(670, 468, 120, 14, PC))
    platforms.append(Platform(880, 418, 120, 14, PC))
    platforms.append(Platform(1080, 452, 120, 14, PC))

    coins.append(Coin(320, 468))
    coins.append(Coin(530, 418))
    coins.append(Coin(730, 446))
    coins.append(Coin(940, 396))
    coins.append(Coin(1140, 430))

    goals.append(Goal(1224, 508))

    labels.append(Label(68,  506, 'Arrow keys to move',  (170, 210, 170)))
    labels.append(Label(68,  486, 'Up arrow to jump',    (170, 210, 170)))
    labels.append(Label(268, 462, 'Collect coins',       (255, 215, 0)))
    labels.append(Label(1148, 476, '> exit',             (100, 255, 130)))

    for ax in range(160, 1180, 170):
        labels.append(Label(ax, 534, '>', (80, 120, 80)))


# Tutorial 2: Color language. Habit: green = safe, red = danger.
def _tutorial_2():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 1500, 600
    spawn_x, spawn_y = 40, 524

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0,    560, 280,  40, FC))
    platforms.append(Platform(380,  560, 220,  40, FC))
    platforms.append(Platform(720,  560, 220,  40, FC))
    platforms.append(Platform(1060, 560, 440,  40, FC))

    platforms.append(Platform(300,  470, 60, 14, PC))
    platforms.append(Platform(620,  450, 80, 14, PC))
    platforms.append(Platform(960,  470, 80, 14, PC))

    spikes.extend([Spike(x, 540) for x in (290, 310, 330, 350)])
    spikes.extend([Spike(x, 540) for x in (620, 640, 660, 680, 700)])
    spikes.extend([Spike(x, 540) for x in (960, 980, 1000, 1020, 1040)])

    jumppads.append(JumpPad(800,  550))
    jumppads.append(JumpPad(1140, 550))

    coins.append(Coin(330, 448))
    coins.append(Coin(660, 428))
    coins.append(Coin(820, 420))
    coins.append(Coin(1160, 420))
    coins.append(Coin(1000, 448))

    goals.append(Goal(1430, 508))

    labels.append(Label(40,  500, 'Green is safe',  (130, 230, 140)))
    labels.append(Label(40,  520, 'Red hurts',      (240, 130, 130)))
    labels.append(Label(770, 510, 'Green pads boost', (130, 230, 140)))


# Tutorial 3: Checkpoints. Habit: green flags save your spot.
def _tutorial_3():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 2000, 600
    spawn_x, spawn_y = 40, 524

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0, 560, WORLD_W, 40, FC))

    platforms.append(Platform(260,  490, 100, 14, PC))
    platforms.append(Platform(420,  440, 100, 14, PC))
    platforms.append(Platform(600,  470, 100, 14, PC))
    platforms.append(Platform(900,  490, 100, 14, PC))
    platforms.append(Platform(1080, 440, 100, 14, PC))
    platforms.append(Platform(1260, 480, 100, 14, PC))
    platforms.append(Platform(1560, 460, 100, 14, PC))
    platforms.append(Platform(1740, 430, 100, 14, PC))

    spikes.extend([Spike(x, 540) for x in (760, 780, 800, 820, 840)])
    spikes.extend([Spike(x, 540) for x in (1400, 1420, 1440, 1460, 1480, 1500)])

    coins.append(Coin(470, 418))
    coins.append(Coin(1130, 418))
    coins.append(Coin(1790, 408))

    checkpoints.append(Checkpoint(700,  520))
    checkpoints.append(Checkpoint(1340, 520))

    goals.append(Goal(1920, 508))

    labels.append(Label(680,  490, 'Green flag = checkpoint', (130, 230, 140)))


# Tutorial 4: Enemies. Habit: stomp red things from above, side touch = death.
def _tutorial_4():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 2000, 600
    spawn_x, spawn_y = 40, 524

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0, 560, WORLD_W, 40, FC))
    platforms.append(Platform(380,  480, 120, 14, PC))
    platforms.append(Platform(700,  450, 120, 14, PC))
    platforms.append(Platform(1020, 480, 120, 14, PC))
    platforms.append(Platform(1340, 450, 120, 14, PC))
    platforms.append(Platform(1660, 480, 120, 14, PC))

    enemies.append(Enemy(260,  536, 220,  500, 1.4))
    enemies.append(Enemy(880,  536, 840,  1120, 1.6))
    enemies.append(Enemy(1500, 536, 1460, 1740, 1.8))

    coins.append(Coin(440, 458))
    coins.append(Coin(760, 428))
    coins.append(Coin(1080, 458))
    coins.append(Coin(1400, 428))
    coins.append(Coin(1720, 458))

    checkpoints.append(Checkpoint(620,  520))
    checkpoints.append(Checkpoint(1260, 520))

    goals.append(Goal(1920, 508))

    labels.append(Label(40,  500, 'Jump on enemies', (130, 230, 140)))
    labels.append(Label(40,  520, 'Side touch hurts', (240, 130, 130)))


def _level_1a():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 1600, 1200
    spawn_x, spawn_y = 20, WORLD_H - 56

    swings.extend([
        Swing(375,  WORLD_H-400, 280, 1.1, 60, 0),
        Swing(375,  WORLD_H-400, 280, 1.1, 60, 1.57),
        Swing(815,  WORLD_H-400, 280, 1.3, 60, 0),
        Swing(815,  WORLD_H-400, 280, 1.3, 60, 1.57),
        Swing(1315, WORLD_H-400, 280, 1.5, 60, 0),
        Swing(1315, WORLD_H-400, 280, 1.5, 60, 1.57),
    ])

    platforms.extend([
        Platform(-500, WORLD_H-20, WORLD_W+500, 20),
        Platform(-30,  WORLD_H-160, 20, 140, (90, 90, 110)),
        Platform(190,  WORLD_H-110, 120, 20),
        Platform(440,  WORLD_H-185, 120, 20),
        Platform(690,  WORLD_H-150, 120, 20),
        Platform(940,  WORLD_H-225, 120, 20),
        Platform(1190, WORLD_H-165, 120, 20),
        Platform(1440, WORLD_H-130, 120, 20),
    ])

    signs.append(Sign(30, WORLD_H-82, 'GO LEFT'))
    goals.append(Goal(-300, WORLD_H-72))

    spikes.extend([
        *[Spike(x, WORLD_H-40) for x in range(120,  278, 20)],
        *[Spike(x, WORLD_H-40) for x in range(340,  528, 20)],
        *[Spike(x, WORLD_H-40) for x in range(590,  778, 20)],
        *[Spike(x, WORLD_H-40) for x in range(840,  1028, 20)],
        *[Spike(x, WORLD_H-40) for x in range(1090, 1278, 20)],
        *[Spike(x, WORLD_H-40) for x in range(1340, 1528, 20)],
        Spike(220,  WORLD_H-130), Spike(240,  WORLD_H-130), Spike(260,  WORLD_H-130),
        Spike(470,  WORLD_H-205), Spike(490,  WORLD_H-205), Spike(510,  WORLD_H-205),
        Spike(720,  WORLD_H-170), Spike(740,  WORLD_H-170), Spike(760,  WORLD_H-170),
        Spike(970,  WORLD_H-245), Spike(990,  WORLD_H-245), Spike(1010, WORLD_H-245),
        Spike(1220, WORLD_H-185), Spike(1240, WORLD_H-185), Spike(1260, WORLD_H-185),
        Spike(1470, WORLD_H-150), Spike(1490, WORLD_H-150), Spike(1510, WORLD_H-150),
    ])


# Level 2 — Weaponizes: "green = safe". Green pools look like the jump pads/safe
# platforms from the tutorial, but they kill on contact.
def _level_2():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 2200, 600
    spawn_x, spawn_y = 40, 524

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0,    560, 360,  40, FC))
    platforms.append(Platform(560,  560, 280,  40, FC))
    platforms.append(Platform(1040, 560, 280,  40, FC))
    platforms.append(Platform(1520, 560, 280,  40, FC))
    platforms.append(Platform(2000, 560, 200,  40, FC))

    platforms.append(Platform(420,  490, 80,  14, PC))
    platforms.append(Platform(900,  470, 80,  14, PC))
    platforms.append(Platform(1380, 490, 80,  14, PC))
    decor.append(Platform(1860, 470, 80, 14, PC))

    liquids.append(Liquid(360, 560, 200, 40))
    liquids.append(Liquid(840, 560, 200, 40))
    liquids.append(Liquid(1320, 560, 200, 40))
    liquids.append(Liquid(1800, 560, 200, 40))

    # Looks terrifying — safe to walk through, deadly to jump over.
    decor.append(BigDecorSpike(150, 460, 80, 100))
    for hx in range(130, 230, 20):
        spikes.append(Spike(hx, 380, hidden=True))

    coins.append(Coin(460, 470))
    coins.append(Coin(940, 450))
    coins.append(Coin(1420, 470))
    coins.append(Coin(1900, 450))

    def enemy_swarm():
        for fx, fl, fr in [
            (580,  560, 820),  (640,  560, 820),  (740,  560, 820),
            (1060, 1040, 1300),(1140, 1040, 1300),(1220, 1040, 1300),
            (1540, 1520, 1780),(1620, 1520, 1780),(1700, 1520, 1780),
            (2020, 2000, 2180),(2080, 2000, 2180),(2140, 2000, 2180),
        ]:
            enemies.append(Enemy(fx, 536, fl, fr, 2.0))

    checkpoints.append(Checkpoint(700,  520, trap=enemy_swarm, fake=True))
    checkpoints.append(Checkpoint(1180, 520, trap=enemy_swarm, fake=True))

    goals.append(Goal(2120, 508))


# Level 3 — Weaponizes: "coins are reward". A glittering coin sits in plain sight;
# collecting it unleashes enemies, swings, and spikes in the path ahead.
def _level_3():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 2400, 700
    spawn_x, spawn_y = 40, 624

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0, 660, WORLD_W, 40, FC))

    platforms.append(Platform(260,  560, 130, 14, PC))
    platforms.append(Platform(520,  500, 130, 14, PC))
    platforms.append(Platform(820,  540, 130, 14, PC))
    platforms.append(Platform(1120, 480, 130, 14, PC))
    platforms.append(Platform(1420, 520, 130, 14, PC))
    platforms.append(Platform(1720, 470, 130, 14, PC))
    platforms.append(Platform(2020, 510, 130, 14, PC))

    spikes.extend([Spike(x, 640) for x in range(400, 520, 20)])
    spikes.extend([Spike(x, 640) for x in range(960, 1110, 20)])

    enemies.append(Enemy(680, 636, 640, 820, 1.5))

    coins.append(Coin(320, 538))
    coins.append(Coin(580, 478))
    coins.append(Coin(1780, 448))

    def spring_trap():
        enemies.extend([
            Enemy(1280, 636, 1140, 1410, 2.2),
            Enemy(1620, 636, 1560, 1850, 2.4),
            Enemy(1980, 636, 1860, 2200, 2.6),
        ])
        swings.extend([
            Swing(1470, 240, 260, 1.6, 55, 0),
            Swing(1900, 240, 260, 1.7, 55, 0.9),
        ])
        spikes.extend([Spike(x, 640) for x in range(1300, 1410, 20)])

    # A lonely, isolated coin floating over the gap — irresistible.
    coins.append(Coin(1185, 440, trap=spring_trap))

    checkpoints.append(Checkpoint(950, 620))

    goals.append(Goal(2320, 608))


# Level 4 — Weaponizes: "constant movement / progress means going forward".
# The right path looks impossible. The exit only opens after standing still.
def _level_4():
    global WORLD_W, WORLD_H, spawn_x, spawn_y, idle_target
    WORLD_W, WORLD_H = 1400, 600
    spawn_x, spawn_y = 60, 524

    FC = (95, 70, 45)
    PC = (65, 145, 65)

    platforms.append(Platform(0, 560, WORLD_W, 40, FC))
    platforms.append(Platform(900, 200, 500, 360, FC))

    spikes.extend([Spike(x, 540) for x in range(280, 900, 20)])

    idle_target = 180  # 3 seconds at 60fps
    goals.append(Goal(120, 508))
    labels.append(Label(60,  500, 'No way through.', (200, 200, 210)))


# Level 5 (BOSS) — Same layout as Level 1, but exit is on the RIGHT this time.
# Players burned by Level 1's "go left" twist will instinctively go left again
# and walk straight into the manipulation troll zone.
def _level_5():
    global WORLD_W, WORLD_H, spawn_x, spawn_y
    WORLD_W, WORLD_H = 1600, 1200
    spawn_x, spawn_y = 20, WORLD_H - 56

    swings.extend([
        Swing(375,  WORLD_H-400, 280, 1.1, 55, 0),
        Swing(815,  WORLD_H-400, 280, 1.3, 55, 0),
        Swing(1315, WORLD_H-400, 280, 1.5, 55, 0),
    ])

    platforms.extend([
        Platform(-500, WORLD_H-20, WORLD_W+500, 20),
        Platform(-30,  WORLD_H-160, 20, 140, (90, 90, 110)),
        Platform(190,  WORLD_H-110, 120, 20),
        Platform(440,  WORLD_H-185, 120, 20),
        Platform(690,  WORLD_H-150, 120, 20),
        Platform(940,  WORLD_H-225, 120, 20),
        Platform(1190, WORLD_H-165, 120, 20),
        Platform(1440, WORLD_H-130, 120, 20),
    ])

    goals.append(Goal(1460, WORLD_H-182))

    spikes.extend([
        *[Spike(x, WORLD_H-40) for x in range(120,  278, 20)],
        *[Spike(x, WORLD_H-40) for x in range(340,  528, 20)],
        *[Spike(x, WORLD_H-40) for x in range(590,  778, 20)],
        *[Spike(x, WORLD_H-40) for x in range(840,  1028, 20)],
        *[Spike(x, WORLD_H-40) for x in range(1090, 1278, 20)],
        *[Spike(x, WORLD_H-40) for x in range(1340, 1528, 20)],
        Spike(220,  WORLD_H-130),                            Spike(260,  WORLD_H-130),
        Spike(470,  WORLD_H-205),                            Spike(510,  WORLD_H-205),
        Spike(720,  WORLD_H-170),                            Spike(760,  WORLD_H-170),
        Spike(970,  WORLD_H-245),                            Spike(1010, WORLD_H-245),
        Spike(1220, WORLD_H-185),                            Spike(1260, WORLD_H-185),
        Spike(1470, WORLD_H-150), Spike(1490, WORLD_H-150), Spike(1510, WORLD_H-150),
    ])

    troll_zones.append(TrollZone(
        -500, 0, 460, WORLD_H,
        ["You're so easy to manipulate.", "Go back and do your tutorial again..."],
        'tutorial_1'
    ))


SCENE_ORDER = ['tutorial_1', 'tutorial_2', 'tutorial_3', 'tutorial_4',
               'level_1a', 'level_2', 'level_3', 'level_4', 'level_5']
SCENE_TITLES = {
    'tutorial_1': 'Tutorial 1',
    'tutorial_2': 'Tutorial 2',
    'tutorial_3': 'Tutorial 3',
    'tutorial_4': 'Tutorial 4',
    'level_1a':   'Level 1',
    'level_2':    'Level 2',
    'level_3':    'Level 3',
    'level_4':    'Level 4',
    'level_5':    'Level 5: BOSS',
}


# ── Init ──────────────────────────────────────────────────────────────────────

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((W, H))
clock  = pygame.time.Clock()

font_sign  = pygame.font.SysFont('arial', 9)
font_label = pygame.font.SysFont('arial', 15)
font_big   = pygame.font.SysFont('arial', 26, bold=True)

snd_jump = pygame.mixer.Sound('assets/jump.wav')
snd_coin = pygame.mixer.Sound('assets/coin.wav')
snd_die  = pygame.mixer.Sound('assets/die.wav')
snd_win  = pygame.mixer.Sound('assets/wingame.wav')
all_sounds = [snd_jump, snd_coin, snd_die, snd_win]
muted = False

player = Player()
load_scene('tutorial_1')

# ── Main loop ─────────────────────────────────────────────────────────────────

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            muted = not muted
            vol = 0 if muted else 1
            for s in all_sounds:
                s.set_volume(vol)

    if overlay_timer > 0:
        overlay_timer -= 1
        if overlay_timer == 0:
            load_scene(overlay_next)
    else:
        player.move()

        for swing in swings:
            swing.move()
        for enemy in enemies:
            enemy.move()

        if any(s.check_collision(player) for s in swings):
            snd_die.play()
            player.reset()

        for spike in spikes:
            if spike.check_collision(player):
                snd_die.play()
                player.reset()
                break

        for liquid in liquids:
            if liquid.check_collision(player):
                snd_die.play()
                player.reset()
                break

        for pad in jumppads:
            pad.check_collision(player)

        for enemy in enemies:
            result = enemy.check_collision(player)
            if result == 'hit':
                snd_die.play()
                player.reset()
                break

        if idle_target > 0 and not idle_reveal:
            keys = pygame.key.get_pressed()
            moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP]
            if not moving and player.on_ground:
                idle_frames += 1
                if idle_frames >= idle_target:
                    idle_reveal = True
                    toast_text = 'Stillness reveals the path.'
            else:
                idle_frames = 0

        for coin in coins:
            if coin.check_collision(player):
                snd_coin.play()

        for cp in checkpoints:
            if cp.check_collision(player):
                spawn_x, spawn_y = cp.x - 14, cp.y - 4

        for tz in troll_zones:
            if tz.check_collision(player):
                show_overlay(tz.message, 220, tz.next_scene)
                break

        for goal in goals:
            if goal.check_collision(player):
                if idle_target > 0 and not idle_reveal:
                    continue
                idx = SCENE_ORDER.index(scene)
                snd_win.play()
                if idx + 1 < len(SCENE_ORDER):
                    nxt = SCENE_ORDER[idx + 1]
                    show_overlay([SCENE_TITLES[nxt]], 90, nxt)
                else:
                    show_overlay(['You win.'], 180, 'tutorial_1')
                break

    screen.fill((10, 20, 50))

    cam_x = max(0, min(player.rect.x - W//2, WORLD_W - W))
    cam_y = max(0, min(player.rect.y - H//2, WORLD_H - H))

    for p  in platforms:   p.draw(cam_x, cam_y)
    for d  in decor:       d.draw(cam_x, cam_y)
    for lq in liquids:     lq.draw(cam_x, cam_y)
    for jp in jumppads:    jp.draw(cam_x, cam_y)
    for sp in spikes:      sp.draw(cam_x, cam_y)
    for c  in coins:       c.draw(cam_x, cam_y)
    for cp in checkpoints: cp.draw(cam_x, cam_y)
    for g  in goals:
        if scene == 'level_4' and idle_target > 0 and not idle_reveal:
            continue
        g.draw(cam_x, cam_y)
    for sg in signs:       sg.draw(cam_x, cam_y, font_sign)
    for lb in labels:      lb.draw(cam_x, cam_y, font_label)
    for en in enemies:     en.draw(cam_x, cam_y)
    for sw in swings:      sw.draw(cam_x, cam_y)
    player.draw(cam_x, cam_y)

    if toast_text:
        toast_surf = font_label.render(toast_text, True, (220, 220, 230))
        toast_surf.set_alpha(180)
        screen.blit(toast_surf, (W - toast_surf.get_width() - 14, 14))

    mute_surf = font_label.render('M mute' if not muted else 'M unmute', True, (120, 120, 140))
    mute_surf.set_alpha(140)
    screen.blit(mute_surf, (8, 8))

    if overlay_timer > 0:
        alpha = min(255, (220 - overlay_timer) * 8)
        for i, line in enumerate(overlay_lines):
            surf = font_big.render(line, True, (255, 255, 200))
            surf.set_alpha(alpha)
            screen.blit(surf, (W//2 - surf.get_width()//2, H//2 - 20 + i*36))

    pygame.display.flip()
    clock.tick(60)
