import pygame
import math
import random

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Endless Space Shooter")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Game variables
clock = pygame.time.Clock()
score = 0
font = pygame.font.SysFont(None, 36)

# Power-up constants
POWERUP_DURATION = 15
POWERUP_KILL_WINDOW = 7
POWERUP_KILL_COUNT = 5

# Helper functions
def draw_hollow_triangle(surface, color, position, angle, size):
    x, y = position
    points = [
        (x + size * math.cos(angle), y + size * math.sin(angle)),
        (x + size * math.cos(angle + 2.5), y + size * math.sin(angle + 2.5)),
        (x + size * math.cos(angle - 2.5), y + size * math.sin(angle - 2.5)),
    ]
    pygame.draw.polygon(surface, color, points, width=1)

def draw_solid_circle(surface, color, position, radius):
    pygame.draw.circle(surface, color, position, radius)

def draw_powerup_shape(surface, position):
    x, y = position
    size = 20
    pygame.draw.rect(surface, WHITE, (x - size // 2, y - size // 2, size, size), 1)
    pygame.draw.circle(surface, WHITE, (int(x), int(y)), size // 3, 1)

# Classes
class Player:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        self.base_speed = 5
        self.speed = self.base_speed
        self.size = 20
        self.cooldown = 0.2
        self.last_shot = 0
        self.powered_up = False
        self.powerup_end_time = 0

    def update(self, dt, current_time):
        if self.powered_up and current_time > self.powerup_end_time:
            self.powered_up = False
            self.speed = self.base_speed

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.pos.y -= self.speed
        if keys[pygame.K_s]: self.pos.y += self.speed
        if keys[pygame.K_a]: self.pos.x -= self.speed
        if keys[pygame.K_d]: self.pos.x += self.speed

        self.pos.x = max(self.size, min(WIDTH - self.size, self.pos.x))
        self.pos.y = max(self.size, min(HEIGHT - self.size, self.pos.y))

    def draw(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        angle = math.atan2(mouse_y - self.pos.y, mouse_x - self.pos.x)
        draw_hollow_triangle(screen, WHITE, self.pos, angle, self.size)
        if self.powered_up:
            radius = self.size + 10 + int(5 * math.sin(pygame.time.get_ticks() * 0.005))
            pygame.draw.circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), radius, 1)

    def shoot(self, bullets, current_time):
        if current_time - self.last_shot > self.cooldown:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            direction = pygame.Vector2(mouse_x, mouse_y) - self.pos
            direction = direction.normalize()
            if self.powered_up:
                angle_offset = math.radians(15)
                for offset in [-angle_offset, 0, angle_offset]:
                    rotated = direction.rotate_rad(offset)
                    bullets.append(Bullet(self.pos.copy(), rotated))
            else:
                bullets.append(Bullet(self.pos.copy(), direction))
            self.last_shot = current_time

    def apply_powerup(self, current_time):
        self.powered_up = True
        self.powerup_end_time = current_time + POWERUP_DURATION
        self.speed = self.base_speed * 1.2

class Bullet:
    def __init__(self, pos, direction):
        self.pos = pos
        self.direction = direction
        self.speed = 10
        self.radius = 4

    def update(self):
        self.pos += self.direction * self.speed

    def draw(self):
        draw_solid_circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), self.radius)

    def off_screen(self):
        return not (0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT)

class Enemy:
    def __init__(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top': self.pos = pygame.Vector2(random.randint(0, WIDTH), 0)
        elif edge == 'bottom': self.pos = pygame.Vector2(random.randint(0, WIDTH), HEIGHT)
        elif edge == 'left': self.pos = pygame.Vector2(0, random.randint(0, HEIGHT))
        else: self.pos = pygame.Vector2(WIDTH, random.randint(0, HEIGHT))
        self.speed = 2
        self.size = 15

    def update(self, player_pos):
        direction = (player_pos - self.pos).normalize()
        self.pos += direction * self.speed

        self.pos.x = max(self.size, min(WIDTH - self.size, self.pos.x))
        self.pos.y = max(self.size, min(HEIGHT - self.size, self.pos.y))

    def draw(self, player_pos):
        angle = math.atan2(player_pos.y - self.pos.y, player_pos.x - self.pos.x)
        draw_hollow_triangle(screen, RED, self.pos, angle, self.size)

    def hit_by(self, bullet):
        return self.pos.distance_to(bullet.pos) < bullet.radius + self.size

class PowerUp:
    def __init__(self):
        self.pos = pygame.Vector2(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
        self.size = 20

    def draw(self):
        draw_powerup_shape(screen, self.pos)

    def collected_by(self, player):
        return self.pos.distance_to(player.pos) < player.size + self.size

# Game objects
player = Player()
bullets = []
enemies = []
powerup = None
kill_times = []
enemy_spawn_timer = 0
enemy_spawn_interval = 1.5

# Game loop
running = True
start_time = pygame.time.get_ticks()
while running:
    dt = clock.tick(60) / 1000
    current_time = pygame.time.get_ticks() / 1000
    elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
    elapsed_time_score = int(elapsed_time * 10)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            player.shoot(bullets, current_time)

    player.update(dt, current_time)

    for bullet in bullets[:]:
        bullet.update()
        if bullet.off_screen():
            bullets.remove(bullet)

    for enemy in enemies[:]:
        enemy.update(player.pos)
        for bullet in bullets:
            if enemy.hit_by(bullet):
                enemies.remove(enemy)
                if bullet in bullets:
                    bullets.remove(bullet)
                score += 100
                kill_times.append(current_time)
                kill_times = [t for t in kill_times if current_time - t < POWERUP_KILL_WINDOW]
                if len(kill_times) >= POWERUP_KILL_COUNT and not powerup and not player.powered_up:
                    powerup = PowerUp()
                break
        if not player.powered_up and player.pos.distance_to(enemy.pos) < enemy.size:
            running = False

    if powerup and powerup.collected_by(player):
        player.apply_powerup(current_time)
        powerup = None

    enemy_spawn_timer += dt
    if enemy_spawn_timer > enemy_spawn_interval:
        enemies.append(Enemy())
        enemy_spawn_timer = 0
        enemy_spawn_interval = max(0.3, 1.5 - elapsed_time * 0.01)

    screen.fill(BLACK)
    player.draw()
    for bullet in bullets: bullet.draw()
    for enemy in enemies: enemy.draw(player.pos)
    if powerup: powerup.draw()
    total_score = elapsed_time_score + score
    score_text = font.render(f"Score: {total_score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    pygame.display.flip()

pygame.quit()
