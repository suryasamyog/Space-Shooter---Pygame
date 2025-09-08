
import pygame
from os.path import join
from random import randint, uniform


class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_frect(center = (window_w/2, window_h/2))
        self.direction = pygame.math.Vector2()
        self.speed = 300

        self.can_shoot = True
        self.shoot_time = 0
        self.shoot_cooldown = 400 #milliseconds

        self.mask = pygame.mask.from_surface(self.image)

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.shoot_cooldown:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction.normalize() if self.direction.magnitude() > 0 else self.direction
        self.rect.center += self.direction * self.speed * dt

        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()
            laser_sound.play()
        
        self.laser_timer()

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = (randint(0, window_w), randint(0, window_h)))
        self.image = pygame.transform.scale(self.image, (randint(15,20), randint(15,20)))
        self.blink_time = pygame.time.get_ticks()
        self.blink_duration = randint(200, 1000)
        self.visible = True

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.blink_time >= self.blink_duration:
            self.visible = not self.visible
            self.blink_time = current_time
            self.blink_duration = randint(200, 1000)

        if self.visible:
            self.image.set_alpha(255)
        else:
            self.image.set_alpha(100)

class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom = pos) 

        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.centery -= 400 * dt
        if self.rect.bottom < 0:
            self.kill()

class Heart(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_image = pygame.transform.scale(surf, (40, 40))
        self.image = self.original_image
        self.rect = self.image.get_frect(midtop=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.expand_time = pygame.time.get_ticks()
        self.expand_duration = 500  # milliseconds
        self.expanded = False

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.expand_time >= self.expand_duration:
            self.expand_time = current_time
            self.expanded = not self.expanded

        if self.expanded:
            self.image = pygame.transform.scale(self.original_image, (50, 50))
        else:
            self.image = self.original_image
        self.rect = self.image.get_frect(center=self.rect.center)

    @staticmethod
    def create_hearts(surf, groups, window_w):
        positions = [
            (window_w // 2 - 70, 50),
            (window_w // 2, 50),
            (window_w // 2 + 70, 50)
        ]
        return [Heart(surf, pos, groups) for pos in positions]
    
    @staticmethod
    def delete_hearts(hearts):
        global game_over
        if hearts:
            hearts[-1].kill()
            hearts.pop()

        if hearts == []:
            explosion = AnimatedExplosion(explosion_frames, player.rect.center, all_sprites)
            explosion = pygame.transform.scale(explosion.image, (1000, 1000))
            explosion_sound.play()
            player.kill()
            game_over = True

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_image = surf
        self.image = surf
        self.rect = self.image.get_frect(center = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4000
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)

        self.rotation_speed = randint(40, 80)
        self.angle = 0

        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

        self.angle += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1)
        self.rect = self.image.get_frect(center = self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center = pos)
        

    def update(self, dt):
        self.frame_index += 30 * dt
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)] 
            
def collision():
    global score
    for laser in laser_sprites:
        collided_laser = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if collided_laser:
            laser.kill()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_sound.play()
            score += 1
            

    if pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask):
        damage_sound.play()
        Heart.delete_hearts(hearts)
        
def score_display():
    current_time = pygame.time.get_ticks() // 1000
    score_surf = font.render(str(score), True, 'white')
    score_rect = score_surf.get_frect(midbottom = (window_w/2, window_h - 50))
    screen.blit(score_surf, score_rect)
    pygame.draw.rect(screen, 'white', score_rect.inflate(30,10).move(-1, -5), 5, 10)

def show_game_over():
    over_surf = font0.render("GAME OVER", True, (240, 240, 240))
    over_rect = over_surf.get_frect(center=(window_w//2, window_h//2 - 100))
    restart_surf = font1.render("PRESS R TO RESTART", True, (240, 240, 240))
    restart_rect = restart_surf.get_frect(center=(window_w//2, window_h//2 + 100))
    screen.blit(over_surf, over_rect)
    screen.blit(restart_surf, restart_rect)

#general setup
pygame.init()
window_w, window_h = 1280, 720
screen = pygame.display.set_mode((window_w, window_h))
pygame.display.set_caption("Space Shooter")
running = True
game_over = False
score = 0
clock = pygame.time.Clock()


#sprite groups and imports
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
for s in range(40):
    Star(all_sprites, star_surf)

heart_surf = pygame.image.load(join('images', 'purple.png')).convert_alpha()
hearts = Heart.create_hearts(heart_surf, all_sprites, window_w)
player = Player(all_sprites) 

meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Minecraft.ttf'), 40)
font0 = pygame.font.Font(join('images', 'Minecraft.ttf'), 80)
font1 = pygame.font.Font(join('images', 'Minecraft.ttf'), 20)
explosion_frames = [pygame.image.load(join('images', 'explosion', f'{frame}.png')).convert_alpha() for frame in range(21)]


#sounds
laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
laser_sound.set_volume(0.4)
explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
explosion_sound.set_volume(0.4)
game_sound = pygame.mixer.Sound(join('audio', 'game_music.wav'))
game_sound.set_volume(0.2)
damage_sound = pygame.mixer.Sound(join('audio', 'damage.ogg'))
damage_sound.set_volume(0.6)
game_sound.play(loops = -1)


#custom event
meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, 300)

#game loop
while running:
    dt = clock.tick() / 1000 
    
    #event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not game_over and event.type == meteor_event:
            x, y = randint(0, window_w), -50
            Meteor(meteor_surf, (x,y), (all_sprites, meteor_sprites))
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            
            score = 0
            game_over = False

            all_sprites.empty()
            meteor_sprites.empty()
            laser_sprites.empty()

            for s in range(40):
                Star(all_sprites, star_surf)
            
            hearts = Heart.create_hearts(heart_surf, all_sprites, window_w)
            player = Player(all_sprites)
        

    if not game_over:
        collision()
        all_sprites.update(dt)
    # fill the screen with red color
    screen.fill("#19091C")

        
    #screen.blit(player_surf, player_rect) 
    
    all_sprites.draw(screen)
    score_display()

    if game_over:
        show_game_over()
    
    # draw the game
    pygame.display.update()

pygame.quit()