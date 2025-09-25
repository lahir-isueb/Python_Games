import pygame
import random
import math

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Bullet Hell")

# --- GAME OVER ---

def GAME_OVER(final_score):
    screen.fill(BLACK)
    over_text = big_font.render("GAME OVER", True, RED)
    score_text = font.render(f"Final Score: {final_score}", True, WHITE)
    instr_text = font.render("Press space to exit", True, GRAY)

    screen.blit(over_text, over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
    screen.blit(score_text, score_text.get_rect(center=(WIDTH//2, HEIGHT//2)))
    screen.blit(instr_text, instr_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                print(f"Final score: {final_score}")
                waiting = False
        clock.tick(15)

# --- Colors ---
WHITE = (255, 255, 255)
GRAY = (125, 125, 125)
BLACK = (0, 0, 0)
MAROON = (100, 0, 0)
MAROONISH_RED = (200, 0, 0)
RED = (255, 0, 0)
ORANGE = (255, 120, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (162, 0, 255)
MAGENTA = (255, 0, 255)
HOT_PINK = (255, 0, 106)

# --- Spawner Size ---
SPAWNER_SIZE = 50

# --- Player ---
player_size = 50
player_x = WIDTH // 2 - 100
player_y = HEIGHT // 2
player_speed = 8
player_lives = 3

# --- Enemy ---
enemy_size = 50
enemies = []

# --- Spawner ---
spawner_pos = (WIDTH // 2 - SPAWNER_SIZE // 2, HEIGHT // 2 - SPAWNER_SIZE // 2)
initial_spawn_delay = 2000 # ORIGINAL VALUE 2000
last_spawn_time = pygame.time.get_ticks()
enemy_speed = 5
min_spawn_delay = 500  # max spawn rate
spawn_rate = 11.67

player_x = spawner_pos[0] - player_size - 500  # 20 pixels gap to the left
player_y = spawner_pos[1] + SPAWNER_SIZE // 2 - player_size // 2  # vertically centered

# --- Bounce limits / health ---
basic_hp = 5 # gray enemy
homing_hp = 2 # green enemy
fatal_hp = 5 # red enemy
flow_hp = 3 # blue enemy
sticky_hp = 8 # yellow enemy
gloomy_hp = 6 # purple enemy
trail_hp = 3 # orange enemy
impostor_hp = 4 # white enemy
splitter_hp = 3 # magenta enemy
bomb_hp = 5 # hot pink enemy

# --- Score ---
score = 0
font = pygame.font.SysFont(None, 40)
big_font = pygame.font.SysFont(None, 48)
player_font = pygame.font.SysFont(None, 48)
regen = 70
next_regen_score = regen

# --- Clock ---
clock = pygame.time.Clock()
FPS = 60

# --- Enemy unlocking ---
available_enemy_types = [1]  # start with basic
locked_enemy_types = [2, 3, 4, 5, 6, 7, 8, 9, 10]
unlock_scores = [20, 60, 120, 200, 300, 420, 560, 720, 900] # Add 180 next time

# --- Trail for orange enemy ---
trail_squares = []  # each: {"x","y","spawn","health"}
trail_lifetime_ms = 3000 # this is the length of the trail
trail_interval_ms = 450 # this is the distance between trail particles
trail_size = 10

# --- Projectile ---
projectiles = []  # each: {"x","y","dx","dy"}
projectile_speed = 2.5
projectile_size = 10

# --- Player damage flash ---
damage_flash_time = 0
invincible_until = 0
invincibility_duration = 1000

# +++ Regen indicator +++

heal_indicators = []  # each: {"x","y","spawn_time"}
heal_duration = 500   # milliseconds the green flash lasts

def rotate_toward(current_angle, target_angle, turn_speed):
    difference = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi
    if abs(difference) < turn_speed:
        return target_angle
    return current_angle + turn_speed * (1 if difference > 0 else -1)

def check_collision(px, py, pw, ph, ex, ey, ew, eh):
    return px < ex + ew and px + pw > ex and py < ey + eh and py + ph > ey

def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def TITLE_SCREEN():
    screen.fill(BLACK)
    title_text = big_font.render("BULLET HELL", True, RED)
    instr_text = font.render("Press SPACE to start", True, WHITE)

    screen.blit(title_text, title_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
    screen.blit(instr_text, instr_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False
        clock.tick(15)

TITLE_SCREEN()

running = True
while running:
    clock.tick(FPS)
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    keys = pygame.key.get_pressed()
    dx = 0
    dy = 0
    if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

    # Normalize diagonal movement
    if dx != 0 or dy != 0:
        length = math.hypot(dx, dy)
        dx = dx / length * player_speed
        dy = dy / length * player_speed
        player_moving = True
    else:
        player_moving = False

    player_x += dx
    player_y += dy
    player_x = max(0, min(WIDTH - player_size, player_x))
    player_y = max(0, min(HEIGHT - player_size, player_y))

    # --- Dynamic Enemy Unlock ---
    while unlock_scores and score >= unlock_scores[0]:
        if locked_enemy_types:
            new_type = random.choice(locked_enemy_types)
            available_enemy_types.append(new_type)
            locked_enemy_types.remove(new_type)
        unlock_scores.pop(0)

    # --- Enemy Spawning ---
    adjusted_score = score / 2  # scale back to old point rate
    spawn_delay = max(
        min_spawn_delay,
        initial_spawn_delay - int(adjusted_score * spawn_rate)
    )
    if current_time - last_spawn_time >= spawn_delay:
        enemy_type = random.choice(available_enemy_types)
        angle = random.uniform(0, 2 * math.pi)
        if enemy_type == 1:     # Gray
            dx = math.cos(angle) * enemy_speed
            dy = math.sin(angle) * enemy_speed
            health = basic_hp
        elif enemy_type == 2:   # Green
            dx = math.cos(angle) * (enemy_speed * 0.7) #0.7
            dy = math.sin(angle) * (enemy_speed * 0.7)
            health = homing_hp
        elif enemy_type == 3:   # Red
            dx = math.cos(angle) * enemy_speed
            dy = math.sin(angle) * enemy_speed
            health = fatal_hp
        elif enemy_type == 4:   # Blue
            dx = math.cos(angle) * (enemy_speed * 2/3)
            dy = math.sin(angle) * (enemy_speed * 2/3)
            health = flow_hp
        elif enemy_type == 5:   # Yellow
            dx = math.cos(angle) * enemy_speed
            dy = math.sin(angle) * enemy_speed
            health = sticky_hp
        elif enemy_type == 6:   # Purple
            dx = math.cos(angle) * enemy_speed * 1.85
            dy = math.sin(angle) * enemy_speed * 1.85
            health = gloomy_hp
        elif enemy_type == 7:   # Orange
            dx = math.cos(angle) * enemy_speed
            dy = math.sin(angle) * enemy_speed
            health = trail_hp
        elif enemy_type == 8:   # Sussy White Impostor
            dx = math.cos(angle) * enemy_speed * 1.5
            dy = math.sin(angle) * enemy_speed * 1.5
            health = impostor_hp
        elif enemy_type == 9:   # Magenta
            dx = math.cos(angle) * enemy_speed
            dy = math.sin(angle) * enemy_speed
            health = splitter_hp
        elif enemy_type == 10:  # Hot Pink
            dx = math.cos(angle) * enemy_speed
            dy = math.sin(angle) * enemy_speed
            health = bomb_hp
        enemies.append({
            "x": spawner_pos[0],
            "y": spawner_pos[1],
            "dx": dx,
            "dy": dy,
            "type": enemy_type,
            "angle": angle,
            "bounces": 0,
            "health": health,
            "stopped": False,
            "stop_start_time": None,
            "last_trail_time": current_time
        })
        last_spawn_time = current_time
        
        

    # --- Enemy Movement ---
    for enemy in enemies[:]:
        enemy_died = False

        if enemy["type"] == 1:
            enemy["x"] += enemy["dx"]; enemy["y"] += enemy["dy"]
            bounced = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size: enemy["dx"] *= -1; bounced = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size: enemy["dy"] *= -1; bounced = True
            if bounced: enemy["bounces"] += 1; enemy["health"] -= 1
            if enemy["bounces"] >= basic_hp: enemy_died = True

        elif enemy["type"] == 2:
            dx = player_x - enemy["x"]; dy = player_y - enemy["y"]
            target_angle = math.atan2(dy, dx)
            enemy["angle"] = rotate_toward(enemy["angle"], target_angle, 0.02)
            enemy["dx"] = math.cos(enemy["angle"]) * (enemy_speed * 0.7)
            enemy["dy"] = math.sin(enemy["angle"]) * (enemy_speed * 0.7)
            enemy["x"] += enemy["dx"]; enemy["y"] += enemy["dy"]
            bounced = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size: enemy["angle"] = math.pi - enemy["angle"]; bounced = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size: enemy["angle"] = -enemy["angle"]; bounced = True
            if bounced: enemy["bounces"] += 1; enemy["health"] -= 1
            if enemy["bounces"] >= homing_hp: enemy_died = True

        elif enemy["type"] == 3:
            enemy["x"] += enemy["dx"]; enemy["y"] += enemy["dy"]
            bounced = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size: enemy["dx"] *= -1; bounced = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size: enemy["dy"] *= -1; bounced = True
            if bounced: enemy["bounces"] += 1; enemy["health"] -= 1
            if enemy["bounces"] >= fatal_hp: enemy_died = True

        elif enemy["type"] == 4:  # Blue
            dist = distance(enemy["x"], enemy["y"], player_x, player_y)
            speed_multiplier = 2.5 if dist < 250 else 2/3
            # Move enemy
            enemy["x"] += enemy["dx"] * speed_multiplier
            enemy["y"] += enemy["dy"] * speed_multiplier
            bounced = False
            # X-axis bounce
            if enemy["x"] <= 0:
                enemy["x"] = 0
                enemy["dx"] *= -1
                bounced = True
            elif enemy["x"] >= WIDTH - enemy_size:
                enemy["x"] = WIDTH - enemy_size
                enemy["dx"] *= -1
                bounced = True
            # Y-axis bounce
            if enemy["y"] <= 0:
                enemy["y"] = 0
                enemy["dy"] *= -1
                bounced = True
            elif enemy["y"] >= HEIGHT - enemy_size:
                enemy["y"] = HEIGHT - enemy_size
                enemy["dy"] *= -1
                bounced = True
            # Update bounce count and health once per frame
            if bounced:
                enemy["bounces"] += 1
                enemy["health"] -= 1
            # Remove enemy if health depleted
            if enemy["bounces"] >= flow_hp or enemy["health"] <= 0:
                enemy_died = True


        elif enemy["type"] == 5:  # Yellow
            if enemy["stopped"]:
                # after 2 seconds resume moving
                if current_time - enemy["stop_start_time"] >= 2000:
                    enemy["stopped"] = False
            else:
                enemy["x"] += enemy["dx"]
                enemy["y"] += enemy["dy"]

                bounced = False
                if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size:
                    enemy["dx"] *= -1
                    bounced = True
                if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size:
                    enemy["dy"] *= -1
                    bounced = True

                if bounced:
                    enemy["health"] -= 1
                    if enemy["health"] <= 0:
                        enemy_died = True
                    else:
                        enemy["stopped"] = True
                        enemy["stop_start_time"] = current_time

            # final safety: if health already at 0, mark dead
            if enemy["health"] <= 0:
                enemy_died = True

        elif enemy["type"] == 6:  # Purple
            dist = distance(enemy["x"], enemy["y"], player_x, player_y)
            if dist > 250:
                enemy["x"] += enemy["dx"]
                enemy["y"] += enemy["dy"]
                bounced = False
                if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size: 
                    enemy["dx"] *= -1; bounced = True
                if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size: 
                    enemy["dy"] *= -1; bounced = True
                if bounced:
                    enemy["bounces"] += 1; enemy["health"] -= 1
                if enemy["health"] <= 0: enemy_died = True


        elif enemy["type"] == 7:  # Orange
            enemy["x"] += enemy["dx"]; enemy["y"] += enemy["dy"]
            bounced = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size: enemy["dx"] *= -1; bounced = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size: enemy["dy"] *= -1; bounced = True
            if bounced: enemy["bounces"] += 1; enemy["health"] -= 1
            if current_time - enemy["last_trail_time"] >= trail_interval_ms:
                trail_squares.append({
                    "x": int(enemy["x"] + enemy_size / 2 - trail_size/2),
                    "y": int(enemy["y"] + enemy_size / 2 - trail_size/2),
                    "spawn": current_time,
                    "health": 3
                })
                enemy["last_trail_time"] = current_time
            if enemy["health"] <= 0: enemy_died = True

        elif enemy["type"] == 8:  # White (Impostor)
            if player_moving:  # move only if player is moving
                enemy["x"] += enemy["dx"]
                enemy["y"] += enemy["dy"]
            bounced = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size:
                enemy["dx"] *= -1
                bounced = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size:
                enemy["dy"] *= -1
                bounced = True
            if bounced:
                enemy["bounces"] += 1
                enemy["health"] -= 1
            if enemy["bounces"] >= impostor_hp or enemy["health"] <= 0:
                enemy_died = True

        elif enemy["type"] == 9:  # Magenta
            # Move normally
            enemy["x"] += enemy["dx"]
            enemy["y"] += enemy["dy"]

            # --- Handle spawn protection ---
            if enemy.get("spawn_protected"):
                # remove protection after 0.5 seconds
                if pygame.time.get_ticks() - enemy["spawn_time"] > 500:
                    enemy.pop("spawn_protected")

            # Bounce or split
            hit_edge = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size:
                hit_edge = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size:
                hit_edge = True

            if hit_edge:
                # If still protected, just bounce off edges normally (no split/damage yet)
                if enemy.get("spawn_protected"):
                    # bounce without damage
                    if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size:
                        enemy["dx"] *= -1
                    if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size:
                        enemy["dy"] *= -1
                else:
                    # Kill and split into two clones if health > 1
                    if enemy["health"] > 1:
                        for i in range(2):
                            angle = random.uniform(0, 2 * math.pi)
                            dx = math.cos(angle) * enemy_speed
                            dy = math.sin(angle) * enemy_speed
                            enemies.append({
                                "x": max(1, min(WIDTH - enemy_size - 1, enemy["x"])),
                                "y": max(1, min(HEIGHT - enemy_size - 1, enemy["y"])),
                                "dx": dx,
                                "dy": dy,
                                "type": 9,
                                "angle": angle,
                                "bounces": 0,
                                "health": enemy["health"] - 1,
                                "spawn_protected": True,
                                "spawn_time": pygame.time.get_ticks()
                            })
                    else:
                        # This was a 1 HP magenta enemy — add to score on death
                        score += 1

                    enemies.remove(enemy)
                continue
            # If waiting flag: wait until enemy is off the edge before taking damage
            if enemy.get("waiting"):
                # Check if off edge now
                if 0 < enemy["x"] < WIDTH - enemy_size and 0 < enemy["y"] < HEIGHT - enemy_size:
                    enemy.pop("waiting")  # remove waiting flag

                    
        elif enemy["type"] == 10:  # Hot Pink Bomb
            # Move like basic
            enemy["x"] += enemy["dx"]
            enemy["y"] += enemy["dy"]
            bounced = False
            if enemy["x"] <= 0 or enemy["x"] >= WIDTH - enemy_size:
                enemy["dx"] *= -1
                bounced = True
            if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - enemy_size:
                enemy["dy"] *= -1
                bounced = True
            if bounced:
                enemy["health"] -= 1

            # Proximity trigger – bomb kills itself and explodes
            if distance(enemy["x"], enemy["y"], player_x, player_y) < 200:# EXPLODE DISTANCE FROM PALYER
                # spawn 8 projectiles immediately
                for i in range(8):
                    ang = i * (2 * math.pi / 8)
                    dxp = math.cos(ang) * projectile_speed
                    dyp = math.sin(ang) * projectile_speed
                    projectiles.append({
                        "x": enemy["x"] + enemy_size // 2,
                        "y": enemy["y"] + enemy_size // 2,
                        "dx": dxp,
                        "dy": dyp
                    })
                # instantly kill bomb (not player)
                enemy["health"] = 0  # mark as dead

            # If HP ≤ 0 (killed normally or via proximity), explode once and remove
            if enemy["health"] <= 0:
                # (optional) award score here if you want
                enemy_died = True




        if check_collision(player_x, player_y, player_size, player_size,
                           enemy["x"], enemy["y"], enemy_size, enemy_size):
            if enemy["type"] == 3:
                GAME_OVER(score)
                running = False
                break
            else:
                if current_time >= invincible_until:
                    player_lives -= 1
                    damage_flash_time = current_time
                    invincible_until = current_time + invincibility_duration
                    enemies.remove(enemy)
                    if player_lives <= 0:
                        GAME_OVER(score)
                        running = False
                continue

        if enemy_died:
            if enemy in enemies:
                enemies.remove(enemy)
            score+=2
            while score >= next_regen_score and player_lives < 3:
                player_lives += 1
                next_regen_score += regen
                # Add green heal indicator at player position
                heal_indicators.append({
                    "x": player_x,
                    "y": player_y,
                    "spawn_time": pygame.time.get_ticks()
                })


    # --- Trail squares update ---
    new_trails = []
    for sq in trail_squares:
        if current_time - sq["spawn"] > trail_lifetime_ms:
            continue
        if check_collision(player_x, player_y, player_size, player_size,
                           sq["x"], sq["y"], trail_size, trail_size):
            if current_time >= invincible_until:
                player_lives -= 1
                damage_flash_time = current_time
                invincible_until = current_time + invincibility_duration
                if player_lives <= 0:
                    GAME_OVER(score)
                    running = False
                    break
            sq["health"] -= 1
            if sq["health"] > 0:
                new_trails.append(sq)
            continue
        new_trails.append(sq)
    trail_squares = new_trails

    # --- Projectiles movement ---
    new_projectiles = []
    for p in projectiles:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        # Check collision with player
        if check_collision(player_x, player_y, player_size, player_size,
                           p["x"], p["y"], projectile_size, projectile_size):
            if current_time >= invincible_until:  # respect invincibility window
                player_lives -= 1
                damage_flash_time = current_time
                invincible_until = current_time + invincibility_duration
                if player_lives <= 0:
                    GAME_OVER(score)
                    running = False
                    break
            # projectiles disappear after hitting player
            continue

        # Keep projectile on screen
        if 0 < p["x"] < WIDTH and 0 < p["y"] < HEIGHT:
            new_projectiles.append(p)

    projectiles = new_projectiles

    # --- Drawing ---
    screen.fill(BLACK)

    # draw spawner
    pygame.draw.rect(screen, BLACK, (*spawner_pos, SPAWNER_SIZE, SPAWNER_SIZE))
    pygame.draw.rect(screen, MAROON, (*spawner_pos, SPAWNER_SIZE, SPAWNER_SIZE), 3)


    # --- FULL SPAWNER INDICATOR --
    # --- Spawner Animation ---
    center = (spawner_pos[0] + SPAWNER_SIZE // 2,
              spawner_pos[1] + SPAWNER_SIZE // 2)

    # 0.0 = just spawned, 1.0 = about to spawn
    indicator_ratio = min(1.0, (current_time - last_spawn_time) / spawn_delay)

    def lerp_color(c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    pulse_color = lerp_color(MAROON, RED, indicator_ratio)

    # --- shrinking/fading glow ---
    glow_size = SPAWNER_SIZE * 4  # surface large enough for glow
    glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)

    # fade alpha in as spawn nears
    alpha = int(40 + 180 * indicator_ratio)

    # radius shrinks from big to exactly the box radius
    start_glow_radius = SPAWNER_SIZE * 2          # starting radius
    end_glow_radius = SPAWNER_SIZE // 2           # final radius exactly at box size
    glow_radius = int(start_glow_radius * (1 - indicator_ratio) +
                      end_glow_radius * indicator_ratio)

    pygame.draw.circle(glow_surface, (*pulse_color, alpha),
                       (glow_size // 2, glow_size // 2), glow_radius)
    screen.blit(glow_surface, (center[0] - glow_size // 2, center[1] - glow_size // 2))

    # --- shrinking indicator circle outline ---
    radius = glow_radius
    pygame.draw.circle(screen, pulse_color, center, int(radius), 4)
    
    # --- rotating arcs (optional) ---
    angle_progress = current_time / 500.0  # rotation speed
    arc_radius = radius + 5
    for i in range(3):  # three arc segments
        start_angle = angle_progress + i * (2 * math.pi / 3)
        end_angle = start_angle + math.pi / 4
        pygame.draw.arc(screen, pulse_color,
                        (center[0] - arc_radius, center[1] - arc_radius,
                         arc_radius * 2, arc_radius * 2),
                        start_angle, end_angle, 5)

    # --- spawner core ---
    pygame.draw.rect(screen, BLACK, (*spawner_pos, SPAWNER_SIZE, SPAWNER_SIZE))
    pygame.draw.rect(screen, MAROON, (*spawner_pos, SPAWNER_SIZE, SPAWNER_SIZE), 3)

    # draw trail squares
    for sq in trail_squares:
        pygame.draw.rect(screen, ORANGE, (sq["x"], sq["y"], trail_size, trail_size))

    # draw projectiles
    for p in projectiles:
        pygame.draw.rect(screen, HOT_PINK, (p["x"], p["y"], projectile_size, projectile_size))

    # draw enemies
    for enemy in enemies:
        if enemy["type"] == 1: color = GRAY
        elif enemy["type"] == 2: color = GREEN
        elif enemy["type"] == 3: color = RED
        elif enemy["type"] == 4: color = BLUE
        elif enemy["type"] == 5: color = YELLOW
        elif enemy["type"] == 6: color = PURPLE
        elif enemy["type"] == 7: color = ORANGE
        elif enemy["type"] == 8: color = WHITE
        elif enemy["type"] == 9: color = MAGENTA
        elif enemy["type"] == 10: color = HOT_PINK
        pygame.draw.rect(screen, color, (enemy["x"], enemy["y"], enemy_size, enemy_size))

        if enemy["type"] == 8:
            text_surface = big_font.render(str(player_lives), True, BLACK)
        else:
            text_surface = big_font.render(str(max(enemy["health"], 0)), True, BLACK)
            
        text_rect = text_surface.get_rect(center=(enemy["x"] + enemy_size/2, enemy["y"] + enemy_size/2))
        screen.blit(text_surface, text_rect)

    # draw player (flash red if hit)
    if current_time - damage_flash_time < 100:
        pygame.draw.rect(screen, RED, (player_x, player_y, player_size, player_size))
    else:
        pygame.draw.rect(screen, WHITE, (player_x, player_y, player_size, player_size))


    new_heal_indicators = []
    for ind in heal_indicators:
        if current_time - ind["spawn_time"] < heal_duration:
            alpha = 255 * (1 - (current_time - ind["spawn_time"]) / heal_duration)  # optional fade
            s = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
            s.fill((0, 255, 0, int(alpha)))  # green with fading alpha
            screen.blit(s, (ind["x"], ind["y"]))
            new_heal_indicators.append(ind)
    heal_indicators = new_heal_indicators


    # draw player lives in center
    player_life_text = player_font.render(str(player_lives), True, BLACK)
    player_life_rect = player_life_text.get_rect(center=(player_x + player_size/2, player_y + player_size/2))
    screen.blit(player_life_text, player_life_rect)

    # draw HUD
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (20, 20))
        
    pygame.display.flip()

pygame.quit()
