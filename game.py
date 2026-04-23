import pygame, random, math, os
from enum import Enum
from collections import namedtuple

# --- CONFIG ---
WIDTH, HEIGHT = 800, 600
BLOCK = 20
BASE_SPEED = 12
SCORE_FILE = "highscores.txt"

C_BG = (10, 10, 20)
C_P1 = (0, 255, 150)   
C_AI = (255, 45, 85)   
C_FOOD = (255, 230, 0) 
C_GOLD = (255, 215, 0)
C_WHITE = (255, 255, 255)
C_CYAN = (0, 200, 255)
C_WALL = (60, 60, 90)

Point = namedtuple("Point", "x y")

class Mode(Enum):
    MENU = 0; CLASSIC = 1; AI_VERSUS = 2; SURVIVAL = 3; BOSS = 4; GAMEOVER = 5

class Direction(Enum):
    RIGHT=1; LEFT=2; UP=3; DOWN=4

class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init()
            self.chomp = self._load("chomp.wav")
            self.crash = self._load("crash.wav")
            self.ghost = self._load("ghost.wav")
        except:
            self.chomp = self.crash = self.ghost = None
    def _load(self, f):
        return pygame.mixer.Sound(f) if os.path.exists(f) else None
    def play(self, s):
        if s: s.play()

class SnakeX:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SNAKE X // NEON PRO")
        self.clock = pygame.time.Clock()
        self.sounds = SoundManager()
        self.selected = 0
        self.high_score = self.load_highscore()
        self.font_lg = pygame.font.SysFont("Courier", 90, bold=True)
        self.font_md = pygame.font.SysFont("Courier", 35, bold=True)
        self.font_sm = pygame.font.SysFont("Courier", 20, bold=True)
        self.mode = Mode.MENU
        self.reset()

    def load_highscore(self):
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r") as f: return int(f.read())
            except: return 0
        return 0

    def reset(self):
        self.p1_head = Point(BLOCK * 5, HEIGHT // 2)
        self.p1_body = [self.p1_head, Point(self.p1_head.x-BLOCK, self.p1_head.y)]
        self.p1_dir = Direction.RIGHT
        self.p1_score = 0
        self.new_record = False
        
        # Ghost State
        self.ghost_mode = False
        self.ghost_timer = 0
        
        self.ai_head = Point(WIDTH - (BLOCK * 6), HEIGHT // 2)
        self.ai_body = [self.ai_head, Point(self.ai_head.x+BLOCK, self.ai_head.y)]
        self.ai_dir = Direction.LEFT
        
        self.obstacles = []
        self.speed = BASE_SPEED
        if self.mode == Mode.BOSS:
            for _ in range(15): self.obstacles.append(self.place_item())
        self.food = self.place_item()

    def place_item(self):
        while True:
            p = Point(random.randrange(BLOCK, WIDTH-BLOCK, BLOCK), 
                      random.randrange(BLOCK, HEIGHT-BLOCK, BLOCK))
            if p not in self.p1_body and p not in self.obstacles: return p

    def draw_vignette(self):
        for i in range(0, HEIGHT, 6):
            s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            s.fill((255, 255, 255, 20)) 
            self.display.blit(s, (0, i))
        sz, th = 40, 3
        pygame.draw.lines(self.display, C_CYAN, False, [(sz, 20), (20, 20), (20, sz)], th)
        pygame.draw.lines(self.display, C_CYAN, False, [(WIDTH-sz, 20), (WIDTH-20, 20), (WIDTH-20, sz)], th)
        pygame.draw.lines(self.display, C_CYAN, False, [(sz, HEIGHT-20), (20, HEIGHT-20), (20, HEIGHT-sz)], th)
        pygame.draw.lines(self.display, C_CYAN, False, [(WIDTH-sz, HEIGHT-20), (WIDTH-20, HEIGHT-20), (WIDTH-20, HEIGHT-sz)], th)

    def draw_pixel_snake(self, body, color, direction, alpha=255):
        for i, b in enumerate(body):
            # Surface for alpha support
            s = pygame.Surface((BLOCK, BLOCK), pygame.SRCALPHA)
            r = (1, 1, BLOCK - 2, BLOCK - 2)
            
            if i == 0: # HEAD
                pygame.draw.rect(s, (*color, alpha), r, border_radius=5)
                ec = (255, 255, 255, alpha)
                if direction in [Direction.RIGHT, Direction.LEFT]:
                    pygame.draw.rect(s, ec, (12, 4, 4, 4))
                    pygame.draw.rect(s, ec, (12, 12, 4, 4))
                else:
                    pygame.draw.rect(s, ec, (4, 4, 4, 4))
                    pygame.draw.rect(s, ec, (12, 4, 4, 4))
            else: # BODY
                curr_c = color if i % 2 == 0 else (max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40))
                pygame.draw.rect(s, (*curr_c, alpha), r, border_radius=3)
            
            self.display.blit(s, (b.x, b.y))

    def step(self):
        t = pygame.time.get_ticks()
        
        # Ghost expiration
        if self.ghost_mode and t > self.ghost_timer:
            self.ghost_mode = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP and self.p1_dir != Direction.DOWN: self.p1_dir = Direction.UP
                elif e.key == pygame.K_DOWN and self.p1_dir != Direction.UP: self.p1_dir = Direction.DOWN
                elif e.key == pygame.K_LEFT and self.p1_dir != Direction.RIGHT: self.p1_dir = Direction.LEFT
                elif e.key == pygame.K_RIGHT and self.p1_dir != Direction.LEFT: self.p1_dir = Direction.RIGHT
                # SECRET KEY
                if e.key == pygame.K_g and not self.ghost_mode:
                    self.ghost_mode = True
                    self.ghost_timer = t + 5000 # 5 Seconds
                    self.sounds.play(self.sounds.ghost)

        if self.mode == Mode.AI_VERSUS:
            if self.ai_head.x < self.food.x and self.ai_dir != Direction.LEFT: self.ai_dir = Direction.RIGHT
            elif self.ai_head.x > self.food.x and self.ai_dir != Direction.RIGHT: self.ai_dir = Direction.LEFT
            elif self.ai_head.y < self.food.y and self.ai_dir != Direction.UP: self.ai_dir = Direction.DOWN
            elif self.ai_head.y > self.food.y and self.ai_dir != Direction.DOWN: self.ai_dir = Direction.UP

        def move_h(h, d):
            x, y = h.x, h.y
            if d == Direction.RIGHT: x += BLOCK
            elif d == Direction.LEFT: x -= BLOCK
            elif d == Direction.UP: y -= BLOCK
            elif d == Direction.DOWN: y += BLOCK
            return Point(x, y)

        self.p1_head = move_h(self.p1_head, self.p1_dir)
        if self.mode == Mode.AI_VERSUS: self.ai_head = move_h(self.ai_head, self.ai_dir)

        # Collision (Bypassed if Ghost)
        def is_dead(h, body, other):
            if self.ghost_mode and h == self.p1_head: return False
            return h.x < 0 or h.x >= WIDTH or h.y < 0 or h.y >= HEIGHT or h in body[1:] or h in other or h in self.obstacles

        if is_dead(self.p1_head, self.p1_body, self.ai_body if self.mode == Mode.AI_VERSUS else []):
            self.sounds.play(self.sounds.crash)
            if self.p1_score > self.high_score:
                self.high_score = self.p1_score
                self.new_record = True
                with open(SCORE_FILE, "w") as f: f.write(str(self.high_score))
            self.mode = Mode.GAMEOVER
            return True

        self.p1_body.insert(0, self.p1_head)
        if self.p1_head == self.food:
            self.p1_score += 1
            self.sounds.play(self.sounds.chomp)
            self.food = self.place_item()
            if self.mode == Mode.SURVIVAL: self.speed += 0.5
        else: self.p1_body.pop()

        if self.mode == Mode.AI_VERSUS:
            self.ai_body.insert(0, self.ai_head)
            if self.ai_head == self.food: self.food = self.place_item()
            else: self.ai_body.pop()

        # Render
        self.display.fill(C_BG)
        for x in range(0, WIDTH, BLOCK): pygame.draw.line(self.display, (15, 15, 30), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, BLOCK): pygame.draw.line(self.display, (15, 15, 30), (0, y), (WIDTH, y))
        
        for o in self.obstacles: pygame.draw.rect(self.display, C_WALL, (o.x+2, o.y+2, BLOCK-4, BLOCK-4), border_radius=4)
        pygame.draw.circle(self.display, (120, 100, 0), (self.food.x+10, self.food.y+10), 12)
        pygame.draw.rect(self.display, C_FOOD, (self.food.x+4, self.food.y+4, BLOCK-8, BLOCK-8), border_radius=2)
        
        # Draw Snakes
        p1_c = C_CYAN if self.ghost_mode else C_P1
        p1_a = 160 if self.ghost_mode else 255
        self.draw_pixel_snake(self.p1_body, p1_c, self.p1_dir, p1_a)
        if self.mode == Mode.AI_VERSUS: self.draw_pixel_snake(self.ai_body, C_AI, self.ai_dir)

        # UI
        if self.ghost_mode:
            rem = max(0, (self.ghost_timer - t) // 1000)
            g_txt = self.font_sm.render(f"GHOST MODE: {rem}s", True, C_CYAN)
            self.display.blit(g_txt, (WIDTH//2 - g_txt.get_width()//2, 35))
        
        s_txt = self.font_sm.render(f"SCORE: {self.p1_score}", True, C_WHITE)
        self.display.blit(s_txt, (35, 35))

        self.draw_vignette()
        pygame.display.update()
        self.clock.tick(self.speed)
        return True

    def run_menu(self):
        t = pygame.time.get_ticks()
        self.display.fill(C_BG)
        title_y = 100 + math.sin(t * 0.005) * 12
        txt = self.font_lg.render("SNAKE X", True, C_P1)
        self.display.blit(txt, (WIDTH//2 - txt.get_width()//2, title_y))
        modes = ["CLASSIC", "VERSUS AI", "SURVIVAL", "BOSS CHALLENGE"]
        for i, m in enumerate(modes):
            active = (i == self.selected)
            color = C_WHITE if active else (100, 100, 120)
            prefix = ">> " if active else "   "
            m_txt = self.font_md.render(f"{prefix}{m}", True, color)
            self.display.blit(m_txt, (WIDTH//2 - 140 + (10 if active else 0), 300 + i*50))
        self.draw_vignette()
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP: self.selected = (self.selected-1)%4
                elif e.key == pygame.K_DOWN: self.selected = (self.selected+1)%4
                elif e.key == pygame.K_RETURN:
                    self.mode = Mode(self.selected + 1)
                    self.reset()
        return True

    def run_gameover(self):
        self.display.fill(C_BG)
        msg = "NEW RECORD!" if self.new_record else "CRASHED!"
        t1 = self.font_lg.render(msg, True, C_GOLD if self.new_record else C_AI)
        self.display.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
        self.draw_vignette()
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN: self.mode = Mode.MENU
            if e.type == pygame.QUIT: return False
        return True

if __name__ == "__main__":
    game = SnakeX()
    run = True
    while run:
        if game.mode == Mode.MENU: run = game.run_menu()
        elif game.mode == Mode.GAMEOVER: run = game.run_gameover()
        else: run = game.step()
    pygame.quit()