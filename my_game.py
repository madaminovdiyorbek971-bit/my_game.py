import pygame, random, sys, os, math
from array import array

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
W, H = 480, 800
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

PIPE_W = 80
CAP_H = 32
GROUND = H - 70

# ---- Bosqichlar ----
STAGES = [
    {"count": 20, "speed": 4, "gap": 200, "every": 90, "boss": 0},
    {"count": 40, "speed": 5, "gap": 175, "every": 72, "boss": 0},
    {"count": 30, "speed": 6, "gap": 165, "every": 66, "boss": 6},
]

settings = {"sound": True, "color": 0}

# nomi, tana, chegara, qanot
PALS = [
    ("Sariq", (255, 200, 0), (230, 150, 0), (255, 235, 120)),
    ("Qizil", (235, 80, 80), (170, 40, 40), (255, 170, 170)),
    ("Ko'k", (70, 140, 255), (30, 80, 190), (170, 205, 255)),
    ("Yashil", (90, 200, 110), (40, 130, 60), (190, 240, 190)),
    ("Binafsha", (170, 100, 230), (110, 50, 170), (220, 185, 250)),
]

GREEN_PIPE = ((76, 175, 80), (129, 199, 132), (46, 125, 50), (27, 94, 32))
RED_PIPE = ((225, 75, 75), (245, 140, 140), (165, 40, 40), (110, 20, 20))

BTN_GREEN = (70, 185, 90)
BTN_BLUE = (60, 140, 230)
BTN_RED = (225, 75, 75)
BTN_GRAY = (120, 130, 150)

_fonts = {}


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]


# ---- Rekord saqlash ----
try:
    BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE = os.getcwd()
REC_FILE = os.path.join(BASE, "rekord.txt")


def load_record():
    try:
        with open(REC_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_record(n):
    try:
        with open(REC_FILE, "w") as f:
            f.write(str(n))
    except Exception:
        pass


record = load_record()

# ---- Tovushlar (koddan yasaladi) ----
RATE = 44100


def gen(f1, f2, dur, vol=0.35):
    n = int(RATE * dur)
    buf = array('h')
    ph = 0.0
    for i in range(n):
        t = i / n
        ph += 2 * math.pi * (f1 + (f2 - f1) * t) / RATE
        buf.append(int(math.sin(ph) * vol * (1 - t) * 32767))
    return buf


def make_sound(*parts):
    try:
        data = array('h')
        for p in parts:
            data.extend(p)
        return pygame.mixer.Sound(buffer=data.tobytes())
    except Exception:
        return None


def play(s):
    if s and settings["sound"]:
        s.play()


S_FLAP = make_sound(gen(450, 750, 0.10))
S_POINT = make_sound(gen(900, 1300, 0.12, 0.3))
S_HIT = make_sound(gen(300, 80, 0.30, 0.5))
S_CLICK = make_sound(gen(700, 900, 0.06, 0.25))
S_STAGE = make_sound(gen(500, 500, 0.10), gen(700, 700, 0.10), gen(900, 900, 0.15))
S_WIN = make_sound(gen(523, 523, 0.15), gen(659, 659, 0.15),
                   gen(784, 784, 0.15), gen(1047, 1047, 0.30))


def click():
    play(S_CLICK)


# ---- Qush ----
def make_bird(flap, pal):
    _, body, edge, wing = pal
    s = pygame.Surface((48, 38), pygame.SRCALPHA)
    pygame.draw.ellipse(s, body, (2, 4, 38, 30))
    pygame.draw.ellipse(s, edge, (2, 4, 38, 30), 3)
    wy = 12 if flap else 21
    pygame.draw.ellipse(s, wing, (6, wy, 18, 12))
    pygame.draw.ellipse(s, edge, (6, wy, 18, 12), 2)
    pygame.draw.circle(s, (255, 255, 255), (30, 14), 7)
    pygame.draw.circle(s, (0, 0, 0), (32, 14), 3)
    pygame.draw.polygon(s, (255, 90, 30), [(38, 18), (47, 21), (38, 26)])
    return s


BIRDS = []


def build_birds():
    global BIRDS
    pal = PALS[settings["color"]]
    BIRDS = [make_bird(False, pal), make_bird(True, pal)]


build_birds()


def draw_bird(cx, cy, angle, idx, scale=1.0):
    img = BIRDS[idx]
    if scale != 1.0:
        img = pygame.transform.scale(img, (int(48 * scale), int(38 * scale)))
    rot = pygame.transform.rotate(img, angle)
    screen.blit(rot, rot.get_rect(center=(cx, cy)))


# ---- Chizish yordamchilari ----
def draw_text(s, size, color, cx, cy, maxw=None):
    f = get_font(size)
    if maxw:
        while f.size(s)[0] > maxw and size > 16:
            size -= 2
            f = get_font(size)
    sh = f.render(s, True, (25, 30, 60))
    screen.blit(sh, sh.get_rect(center=(cx + 3, cy + 3)))
    t = f.render(s, True, color)
    screen.blit(t, t.get_rect(center=(cx, cy)))


def btn(cx, cy, w=300, h=68):
    return pygame.Rect(cx - w // 2, cy - h // 2, w, h)


def draw_button(rect, label, color, pulse=False):
    r = rect.copy()
    if pulse:
        k = math.sin(pygame.time.get_ticks() / 180)
        r.inflate_ip(int(10 * k), int(5 * k))
    dark = tuple(max(0, c - 70) for c in color)
    light = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(screen, dark, r.move(0, 6), border_radius=20)
    pygame.draw.rect(screen, color, r, border_radius=20)
    pygame.draw.rect(screen, light, r, 3, border_radius=20)
    draw_text(label, 44, (255, 255, 255), r.centerx, r.centery, r.width - 30)


def draw_star(cx, cy, r, color=(255, 215, 40)):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, (200, 140, 0), pts, 3)


def draw_pipe(x, y, h, cap_at_bottom, pal):
    if h <= 0:
        return
    main, light, dark, edge = pal
    pygame.draw.rect(screen, main, (x + 6, y, PIPE_W - 12, h))
    pygame.draw.rect(screen, light, (x + 14, y, 10, h))
    pygame.draw.rect(screen, dark, (x + PIPE_W - 24, y, 10, h))
    cap_y = y + h - CAP_H if cap_at_bottom else y
    cap = pygame.Rect(x, cap_y, PIPE_W, CAP_H)
    pygame.draw.rect(screen, main, cap, border_radius=6)
    pygame.draw.rect(screen, light, (x + 8, cap_y + 5, 10, CAP_H - 10))
    pygame.draw.rect(screen, edge, cap, 3, border_radius=6)


def draw_cloud(x, y):
    for dx, dy, r in ((0, 0, 24), (26, -10, 30), (56, 0, 24), (28, 8, 26)):
        pygame.draw.circle(screen, (255, 255, 255), (int(x + dx), int(y + dy)), r)


clouds = [[random.randint(0, W), random.randint(60, 400), random.uniform(0.3, 0.9)]
          for _ in range(5)]

# ---- Konfetti ----
CONF_COLORS = [(255, 80, 80), (255, 215, 60), (80, 200, 120), (80, 160, 255), (220, 120, 255)]
confetti = []


def spawn_confetti(n):
    confetti.clear()
    for _ in range(n):
        confetti.append([random.uniform(0, W), random.uniform(-H, 0),
                         random.uniform(2, 5), random.choice(CONF_COLORS),
                         random.randint(7, 12), random.uniform(0, 6.28)])


def draw_confetti():
    for c in confetti:
        c[1] += c[2]
        c[0] += math.sin(c[5] + c[1] / 25) * 1.5
        if c[1] > H:
            c[1] = -10
            c[0] = random.uniform(0, W)
        pygame.draw.rect(screen, c[3], (int(c[0]), int(c[1]), c[4], c[4] // 2 + 3))


DIM = pygame.Surface((W, H), pygame.SRCALPHA)
DIM.fill((0, 0, 0, 150))


def draw_panel(title, color, size=60, with_confetti=False):
    screen.blit(DIM, (0, 0))
    if with_confetti:
        draw_confetti()
    r = pygame.Rect(50, 190, 380, 420)
    pygame.draw.rect(screen, (30, 40, 78), r, border_radius=28)
    pygame.draw.rect(screen, (255, 215, 80), r, 6, border_radius=28)
    draw_text(title, size, color, W // 2, 250, 340)


# ---- Tugmalar joylashuvi ----
M_PLAY = btn(W // 2, 430)
M_SET = btn(W // 2, 520)
M_QUIT = btn(W // 2, 610)

S_SOUND_B = btn(W // 2, 300, 380)
S_COLOR_B = btn(W // 2, 400, 380)
S_BACK = btn(W // 2, 640)

B_A = btn(W // 2, 470)
B_B = btn(W // 2, 550)

MENU_ICON = pygame.Rect(W - 72, 12, 56, 56)
MENU_HIT = MENU_ICON.inflate(24, 24)

# ---- O'yin holati ----
bird = pygame.Rect(100, H // 2, 34, 28)
vel = 0
pipes = []
score = 0
frame = 0
spawned = 0
stage = 1
banner = 0
end_time = 0
state = "menu"   # menu, settings, ready, play, paused, dead, stage_clear, win
paused_from = "play"
mouse_seen = False
last_tap = -1000


def target_score(st):
    return sum(s["count"] for s in STAGES[:st])


def start(st):
    global bird, vel, pipes, score, frame, spawned, stage, banner, state
    stage = st
    bird = pygame.Rect(100, H // 2, 34, 28)
    vel = 0
    pipes = []
    frame = 0
    spawned = 0
    banner = 0
    score = target_score(st - 1)
    state = "ready"
    confetti.clear()


def go_menu():
    global state
    state = "menu"
    confetti.clear()


def update_record():
    global record
    if score > record:
        record = score
        save_record(record)


def die():
    global state, end_time
    state = "dead"
    end_time = pygame.time.get_ticks()
    update_record()
    play(S_HIT)


# ---- Bosishlarni qabul qilish ----
def get_tap(e):
    global mouse_seen, last_tap
    if e.type == pygame.MOUSEBUTTONDOWN:
        if getattr(e, "button", 1) != 1:
            return None
        mouse_seen = True
        pos = e.pos
    elif e.type == pygame.FINGERDOWN and not mouse_seen:
        x, y = e.x, e.y
        if x <= 1.0 and y <= 1.0:
            x, y = x * W, y * H
        pos = (x, y)
    else:
        return None
    now = pygame.time.get_ticks()
    if now - last_tap < 120:      # ikki marta hisoblanmasin
        return None
    last_tap = now
    return pos


def handle_tap(pos):
    global state, vel, paused_from
    ok = pygame.time.get_ticks() - end_time > 600   # tasodifiy bosishdan himoya

    if state == "menu":
        if M_PLAY.collidepoint(pos):
            click(); start(1)
        elif M_SET.collidepoint(pos):
            click(); state = "settings"
        elif M_QUIT.collidepoint(pos):
            pygame.quit(); sys.exit()

    elif state == "settings":
        if S_SOUND_B.collidepoint(pos):
            settings["sound"] = not settings["sound"]
            click()
        elif S_COLOR_B.collidepoint(pos):
            settings["color"] = (settings["color"] + 1) % len(PALS)
            build_birds()
            click()
        elif S_BACK.collidepoint(pos):
            click(); state = "menu"

    elif state in ("ready", "play"):
        if MENU_HIT.collidepoint(pos):
            click()
            paused_from = state
            state = "paused"
        else:
            state = "play"
            vel = -9
            play(S_FLAP)

    elif state == "paused":
        if B_A.collidepoint(pos):
            click(); state = paused_from
        elif B_B.collidepoint(pos):
            click(); go_menu()

    elif state == "dead" and ok:
        if B_A.collidepoint(pos):
            click(); start(stage)
        elif B_B.collidepoint(pos):
            click(); go_menu()

    elif state == "stage_clear" and ok:
        if B_A.collidepoint(pos):
            click(); start(stage + 1)
        elif B_B.collidepoint(pos):
            click(); go_menu()

    elif state == "win" and ok:
        if B_A.collidepoint(pos):
            click(); start(1)
        elif B_B.collidepoint(pos):
            click(); go_menu()


# ---- Yangilash ----
def update():
    global vel, frame, spawned, state, end_time, score, pipes, banner

    for c in clouds:
        c[0] -= c[2]
        if c[0] < -100:
            c[0] = W + 50
            c[1] = random.randint(60, 400)

    if state == "play":
        cfg = STAGES[stage - 1]
        vel += 0.5
        bird.y += int(vel)
        frame += 1
        if banner > 0:
            banner -= 1

        if spawned < cfg["count"] and frame % cfg["every"] == 0:
            spawned += 1
            is_boss = spawned > cfg["count"] - cfg["boss"]
            g = cfg["gap"] + (15 if is_boss else 0)
            amp = 55 if is_boss else 0
            pipes.append({
                "x": W, "gap": g, "boss": is_boss, "amp": amp,
                "base": random.randint(120 + amp, GROUND - g - 120 - amp),
                "phase": random.uniform(0, 6.28), "ty": 0, "passed": False})
            if is_boss and spawned == cfg["count"] - cfg["boss"] + 1:
                banner = 120

        for p in pipes:
            p["x"] -= cfg["speed"]
            p["phase"] += 0.05
            p["ty"] = p["base"] + p["amp"] * math.sin(p["phase"])
            ty = int(p["ty"])
            top_r = pygame.Rect(p["x"], 0, PIPE_W, ty)
            bot_r = pygame.Rect(p["x"], ty + p["gap"], PIPE_W, GROUND)
            if bird.colliderect(top_r) or bird.colliderect(bot_r):
                die()
                break
            if not p["passed"] and p["x"] + PIPE_W < bird.x:
                p["passed"] = True
                score += 1
                play(S_POINT)

        pipes = [p for p in pipes if p["x"] > -PIPE_W]

        if state == "play" and (bird.top < 0 or bird.bottom > GROUND):
            die()

        if state == "play" and score >= target_score(stage):
            end_time = pygame.time.get_ticks()
            update_record()
            if stage < len(STAGES):
                state = "stage_clear"
                spawn_confetti(70)
                play(S_STAGE)
            else:
                state = "win"
                spawn_confetti(150)
                play(S_WIN)

    elif state == "dead":
        if bird.bottom < GROUND:
            vel += 0.5
            bird.y = min(bird.y + int(vel), GROUND - bird.height)


# ---- Chizish ----
def draw_backdrop():
    screen.fill((120, 205, 255))
    for c in clouds:
        draw_cloud(c[0], c[1])


def draw_ground():
    pygame.draw.rect(screen, (222, 184, 110), (0, GROUND, W, H - GROUND))
    pygame.draw.rect(screen, (110, 190, 70), (0, GROUND, W, 14))


def draw_menu_icon():
    s = pygame.Surface((56, 56), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 110), (0, 0, 56, 56), border_radius=12)
    for i in range(3):
        pygame.draw.rect(s, (255, 255, 255), (13, 14 + i * 12, 30, 5), border_radius=3)
    screen.blit(s, MENU_ICON.topleft)


def draw_world():
    draw_backdrop()
    for p in pipes:
        pal = RED_PIPE if p["boss"] else GREEN_PIPE
        ty = int(p["ty"])
        draw_pipe(p["x"], 0, ty, True, pal)
        by = ty + p["gap"]
        draw_pipe(p["x"], by, GROUND - by, False, pal)
    draw_ground()

    t = pygame.time.get_ticks()
    cy = bird.centery
    if state == "ready":
        cy += int(8 * math.sin(t / 200))
        idx = (t // 120) % 2
    else:
        idx = (frame // 6) % 2
    angle = max(-70, min(35, -vel * 4))
    draw_bird(bird.centerx, cy, angle, idx)

    draw_text(str(score), 84, (255, 255, 255), W // 2, 60)
    rec = get_font(38).render("Rekord: " + str(record), True, (255, 255, 255))
    screen.blit(rec, (15, 15))

    if banner > 0:
        draw_text("BOSS ustunlar!", 56, (255, 90, 90), W // 2, 150)

    if state in ("ready", "play"):
        draw_menu_icon()


def draw_main_menu():
    t = pygame.time.get_ticks()
    draw_text("FLAPPY", 120, (255, 215, 60), W // 2, 140)
    draw_text("BIRD", 120, (255, 255, 255), W // 2, 235)
    draw_bird(W // 2, 330 + int(8 * math.sin(t / 250)), 8 * math.sin(t / 400),
              (t // 120) % 2, 2.0)
    draw_button(M_PLAY, "Boshlash", BTN_GREEN)
    draw_button(M_SET, "Sozlamalar", BTN_BLUE)
    draw_button(M_QUIT, "Chiqish", BTN_RED)
    draw_text("Rekord: " + str(record), 40, (255, 255, 255), W // 2, 685)


def draw_settings():
    t = pygame.time.get_ticks()
    draw_text("Sozlamalar", 80, (255, 255, 255), W // 2, 150)
    snd = "Yoqilgan" if settings["sound"] else "O'chiq"
    draw_button(S_SOUND_B, "Tovush: " + snd,
                BTN_GREEN if settings["sound"] else BTN_GRAY)
    pal = PALS[settings["color"]]
    draw_button(S_COLOR_B, "Qush rangi: " + pal[0], pal[1])
    draw_bird(W // 2, 520 + int(6 * math.sin(t / 250)), 0, (t // 120) % 2, 2.2)
    draw_button(S_BACK, "Orqaga", BTN_BLUE)


def draw_overlay():
    t = pygame.time.get_ticks()
    if state == "paused":
        draw_panel("Pauza", (255, 255, 255), 72)
        draw_text("Ball: " + str(score), 52, (255, 255, 255), W // 2, 350)
        draw_button(B_A, "Davom etish", BTN_GREEN, True)
        draw_button(B_B, "Chiqish", BTN_RED)

    elif state == "dead":
        draw_panel("Yutqazdingiz!", (255, 90, 90), 64)
        draw_text("Ball: " + str(score), 56, (255, 255, 255), W // 2, 340)
        draw_text("Rekord: " + str(record), 42, (255, 215, 80), W // 2, 392)
        draw_button(B_A, "Qayta urinish", BTN_GREEN, True)
        draw_button(B_B, "Menyu", BTN_BLUE)

    elif state == "stage_clear":
        draw_panel(str(stage) + "-bosqich yutildi!", (255, 215, 80), 56, True)
        bob = int(5 * math.sin(t / 200))
        draw_star(W // 2 - 85, 320 + bob, 30)
        draw_star(W // 2, 310 - bob, 42)
        draw_star(W // 2 + 85, 320 + bob, 30)
        draw_text("Ball: " + str(score), 48, (255, 255, 255), W // 2, 395)
        draw_button(B_A, "Keyingi bosqich", BTN_GREEN, True)
        draw_button(B_B, "Chiqish", BTN_RED)

    elif state == "win":
        draw_panel("G'ALABA!", (255, 215, 80), 84, True)
        bob = int(6 * math.sin(t / 180))
        draw_star(W // 2 - 90, 322 + bob, 32)
        draw_star(W // 2, 310 - bob, 46)
        draw_star(W // 2 + 90, 322 + bob, 32)
        draw_text("Ball: " + str(score), 44, (255, 255, 255), W // 2, 385)
        draw_text("Rekord: " + str(record), 38, (255, 215, 80), W // 2, 418)
        draw_button(B_A, "Qayta o'ynash", BTN_GREEN, True)
        draw_button(B_B, "Chiqish", BTN_RED)


def draw():
    if state in ("menu", "settings"):
        draw_backdrop()
        draw_ground()
        if state == "menu":
            draw_main_menu()
        else:
            draw_settings()
        return

    draw_world()

    if state == "ready":
        draw_text(str(stage) + "-bosqich", 64, (255, 255, 255), W // 2, 210)
        if STAGES[stage - 1]["boss"]:
            draw_text("Boss ustunlardan ehtiyot bo'ling!", 38, (255, 120, 120),
                      W // 2, 270, 440)
        draw_text("Boshlash uchun bosing", 46, (255, 255, 255), W // 2, 600, 440)
    else:
        draw_overlay()


while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        pos = get_tap(e)
        if pos is not None:
            handle_tap(pos)

    update()
    draw()
    pygame.display.flip()
    clock.tick(60)