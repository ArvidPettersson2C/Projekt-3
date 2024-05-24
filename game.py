#Author: Arvid Pettersson
#Date: 2024-05-24
#Description: A platformer game where the player jumps around and shoots colourfull confetti
import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_VEL = 5
respawn_point = WIDTH//2, HEIGHT//2
firerate = 1000.0


window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


# initialiserar spelareklassen
class Player(pygame.sprite.Sprite):

    # Konstant färg för spelaren (RGB)
    COLOR = (255, 0, 0)

    # Konstant för gravitationens styrka
    GRAVITY = 1
    
    # Tar sprite sheets för spelaren från mappen "assets"
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)

    # Konstant för fördröjning mellan animationer
    ANIMATION_DELAY = 3
    
    # Funktion som etablerar variabler för spelaren
    def __init__(self, x, y, width, height):
        super().__init__()

        # Initierar spelarens rektangel (position och storlek)
        self.rect = pygame.Rect(x, y, width, height)

        # Initierar hastigheter och andra attribut
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.projectiles = []
        self.last_shot_time = 0

    # Funktion som hanterar hopp
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
    
    # Funktion som hanterar dubbelhopp (om hoppknappen trycks när man är i ett hopp)
    def double_jump(self):
        self.y_vel = -self.GRAVITY * 14
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
    
    # Funktion som hanterar avfyrandet av projektiler och eldhastighet
    def shoot(self, firerate): 
        current_time = pygame.time.get_ticks()
        time_since_last_shot = current_time - self.last_shot_time

        if time_since_last_shot >= firerate:
            projectileDirection = -20 if self.direction == "left" else 20
            self.projectiles.append([[self.rect.centerx, self.rect.centery], projectileDirection, 0])
            self.last_shot_time = current_time

    # Funktion för att förflytta spelaren i riktning i x-led oxh y-led
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    
    # funktion för att flytta spelaren åt vänster
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    # funktion för att flytta spelaren åt höger
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    # Funktion för spelarens gravitation
    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        self.fall_count += 1
        self.update_sprite()

    # Funktion för att ta bort spelarens hastighet när den landar efter ett hopp samt återställer räknare så att spelaren inte bara dubbelhoppar
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
    
    # Uppdaterar spelarens sprite (utseende) beroende på dess tillstånd
    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count > 1:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # Uppdaterar spelarens rektangel och mask baserat på sprite
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    # Ritar spelaren på skärmen
    def draw(self, win, offset_x, offset_y):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))

    # Ritar projektilen på skärmen
    def draw_proj(self, win, offset_x, offset_y, projectile):
        img = pygame.image.load("assets/Other/Confetti (16x16).png")
        win.blit(img, (projectile[0][0] - offset_x - img.get_size()[0]/2, projectile[0][1] - offset_y ))

# Initialiserar klassen för objet (alla typer av objekt som syns)
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
        
    # Funktion som ritar ut objektet 
    def draw(self, win, offset_x, offset_y):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

# klass för Blocken som bygger banan
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

# Laddar bakgrundsbilden från mappen "Background" i mappen "assets"
def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

# Funktion för att skriva ut bakgrundsbilden
def draw(window, background, bg_image, player, objects, offset_x, offset_y, projectiles):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x, offset_y)
    #rita ut projektilerna
    for projectile in projectiles:
        player.draw_proj(window, offset_x, offset_y, projectile)

    player.draw(window, offset_x, offset_y)

    pygame.display.update()

# Funktion för att ta bort projektilerna när de träffar ett objekt
def handle_projectile_collision(player, projectiles, objects):
    for projectile in projectiles.copy():
        
        for obj in objects:
            if obj.rect.colliderect(pygame.image.load("assets/Other/Confetti (16x16).png").get_rect().move(projectile[0][0], projectile[0][1])):
                projectiles.remove(projectile)
                break


# Funktion för att hantera att spelaren landar på marken efteråt (vertikal kollision)
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0: 
                player.rect.bottom = obj.rect.top
                player.landed()
            

            collided_objects.append(obj)
    return collided_objects

# Funktion för att hantera att spelaren springer in en vägg (horisontell kollision)
def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

# Hanterar spelarens rörelser baserat på knapptryckningar
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

# Återställer spelaren, golvet och objekten till startläget
def reset(player, floor, objects, offset_x, offset_y):
    block_size = 96

    player = Player(WIDTH//2, 100, 50, 50) 
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size)]

    offset_x = 0

    offset_y = 0

    return(player, floor, objects, offset_x, offset_y)

# Huvudfunktion för spelet
    # Parametrar:
    #   - pygame.Surface window: Fönstret där spelet visas
    # Return: None
def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(WIDTH//2, 100, 50, 50) 
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size)]

    offset_x = 0
    offset_y = 0
    scroll_area_width = 350
    scroll_area_height = 250

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w and player.jump_count < 2:
                    player.jump()
                    if event.key == pygame.K_w and player.jump_count > 1:
                        player.double_jump()
                if event.key == pygame.K_SPACE:
                    player.shoot(firerate)

                
                
                    

        player.loop(FPS)

        for projectile in player.projectiles.copy():
            projectile[0][0] += projectile[1]
            projectile[2] += 1
            
            if projectile[2] > 150:
                player.projectiles.remove(projectile)

        handle_projectile_collision(player, player.projectiles, objects)

        

        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x, offset_y, player.projectiles)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
        
        if ((player.rect.top - offset_y >= HEIGHT - scroll_area_height) and player.y_vel > 0) or (
                (player.rect.bottom - offset_y <= scroll_area_height) and player.y_vel < 0):
            offset_y += player.y_vel

        if player.rect.top > HEIGHT:
            player, floor, objects, offset_x, offset_y = reset(player, floor, objects, offset_x, offset_y)
        


    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)