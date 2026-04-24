import pygame
import random
import sys
import os

pygame.init()
pygame.mixer.init()

# FULL SCREEN
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Waste Segregation Challenge")

clock = pygame.time.Clock()
font_big   = pygame.font.SysFont(None, 72)
font_med   = pygame.font.SysFont(None, 48)
font_small = pygame.font.SysFont(None, 38)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def load_image(path, size=None):
    img = pygame.image.load(path)
    if size:
        img = pygame.transform.scale(img, size)
    return img.convert_alpha() if img.get_flags() & pygame.SRCALPHA else img.convert()

def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        class Dummy:
            def play(self): pass
        return Dummy()

# ─────────────────────────────────────────────
#  ASSETS
# ─────────────────────────────────────────────
ASSET_IMG = "assets/images/"
ASSET_SND = "assets/sounds/"

bg_img        = load_image(ASSET_IMG + "bg.jpeg",         (WIDTH, HEIGHT))
start_img     = load_image(ASSET_IMG + "start.jpeg",      (WIDTH, HEIGHT))
gameover_img  = load_image(ASSET_IMG + "game_over.jpeg",  (WIDTH, HEIGHT))
nextlevel_img = load_image(ASSET_IMG + "next_level.jpeg", (WIDTH, HEIGHT))

correct_snd     = load_sound(ASSET_SND + "correct.mpeg")
wrong_snd       = load_sound(ASSET_SND + "wrong.mpeg")
click_snd       = load_sound(ASSET_SND + "click.mp3")
popup_snd       = load_sound(ASSET_SND + "popup.mp3")
celebration_snd = load_sound(ASSET_SND + "celebration.mpeg")
gameover_snd    = load_sound(ASSET_SND + "game_over.mp3")

try:
    pygame.mixer.music.load(ASSET_SND + "bg.mpeg")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except Exception:
    pass

# ─────────────────────────────────────────────
#  BIN VISUAL RECTS  (full size, for labels)
# ─────────────────────────────────────────────
BIN_VISUAL = {
    "Bio_Degradable": pygame.Rect(int(WIDTH*0.155), int(HEIGHT*0.58), int(WIDTH*0.09), int(HEIGHT*0.32)),
    "Hazardous":      pygame.Rect(int(WIDTH*0.270), int(HEIGHT*0.60), int(WIDTH*0.09), int(HEIGHT*0.32)),
    "Recycle":        pygame.Rect(int(WIDTH*0.665), int(HEIGHT*0.60), int(WIDTH*0.09), int(HEIGHT*0.32)),
    "Biomedical":     pygame.Rect(int(WIDTH*0.755), int(HEIGHT*0.58), int(WIDTH*0.09), int(HEIGHT*0.32)),
}

# Center of white arrow/opening on each bin (for level 5 tight hitbox)
BIN_ARROW_CENTER = {
    "Bio_Degradable": (int(WIDTH*0.199), int(HEIGHT*0.635)),
    "Hazardous":      (int(WIDTH*0.314), int(HEIGHT*0.655)),
    "Recycle":        (int(WIDTH*0.709), int(HEIGHT*0.655)),
    "Biomedical":     (int(WIDTH*0.800), int(HEIGHT*0.635)),
}

BIN_LABELS = {
    "Bio_Degradable": "Bio-Degradable",
    "Hazardous":      "Hazardous",
    "Recycle":        "Recycle",
    "Biomedical":     "Biomedical",
}

BIN_COLORS = {
    "Bio_Degradable": (34,  139,  34),
    "Hazardous":      (80,   80,  80),
    "Recycle":        (30,  100, 200),
    "Biomedical":     (200,  30,  30),
}

# ─────────────────────────────────────────────
#  LEVEL CONFIG
# ─────────────────────────────────────────────
def get_level_config(level):
    configs = {
        1: {"target":  5, "time": 60, "cats": ["Recycle", "Bio_Degradable"],
            "hitbox_scale": 1.00},
        2: {"target": 10, "time": 55, "cats": ["Recycle", "Bio_Degradable", "Hazardous"],
            "hitbox_scale": 0.70},
        3: {"target": 15, "time": 50, "cats": ["Recycle", "Bio_Degradable", "Hazardous", "Biomedical"],
            "hitbox_scale": 0.50},
        4: {"target": 20, "time": 50, "cats": ["Recycle", "Bio_Degradable", "Hazardous", "Biomedical"],
            "hitbox_scale": 0.50},
        5: {"target": 25, "time": 50, "cats": ["Recycle", "Bio_Degradable", "Hazardous", "Biomedical"],
            "hitbox_scale": 0.50},
    }
    return configs.get(level, configs[5])

def get_bin_hitboxes(level):
    cfg = get_level_config(level)
    scale = cfg["hitbox_scale"]
    hitboxes = {}
    for name, vis in BIN_VISUAL.items():
        w = max(20, int(vis.width  * scale))
        h = max(20, int(vis.height * scale))
        if level == 5:
            cx, cy = BIN_ARROW_CENTER[name]
        else:
            cx, cy = vis.centerx, vis.centery
        hitboxes[name] = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    return hitboxes

# ─────────────────────────────────────────────
#  WASTE DATA
# ─────────────────────────────────────────────
WASTE_SIZE = (200, 200)

def make_waste_surface(color, label):
    surf = pygame.Surface(WASTE_SIZE, pygame.SRCALPHA)
    pygame.draw.rect(surf, color, surf.get_rect(), border_radius=18)
    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 4, border_radius=18)
    inner = surf.get_rect().inflate(-10, -10)
    pygame.draw.rect(surf, (*color[:3], 160), inner, 2, border_radius=14)
    txt = font_small.render(label, True, (255, 255, 255))
    surf.blit(txt, txt.get_rect(center=(WASTE_SIZE[0]//2, WASTE_SIZE[1]//2)))
    return surf

def try_load_waste(filename, fallback_color, fallback_label):
    path = ASSET_IMG + filename
    if os.path.exists(path):
        try:
            img = pygame.image.load(path)
            img = pygame.transform.scale(img, WASTE_SIZE)
            img = img.convert_alpha() if img.get_flags() & pygame.SRCALPHA else img.convert()
            final = pygame.Surface(WASTE_SIZE, pygame.SRCALPHA)
            final.blit(img, (0, 0))
            # White border
            pygame.draw.rect(final, (255, 255, 255), final.get_rect(), 4, border_radius=14)
            # Label strip at bottom
            strip_h = 40
            strip = pygame.Surface((WASTE_SIZE[0], strip_h), pygame.SRCALPHA)
            strip.fill((0, 0, 0, 170))
            final.blit(strip, (0, WASTE_SIZE[1] - strip_h))
            lbl = font_small.render(fallback_label, True, (255, 255, 255))
            final.blit(lbl, lbl.get_rect(centerx=WASTE_SIZE[0]//2,
                                          centery=WASTE_SIZE[1] - strip_h//2))
            return final
        except Exception:
            pass
    return make_waste_surface(fallback_color, fallback_label)

waste_data = {
    "bananapeel":       ("Bio_Degradable", try_load_waste("banana-peel.png",      ( 60,180, 60), "Banana Peel")),
    "tissue":           ("Bio_Degradable", try_load_waste("tissue.png",           ( 60,180, 60), "Tissue")),
    "leaves":           ("Bio_Degradable", try_load_waste("leaves.png",           ( 40,160, 40), "Leaves")),
    "applepeel":        ("Bio_Degradable", try_load_waste("apple_peel.png",       (180, 60, 60), "Apple Peel")),
    "newspaper":        ("Bio_Degradable", try_load_waste("newspaper.png",        (220,200,150), "Newspaper")),
    "crayon":           ("Bio_Degradable", try_load_waste("crayon.png",           (200,150, 80), "Crayon")),
    "leaf_wood":        ("Bio_Degradable", try_load_waste("leaf_wood.png",        ( 40,160, 40), "Leaf/Wood")),
    "onionpeel":        ("Bio_Degradable", try_load_waste("onion-peel.png",       (180,140, 60), "Onion Peel")),
    "paperball":        ("Bio_Degradable", try_load_waste("paper_ball.png",       (220,200,150), "Paper Ball")),
    "plasticbottle":    ("Recycle",        try_load_waste("plastic_bottle.png",   ( 30,130,200), "Plastic Bottle")),
    "plasticbottle2":   ("Recycle",        try_load_waste("plastic_bottle2.png",  ( 30,130,200), "Plastic Bottle")),
    "can":              ("Recycle",        try_load_waste("can.png",              (160,160, 60), "Can")),
    "polythene":        ("Recycle",        try_load_waste("polythene.png",        ( 30,130,200), "Polythene")),
    "wrapper":          ("Recycle",        try_load_waste("wrapper.png",          ( 30,130,200), "Wrapper")),
    "wrapper2":         ("Recycle",        try_load_waste("wrapper2.png",         ( 30,130,200), "Wrapper")),
    "plasticbag":       ("Recycle",        try_load_waste("plastic_bag.png",      ( 30,130,200), "Plastic Bag")),
    "cloth":            ("Recycle",        try_load_waste("cloth.webp",           ( 30,130,200), "Cloth")),
    "disposable_glass": ("Recycle",        try_load_waste("disposable-glass.png", ( 30,130,200), "Disp. Glass")),
    "plastic_cup":      ("Recycle",        try_load_waste("plastic_cup.png",      ( 30,130,200), "Plastic Cup")),
    "cardboard":        ("Recycle",        try_load_waste("cardboard.png",        ( 30,130,200), "Cardboard")),
    "soda_can":         ("Recycle",        try_load_waste("soda_can.png",         ( 30,130,200), "Soda Can")),
    "battery":          ("Hazardous",      try_load_waste("battery.png",          ( 80, 80, 80), "Battery")),
    "blade":            ("Hazardous",      try_load_waste("blade.png",            (160, 80,200), "Blade")),
    "batteries":        ("Hazardous",      try_load_waste("batteries.png",        (160, 80,200), "Batteries")),
    "cable":            ("Hazardous",      try_load_waste("cable.png",            (160, 80,200), "Cable")),
    "glass_garbage":    ("Hazardous",      try_load_waste("glass_garbage.png",    (160, 80,200), "Broken Glass")),
    "simcard":          ("Hazardous",      try_load_waste("simcard.png",          (160, 80,200), "SIM Card")),
    "broken_bulb":      ("Hazardous",      try_load_waste("broken_bulb.webp",     (160, 80,200), "Broken Bulb")),
    "bandage":          ("Biomedical",     try_load_waste("bandage.png",          (200,200,200), "Bandage")),
    "syringe":          ("Biomedical",     try_load_waste("syringe.png",          (180,220,240), "Syringe")),
    "cotton":           ("Biomedical",     try_load_waste("cotton.png",           (200,200,200), "Cotton")),
    "medicine":         ("Biomedical",     try_load_waste("medicine.png",         (200,200,200), "Medicine")),
    "rubber":           ("Hazardous",     try_load_waste("rubber.png",           (200,200,200), "Rubber")),
    "gloves":           ("Biomedical",     try_load_waste("gloves.webp",          (200,200,200), "Gloves")),
    "mask":             ("Biomedical",     try_load_waste("mask.webp",            (200,200,200), "Mask")),
    "vials":            ("Biomedical",     try_load_waste("vials.webp",           (200,200,200), "Vials")),
}

# ─────────────────────────────────────────────
#  WASTE QUEUE
# ─────────────────────────────────────────────
def build_waste_queue(cats):
    """Shuffle all valid waste keys so no same category appears consecutively."""
    valid = [k for k, v in waste_data.items() if v[0] in cats]
    random.shuffle(valid)
    # Re-shuffle until no two adjacent items share a category
    # (max 200 attempts to avoid infinite loop with very few items)
    for _ in range(200):
        bad = False
        for i in range(1, len(valid)):
            if waste_data[valid[i]][0] == waste_data[valid[i-1]][0]:
                bad = True
                break
        if not bad:
            break
        random.shuffle(valid)
    return valid

_waste_queue = []
_last_cat    = None   # category of the last waste shown

def pick_waste(cats):
    global _waste_queue, _last_cat
    # Remove items whose category is no longer valid for this level
    _waste_queue = [k for k in _waste_queue if waste_data[k][0] in cats]
    if not _waste_queue:
        _waste_queue = build_waste_queue(cats)

    # If the front of queue has the same category as the last shown,
    # try to find a different-category item within the queue.
    if _last_cat is not None:
        for i, k in enumerate(_waste_queue):
            if waste_data[k][0] != _last_cat:
                # Swap it to the front
                _waste_queue[0], _waste_queue[i] = _waste_queue[i], _waste_queue[0]
                break
        # If every remaining item is the same category, just proceed anyway

    key = _waste_queue.pop(0)
    _last_cat = waste_data[key][0]
    return key, waste_data[key][1]

# ─────────────────────────────────────────────
#  QUESTIONS
# ─────────────────────────────────────────────
all_questions = [
   {"q": "What are the major R's of sustainability?",
     "options": ["rethink,retry,repay,retire", "refuse,reckon,remember,redo", "refuse,reduce,reuse,recycle", "repair,rethink,revenue,recycle"],
     "answer": "refuse,reduce,reuse,recycle"},
    {"q": "A fruit vendor throws spoiled fruits, plastic bags, and cardboard boxes together.Which waste can be composted?",
     "options": ["Plastic bags", "Cardboard", "Spoiled fruits", "None"],
     "answer": "Recycle"},
    {"q": "Why should plastic waste be cleaned before recycling?",
     "options": ["To avoid contamination during recycling", "To increase weight", "To reduce cost", "To make it biodegradable"],
     "answer": "To avoid contamination during recycling"},
    {"q": "Which of the following combinations is correctly matched?",
     "options": ["Battery- Green bin", "Glass bottle- Blue bin", "Vegetable peels- Blue bin", "Used mask- Green bin"],
     "answer": "Glass bottle- Blue bin"},
    {"q": "Which of the following is common misconception?",
     "options": ["All plastics are recyclable", "Wet waste can be composted", "Segragation is important", "Recycling saves resources"],
     "answer": "All plastics are recyclable"},
    {"q": "What is the main reason for color-coded bins?",
     "options": ["Easy identification and proper segragation", "Decoration", "Cost reduction", "Increase waste"],
     "answer": "Easy identification and proper segragation"},
    {"q": "What is the environmental impact of improper biomedical waste disposal?",
     "options": ["No impact", "Soil fertility increases", "Faster recycling", "Spread of infections and diseases"],
     "answer": "Spread of infections and diseases"},
    {"q": "Why is e-waste considered hazardous??",
     "options": ["It is biodegradable", " It contains toxic substances like lead and mercury", "It is heavy", " It smells bad"],
     "answer": "It contains toxic substances like lead and mercury"},
    {"q": "What is the biggest disadvantage of landfilling biodegradable waste?",
     "options": [" Smell only", " Takes space", "Produces methane gas", "Attracts insects"],
     "answer": "Produces methane gas"},
]

# ─────────────────────────────────────────────
#  QUESTION BUTTON RECTS
# ─────────────────────────────────────────────
def get_option_rects(q, box_x, box_y):
    """Compute clickable rects for options — must match draw_question_overlay layout."""
    box_w   = int(WIDTH  * 0.70)
    pad     = 30
    btn_w   = box_w - pad * 2
    btn_h   = 52
    btn_gap = 12
    # Recompute sub_y the same way draw does
    text_max_w = box_w - pad * 2
    q_lines    = []
    words      = q["q"].split(" ")
    current    = ""
    for word in words:
        test = (current + " " + word).strip()
        if pygame.font.SysFont(None, 48).size(test)[0] <= text_max_w:
            current = test
        else:
            if current:
                q_lines.append(current)
            current = word
    if current:
        q_lines.append(current)
    line_h      = pygame.font.SysFont(None, 48).get_linesize()
    q_y         = box_y + 28 + len(q_lines) * line_h
    sub_y       = q_y + 10
    btn_start_y = sub_y + pygame.font.SysFont(None, 38).get_linesize() + 14
    rects = []
    for i, opt in enumerate(q["options"]):
        bx = box_x + pad
        by = btn_start_y + i * (btn_h + btn_gap)
        rects.append((pygame.Rect(bx, by, btn_w, btn_h), opt))
    return rects

# ─────────────────────────────────────────────
#  PAUSE BUTTON
# ─────────────────────────────────────────────
PAUSE_BTN_SIZE = 56
PAUSE_BTN_RECT = pygame.Rect(WIDTH - PAUSE_BTN_SIZE - 18, 18,
                              PAUSE_BTN_SIZE, PAUSE_BTN_SIZE)

def draw_pause_button():
    s = pygame.Surface((PAUSE_BTN_SIZE, PAUSE_BTN_SIZE), pygame.SRCALPHA)
    s.fill((30, 30, 30, 200))
    screen.blit(s, PAUSE_BTN_RECT.topleft)
    pygame.draw.rect(screen, (200, 200, 200), PAUSE_BTN_RECT, 2, border_radius=10)
    bw, bh = 10, 26
    gap = 8
    total = bw * 2 + gap
    lx = PAUSE_BTN_RECT.centerx - total // 2
    ly = PAUSE_BTN_RECT.centery - bh // 2
    pygame.draw.rect(screen, (255, 255, 255), (lx,             ly, bw, bh), border_radius=3)
    pygame.draw.rect(screen, (255, 255, 255), (lx + bw + gap,  ly, bw, bh), border_radius=3)

# ─────────────────────────────────────────────
#  PAUSE OVERLAY
# ─────────────────────────────────────────────
def get_pause_menu_rects():
    box_w, box_h = 440, 310
    box_x = (WIDTH  - box_w) // 2
    box_y = (HEIGHT - box_h) // 2
    resume_rect = pygame.Rect(WIDTH//2 - 170, box_y + 130, 340, 60)
    exit_rect   = pygame.Rect(WIDTH//2 - 170, box_y + 215, 340, 60)
    return box_x, box_y, box_w, box_h, resume_rect, exit_rect

def draw_pause_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    box_x, box_y, box_w, box_h, resume_rect, exit_rect = get_pause_menu_rects()

    pygame.draw.rect(screen, (25, 25, 50),    (box_x, box_y, box_w, box_h), border_radius=22)
    pygame.draw.rect(screen, (140, 140, 255), (box_x, box_y, box_w, box_h), 3, border_radius=22)

    title = font_big.render("PAUSED", True, (255, 255, 255))
    screen.blit(title, title.get_rect(centerx=WIDTH//2, y=box_y + 28))

    mx, my = pygame.mouse.get_pos()

    r_hover = resume_rect.collidepoint(mx, my)
    pygame.draw.rect(screen, (50, 200, 80) if r_hover else (35, 150, 60),
                     resume_rect, border_radius=12)
    pygame.draw.rect(screen, (150, 255, 150), resume_rect, 2, border_radius=12)
    r_surf = font_med.render("▶   Resume", True, (255, 255, 255))
    screen.blit(r_surf, r_surf.get_rect(center=resume_rect.center))

    e_hover = exit_rect.collidepoint(mx, my)
    pygame.draw.rect(screen, (210, 50, 50) if e_hover else (160, 30, 30),
                     exit_rect, border_radius=12)
    pygame.draw.rect(screen, (255, 150, 150), exit_rect, 2, border_radius=12)
    e_surf = font_med.render("✕   Exit Game", True, (255, 255, 255))
    screen.blit(e_surf, e_surf.get_rect(center=exit_rect.center))

# ─────────────────────────────────────────────
#  GAME STATE
# ─────────────────────────────────────────────
CENTER = (WIDTH // 2, HEIGHT // 2)

class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        global _waste_queue, _last_cat
        _waste_queue = []
        _last_cat    = None

        self.state       = "start"
        self.score       = 0
        self.level       = 1
        self.items_done  = 0
        self.start_ticks = 0
        self.elapsed_before_pause = 0
        self.cfg  = get_level_config(1)
        self.bins = get_bin_hitboxes(1)

        self.waste_key, self.waste_surf = pick_waste(self.cfg["cats"])
        self.waste_pos   = list(CENTER)
        self.moving      = False
        self.move_target = None

        self.shake        = False
        self.shake_timer  = 0
        self.shake_origin = list(CENTER)

        self.current_q        = random.choice(all_questions)
        self.q_feedback       = ""
        self.q_feedback_timer = 0

    def get_time_left(self):
        elapsed = self.elapsed_before_pause + \
                  (pygame.time.get_ticks() - self.start_ticks) // 1000
        return max(0, self.cfg["time"] - elapsed)

    def do_pause(self):
        self.elapsed_before_pause += \
            (pygame.time.get_ticks() - self.start_ticks) // 1000
        self.start_ticks = pygame.time.get_ticks()   # reset so no bleed on resume

    def do_resume(self):
        self.start_ticks = pygame.time.get_ticks()

gs = GameState()

# ─────────────────────────────────────────────
#  DRAW HELPERS
# ─────────────────────────────────────────────
def draw_text_shadow(surf, text, font, color, pos):
    shadow = font.render(text, True, (0, 0, 0))
    surf.blit(shadow, (pos[0]+2, pos[1]+2))
    main = font.render(text, True, color)
    surf.blit(main, pos)

def draw_hud():
    draw_text_shadow(screen, f"Score: {gs.score}", font_med, (255, 255, 255), (20, 20))
    time_left = gs.get_time_left()
    col = (255, 80, 80) if time_left <= 10 else (255, 220, 50)
    draw_text_shadow(screen, f"Time: {time_left}s", font_med, col,
                     (WIDTH - PAUSE_BTN_SIZE - 230, 20))
    draw_text_shadow(screen, f"Level: {gs.level}/5", font_med, (100, 200, 255),
                     (WIDTH//2 - 70, 20))
    draw_text_shadow(screen, f"{gs.items_done}/{gs.cfg['target']} sorted",
                     font_small, (200, 255, 200), (WIDTH//2 - 90, 72))

def draw_bin_labels():
    for name, vis in BIN_VISUAL.items():
        label  = BIN_LABELS[name]
        color  = BIN_COLORS[name]
        lbl_surf = font_small.render(label, True, (255, 255, 255))
        lbl_rect = lbl_surf.get_rect(centerx=vis.centerx, top=vis.bottom + 6)
        bg_rect  = lbl_rect.inflate(16, 10)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((*color, 215))
        pygame.draw.rect(s, (255, 255, 255, 90), s.get_rect(), 2, border_radius=7)
        screen.blit(s, bg_rect)
        screen.blit(lbl_surf, lbl_rect)

def draw_waste():
    rect = gs.waste_surf.get_rect(
        center=(int(gs.waste_pos[0]), int(gs.waste_pos[1])))
    screen.blit(gs.waste_surf, rect)

def wrap_text(text, font, max_width):
    """Split text into lines that fit within max_width."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_question_overlay():
    q = gs.current_q
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    box_w = int(WIDTH  * 0.70)
    box_h = int(HEIGHT * 0.80)
    box_x = (WIDTH  - box_w) // 2
    box_y = (HEIGHT - box_h) // 2
    pygame.draw.rect(screen, (255, 248, 220), (box_x, box_y, box_w, box_h), border_radius=20)
    pygame.draw.rect(screen, (200, 140,  50), (box_x, box_y, box_w, box_h), 3, border_radius=20)

    # ── Question text with word wrap ──
    pad = 30
    text_max_w = box_w - pad * 2
    q_lines = wrap_text(q["q"], font_med, text_max_w)
    line_h  = font_med.get_linesize()
    q_y     = box_y + 28
    for line in q_lines:
        ls = font_med.render(line, True, (60, 30, 0))
        screen.blit(ls, ls.get_rect(centerx=WIDTH // 2, y=q_y))
        q_y += line_h

    sub_y = q_y + 10
    sub = font_small.render("Click an option to answer:", True, (100, 80, 40))
    screen.blit(sub, sub.get_rect(centerx=WIDTH//2, y=sub_y))

    # ── Option buttons – sized to fit inside box ──
    btn_w   = box_w - pad * 2
    btn_h   = 52
    btn_gap = 12
    btn_start_y = sub_y + font_small.get_linesize() + 14
    mx, my  = pygame.mouse.get_pos()

    for i, opt in enumerate(q["options"]):
        bx      = box_x + pad
        by      = btn_start_y + i * (btn_h + btn_gap)
        btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
        hover    = btn_rect.collidepoint(mx, my)
        pygame.draw.rect(screen, (180, 220, 255) if hover else (220, 240, 255),
                         btn_rect, border_radius=10)
        pygame.draw.rect(screen, (80, 120, 200), btn_rect, 2, border_radius=10)
        # Wrap option text if needed
        opt_lines = wrap_text(opt, font_small, btn_w - 20)
        opt_line_h = font_small.get_linesize()
        total_opt_h = len(opt_lines) * opt_line_h
        oy = btn_rect.centery - total_opt_h // 2
        for ol in opt_lines:
            os_ = font_small.render(ol, True, (40, 40, 120))
            screen.blit(os_, os_.get_rect(centerx=btn_rect.centerx, y=oy))
            oy += opt_line_h

    if gs.q_feedback:
        fb_color = (0, 160, 0) if gs.q_feedback == "correct" else (200, 0, 0)
        fb_surf  = font_big.render(gs.q_feedback.upper() + "!", True, fb_color)
        screen.blit(fb_surf, fb_surf.get_rect(centerx=WIDTH//2, y=box_y + box_h - 75))

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
running = True
paused  = False

while running:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        # ── START SCREEN ──
        if gs.state == "start":
            if event.type == pygame.MOUSEBUTTONDOWN:
                click_snd.play()
                gs.state = "playing"
                gs.start_ticks = pygame.time.get_ticks()

        # ── PAUSE MENU (takes priority while paused) ──
        elif paused:
            if event.type == pygame.MOUSEBUTTONDOWN:
                _, _, _, _, resume_rect, exit_rect = get_pause_menu_rects()
                if resume_rect.collidepoint(event.pos):
                    paused = False
                    gs.do_resume()
                elif exit_rect.collidepoint(event.pos):
                    running = False

        # ── PLAYING ──
        elif gs.state == "playing":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PAUSE_BTN_RECT.collidepoint(event.pos):
                    paused = True
                    gs.do_pause()
                elif not gs.moving and not gs.shake:
                    mx, my = event.pos
                    for bin_name, bin_rect in gs.bins.items():
                        if bin_rect.collidepoint(mx, my):
                            correct_cat = waste_data[gs.waste_key][0]
                            if bin_name == correct_cat:
                                correct_snd.play()
                                gs.moving      = True
                                gs.move_target = list(bin_rect.center)
                                gs.items_done += 1
                                gs.score      += 10
                            else:
                                wrong_snd.play()
                                gs.shake        = True
                                gs.shake_timer  = 20
                                gs.shake_origin = list(gs.waste_pos)
                                gs.score        = max(0, gs.score - 5)
                            break

        # ── QUESTION ──
        elif gs.state == "question":
            if gs.q_feedback_timer <= 0:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    q = gs.current_q
                    box_w = int(WIDTH  * 0.70)
                    box_h = int(HEIGHT * 0.80)
                    box_x = (WIDTH  - box_w) // 2
                    box_y = (HEIGHT - box_h) // 2
                    for rect, opt_text in get_option_rects(q, box_x, box_y):
                        if rect.collidepoint(event.pos):
                            if opt_text == q["answer"]:
                                celebration_snd.play()
                                gs.q_feedback = "correct"
                                gs.q_feedback_timer = 90
                            else:
                                wrong_snd.play()
                                gs.q_feedback = "wrong"
                                gs.q_feedback_timer = 70
                            break

        # ── NEXT LEVEL ──
        elif gs.state == "next_level":
            if event.type == pygame.MOUSEBUTTONDOWN:
                gs.state      = "playing"
                gs.items_done = 0
                gs.elapsed_before_pause = 0
                gs.start_ticks = pygame.time.get_ticks()
                gs.cfg  = get_level_config(gs.level)
                gs.bins = get_bin_hitboxes(gs.level)
                gs.waste_key, gs.waste_surf = pick_waste(gs.cfg["cats"])
                gs.waste_pos = list(CENTER)

        # ── GAME OVER ──
        elif gs.state == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx > WIDTH * 0.5:
                    gs.reset()
                    gs.state = "playing"
                    gs.start_ticks = pygame.time.get_ticks()
                else:
                    running = False

    # ─────────────────────────────────────────
    #  UPDATE  (skip if paused)
    # ─────────────────────────────────────────
    if not paused and gs.state == "playing":
        if gs.get_time_left() <= 0:
            gs.state = "game_over"
            gameover_snd.play()

        if gs.moving and gs.move_target:
            dx = gs.move_target[0] - gs.waste_pos[0]
            dy = gs.move_target[1] - gs.waste_pos[1]
            gs.waste_pos[0] += dx * 0.18
            gs.waste_pos[1] += dy * 0.18
            if abs(dx) < 4 and abs(dy) < 4:
                gs.moving      = False
                gs.move_target = None
                gs.waste_key, gs.waste_surf = pick_waste(gs.cfg["cats"])
                gs.waste_pos = list(CENTER)
                if gs.items_done >= gs.cfg["target"]:
                    popup_snd.play()
                    gs.current_q        = random.choice(all_questions)
                    gs.q_feedback       = ""
                    gs.q_feedback_timer = 0
                    gs.state            = "question"

        if gs.shake:
            gs.waste_pos[0] = gs.shake_origin[0] + random.randint(-6, 6)
            gs.waste_pos[1] = gs.shake_origin[1] + random.randint(-4, 4)
            gs.shake_timer -= 1
            if gs.shake_timer <= 0:
                gs.shake     = False
                gs.waste_pos = list(gs.shake_origin)

    if gs.state == "question" and gs.q_feedback_timer > 0:
        gs.q_feedback_timer -= 1
        if gs.q_feedback_timer == 0:
            if gs.q_feedback == "correct":
                gs.level += 1
                if gs.level > 5:
                    gs.state = "game_over"
                    celebration_snd.play()
                else:
                    gs.state = "next_level"
            else:
                gs.items_done = 0
                gs.state      = "playing"
            gs.q_feedback = ""

    # ─────────────────────────────────────────
    #  DRAW
    # ─────────────────────────────────────────
    if gs.state == "start":
        screen.blit(start_img, (0, 0))

    elif gs.state == "playing":
        screen.blit(bg_img, (0, 0))
        draw_bin_labels()
        draw_waste()
        draw_hud()
        draw_pause_button()
        if paused:
            draw_pause_overlay()

    elif gs.state == "question":
        screen.blit(bg_img, (0, 0))
        draw_question_overlay()

    elif gs.state == "next_level":
        screen.blit(nextlevel_img, (0, 0))
        info = font_med.render("Click anywhere to continue", True, (255, 255, 255))
        screen.blit(info, info.get_rect(centerx=WIDTH//2, y=HEIGHT - 80))

    elif gs.state == "game_over":
        screen.blit(gameover_img, (0, 0))
        sc_surf = font_big.render(f"Score: {gs.score}", True, (255, 220, 50))
        screen.blit(sc_surf, sc_surf.get_rect(centerx=WIDTH//2, y=80))
        hint = font_small.render("Click RIGHT to RETRY  |  Click LEFT to QUIT",
                                  True, (255, 255, 255))
        screen.blit(hint, hint.get_rect(centerx=WIDTH//2, y=HEIGHT - 50))

    pygame.display.flip()

pygame.quit()
sys.exit()