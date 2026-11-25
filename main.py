
import pygame
import sys

from logger import log_state, log_event
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()

clock = pygame.time.Clock()
dt = 0.0

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Create groups
updatable = pygame.sprite.Group()
drawable = pygame.sprite.Group()
asteroids = pygame.sprite.Group()
shots = pygame.sprite.Group()

# Assign containers
Player.containers = (updatable, drawable)
Asteroid.containers = (asteroids, updatable, drawable)
AsteroidField.containers = updatable
Shot.containers = (shots, updatable, drawable)

# Create objects
player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
asteroid_field = AsteroidField()

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill("black")

    # Update all objects
    updatable.update(dt)

    # Check player collisions with asteroids
    for asteroid in list(asteroids):
        if asteroid.collides_with(player):
            log_event("player_hit")
            print("Game over!")
            sys.exit()

    # Check shot collisions with asteroids
    for asteroid in list(asteroids):
        for shot in list(shots):
            if shot not in shots:
                continue

            if asteroid.collides_with(shot):
                log_event("asteroid_shot")
                shot.kill()
                asteroid.split()
                break

    # Log game state
    log_state()

    # Draw all objects
    for sprite in drawable:
        sprite.draw(screen)

    pygame.display.flip()

    dt = clock.tick(60) / 1000








