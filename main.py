import pygame
import random
import os
import cv2
import mediapipe as mp
import sys
import threading

FPS = 60
WIDTH = 960 # 640*1.5 = 960
HEIGHT = 720 # 480*1.5 = 720
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)

global game_start_time
global score
global longest_time
global check_time
global chance
global stop_the_camera
stop_the_camera = False
global done
done = False

# 初始化MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(model_complexity=0,
               min_detection_confidence=0.01,
               min_tracking_confidence=0.01)

# 設置相機視窗
camera_window_width = 640
camera_window_height = 480

# 處理相機視窗的函數
def camera_thread():
    global the_x
    global the_y
    global done
    global stop_the_camera
    tracker = cv2.TrackerCSRT_create()  # 創建追蹤器
    tracking = False  # 設定 False 表示尚未開始追蹤

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Cannot receive frame")
            break
        frame = cv2.resize(frame, (camera_window_width, camera_window_height))
        keyName = cv2.waitKey(1)

        if keyName == ord('q') or stop_the_camera:
            break
        if keyName == ord('a'):
            area = cv2.selectROI('oxxostudio', frame, showCrosshair=False, fromCenter=False)
            tracker.init(frame, area)  # 初始化追蹤器
            tracking = True  # 設定可以開始追蹤
            done = True # 完成設定，可以跳出 draw_init 的畫面
        if tracking:
            success, point = tracker.update(frame)  # 追蹤成功後，不斷回傳左上和右下的座標
            if success:
                p1 = [int(point[0]), int(point[1])]
                p2 = [int(point[0] + point[2]), int(point[1] + point[3])]
                the_x = int((point[0] + point[2] / 2)*1.5)
                the_y = int((point[1] + point[3] / 2)*1.5)
                draw_x , draw_y = int(point[0] + point[2] / 2), int(point[1] + point[3] / 2)
                cv2.rectangle(frame, p1, p2, (0, 0, 255), 3)  # 根據座標，繪製四邊形，框住要追蹤的物件
                cv2.circle(frame, (draw_x, draw_y), 5, GREEN, -1)

        cv2.imshow('oxxostudio', frame)

    cap.release()
    cv2.destroyAllWindows()

# 啟動相機處理線程
camera_thread_function = threading.Thread(target=camera_thread)
camera_thread_function.start()

# 設置角色位置
global the_x
global the_y
the_x = WIDTH // 2
the_y =HEIGHT // 2

# initialize the game and make the screen
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("石帥華做的遊戲")
clock = pygame.time.Clock()
longest_time = 0
check_time = 0


# load image
background_img_original = pygame.image.load(os.path.join("img", "background.png")).convert()
ending_background_img = pygame.image.load(os.path.join("img", "doggy.png")).convert()
background_img = pygame.transform.scale(background_img_original, (WIDTH, HEIGHT))
ending_backgroung_img = pygame.image.load(os.path.join("img", "daddy.png")).convert()
bullet_img_first = pygame.image.load(os.path.join("img", "bullet.png")).convert()
player_img = pygame.image.load(os.path.join("img", "dad1.png")).convert()
dad_life_img = pygame.image.load(os.path.join("img", "dad_life.png")).convert()
player_mini_img = pygame.transform.scale(dad_life_img, (50*1.5,67.5*1.5))
player_mini_img.set_colorkey(BLACK)
bullet_img = pygame.transform.scale(bullet_img_first, (13, 54*1.5))
pygame.display.set_icon(dad_life_img)
player_imgs = []
for i in range(3):
    img = pygame.image.load(os.path.join("img", f"dad{i}.png")).convert()
    img = pygame.transform.scale(img, (77, 137))
    img.set_colorkey(BLACK)
    player_imgs.append(img)


rock_imgs = []
for i in range(7):
    ball_size = random.randrange(40, 110)
    ball_img = pygame.image.load(os.path.join("img", f"ball{i}.png")).convert()
    if i ==2:
        rock_imgs.append(pygame.transform.scale(ball_img, (120, 120)))
    else:
        rock_imgs.append(pygame.transform.scale(ball_img, (ball_size, ball_size)))



expl_anim = {}
expl_anim['lg'] = []
expl_anim['sm'] = []
expl_anim['player'] = []
for i in range(9):
    expl_img = pygame.image.load(os.path.join("img", f"expl{i}.png")).convert()
    expl_img.set_colorkey(BLACK)
    expl_anim['lg'].append(pygame.transform.scale(expl_img, (75, 75)))
    expl_anim['sm'].append(pygame.transform.scale(expl_img, (30, 30)))
    player_expl_img = pygame.image.load(os.path.join("img", f"player_expl{i}.png")).convert()
    player_expl_img.set_colorkey(BLACK)
    expl_anim['player'].append(player_expl_img)


# load music
die_sound = pygame.mixer.Sound(os.path.join("sound", "rumble.ogg"))
expl_sounds = [
    pygame.mixer.Sound(os.path.join("sound", "expl0.wav")),
    pygame.mixer.Sound(os.path.join("sound", "expl1.wav"))
]
pygame.mixer.music.load(os.path.join("sound", "background.ogg"))
pygame.mixer.music.set_volume(0.4)

#  choose font
font_name = os.path.join("font.ttf")
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface, text_rect)

# make new rock
def new_rock():
    rock = Rock()
    all_sprites.add(rock)
    rocks.add(rock)

# display player's health
def draw_health(surf, hp, x, y):
    if hp < 0:
        hp = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (hp/100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)  # 2是外框的像素

# display player's lives
def draw_lives(surf, lives, img, x, y):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 80 * i
        img_rect.y = y
        surf.blit(img, img_rect)

def draw_level(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, ORANGE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface, text_rect)

def draw_init():
    screen.blit(background_img, (0, 0))
    draw_text(screen, "影像辨識躲避球", 64, WIDTH/2, HEIGHT/4)
    draw_text(screen, "按下a開始圈選物件", 24, WIDTH / 2, HEIGHT / 4 + 140)
    draw_text(screen, "按下Enter開始遊戲", 24, WIDTH / 2, HEIGHT / 4 + 210)
    pygame.display.update()
    waiting = True
    while waiting:
        clock.tick(FPS)
        # get input
        global stop_the_camera
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                stop_the_camera = True
                return True
            elif done:
                waiting = False
                return False

def draw_end():
    waiting = True
    while waiting:
        # display
        screen.blit(background_img, (0, 0))
        screen.blit(ending_background_img, (355, 160))
        draw_text(screen, "恭喜您被擊落!", 64, WIDTH / 2, HEIGHT / 5-100)
        draw_text(screen, "重新開始: 按 a", 24, WIDTH / 2, HEIGHT / 2 + 60)
        global check_time
        real_time = round(check_time/1000, 3)
        draw_text(screen, f"你存活的時間是:{real_time}秒", 24, WIDTH/2, HEIGHT / 2 +150)
        global longest_time
        if check_time >= longest_time:
            longest_time = check_time
        real_longest_time = round(longest_time/1000, 3)
        draw_text(screen, f"最長的存活時間是:{real_longest_time}秒", 24, WIDTH / 2, HEIGHT / 2 + 100)
        # update
        pygame.display.update()
        clock.tick(FPS)
        # get input
        global stop_the_camera
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                stop_the_camera = True
                return True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    waiting = False
                    return False
# define the characters in the game
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = player_imgs[0]
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()  # 將其定位，框起來
        self.radius = 19.5+26
        # 設置遊戲角色的初始位置
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.health = 100
        self.lives = 3
        self.hidden = False
        self.hide_time = 0
        self.lastTick = pygame.time.get_ticks()
        self.i = 0
        self.game_time = pygame.time.get_ticks()
        self.level = 1

    def update(self):
        now = pygame.time.get_ticks()
        # 更新遊戲角色的位置為手腕的位置
        self.rect.center = (the_x, the_y)

        if now - self.lastTick > 100:
            self.i += 1
            self.image = player_imgs[self.i%3]
            self.lastTick = now

        if self.hidden and now - self.hide_time > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.centery = HEIGHT -58


        if now - self.game_time >= 5000 and now - self.game_time < 10000:
            self.level = 2
        if now - self.game_time >= 10000 and now - self.game_time < 15000:
            self.level = 3
        if now - self.game_time >= 15000 and now - self.game_time < 20000:
            self.level = 4
        if now - self.game_time >= 20000:
            self.level = 5



    def hide(self):
        self.hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (WIDTH/2, HEIGHT + 500)


class Rock(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_ori = random.choice(rock_imgs)
        self.image_ori.set_colorkey(BLACK)
        self.image = self.image_ori.copy()
        self.rect = self.image.get_rect()  # 將其定位，框起來
        self.radius = int(self.rect.width  / 2)
        #test
        pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-180, -100)
        self.speedy = random.randrange(2, 10)
        self.speedx = random.randrange(-3, 3)
        self.total_degree = 0
        self.rot_degree = random.randrange(-5, 5)
        self.game_time = 0
        self.level_time = pygame.time.get_ticks()

    def rotate(self):
        self.total_degree += self.rot_degree
        self.total_degree = self.total_degree % 360
        self.image  = pygame.transform.rotate(self.image_ori, self.total_degree)
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center


    def update(self):
        now = pygame.time.get_ticks()
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx

        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(2, 10)
            self.speedx = random.randrange(-3, 3)
            if now - game_start_time >= 5000 and now - game_start_time < 10000:
                self.speedy = random.randrange(5, 15)
                self.speedx = random.randrange(-3, 3)
            if now - game_start_time >= 10000 and now - game_start_time < 15000:
                self.speedy = random.randrange(10, 20)
                self.speedx = random.randrange(-3, 3)
            if now - game_start_time >= 15000 and now - game_start_time < 20000:
                self.speedy = random.randrange(35, 45)
                self.speedx = random.randrange(-4, 4)
            if now - game_start_time >= 20000:
                self.speedy = random.randrange(55, 65)
                self.speedx = random.randrange(-7, 7)
            global check_time
            check_time = now - game_start_time


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = expl_anim[self.size][0]
        self.rect = self.image.get_rect()  # 將其定位，框起來
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame  == len(expl_anim[self.size]):
                self.kill()
            else:
                self.image = expl_anim[self.size][self.frame]
                center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = center

# turn the music on (repeat)
pygame.mixer.music.play(-1)

# game loop
show_init = True
running = True
show_end = False
while running:
    if show_init:
        close = draw_init()
        if close:
            break
        game_start_time = pygame.time.get_ticks()
        show_init = False
        # define sprite
        all_sprites = pygame.sprite.Group()
        rocks = pygame.sprite.Group()
        player = Player()
        all_sprites.add(player)
        # Reset the rock
        for i in range(8):
            new_rock()
        score = 0

    if show_end:
        show_end = False
        close = draw_end()
        if close:
            break
        # define sprite
        all_sprites = pygame.sprite.Group()
        rocks = pygame.sprite.Group()
        player = Player()
        player.level = 1
        all_sprites.add(player)
        # Reset the rock
        for i in range(8):
            new_rock()
        score = 0
        game_start_time = pygame.time.get_ticks()
    clock.tick(FPS)  # The number of times this loop can be executed in one second
    # get input

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            stop_the_camera = True

    # update the game
    all_sprites.update()
    hits = pygame.sprite.spritecollide(player, rocks, True, pygame.sprite.collide_circle)
    for hit in hits:
        new_rock()
        player.health -= 35 #hit.radius*2(原設定值)
        expl = Explosion(hit.rect.center, 'sm')
        all_sprites.add(expl)
        if player.health <= 0:
            die = Explosion(player.rect.center, 'player')
            all_sprites.add(die)
            die_sound.play()
            player.lives -= 1
            player.health = 100
            player.hide()


    if player.lives == 0 and not (die.alive()):
        show_end = True
        # show_init = True

    # screen display
    screen.fill(BLACK)  # (R, G, B)
    screen.blit(background_img, (0, 0))
    all_sprites.draw(screen)
    display_check_time = round(check_time/1000, 3)
    draw_text(screen, "time: " + str(display_check_time), 20, WIDTH/2, 10)
    if player.level <=4:
        draw_level(screen,"level: " + str(player.level),20, WIDTH/2-100, 10)
    if player.level == 5:
        draw_level(screen, "level: impossible", 25, WIDTH / 2 , 70)
    draw_text(screen, "blood: ", 22, WIDTH-200, 118)
    draw_health(screen, player.health, WIDTH-160, 130)
    draw_lives(screen, player.lives, player_mini_img, WIDTH - 250, 10)
    pygame.display.update()

pygame.quit()
