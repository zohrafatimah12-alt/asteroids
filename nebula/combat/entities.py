"""Combat objects, built on the original Asteroids CircleShape and Shot."""

import math
import random

import pygame

from circleshape import CircleShape  # original Asteroids base class
from shot import Shot  # original Asteroids projectile
from constants import SCREEN_HEIGHT as H, SCREEN_WIDTH as W


def heading_vector(rotation: float) -> pygame.Vector2:
    """Same convention as the original Player: 0 degrees points down-screen."""
    return pygame.Vector2(0, 1).rotate(rotation)


def bearing(origin: pygame.Vector2, target: pygame.Vector2) -> float:
    d = target - origin
    return math.degrees(math.atan2(-d.x, d.y))


def angle_diff(a: float, b: float) -> float:
    return (b - a + 180) % 360 - 180


class Aircraft(CircleShape):
    """Flight model: turn-rate limited heading with momentum (velocity lags the nose)."""

    alive_flag = True  # cleared when a wingman is shot down

    def __init__(self, x, y, *, speed, turn, grip, hp, radius=16, side="enemy", shape="delta"):
        super().__init__(x, y, radius)
        self.max_speed, self.turn_rate, self.grip = speed, turn, grip
        self.hp = self.max_hp = hp
        self.side, self.shape = side, shape
        self.rotation = 0.0
        self.throttle = 0.7
        self.gun_timer = 0.0
        self.stun = 0.0
        self.boost = 0.0
        self.trail: list[pygame.Vector2] = []

    def steer(self, amount: float, dt: float):
        self.rotation += max(-1.0, min(1.0, amount)) * self.turn_rate * dt

    def turn_toward(self, target: pygame.Vector2, dt: float):
        diff = angle_diff(self.rotation, bearing(self.position, target))
        self.steer(diff / max(1.0, self.turn_rate * dt), dt)

    def fly(self, dt: float):
        speed = self.max_speed * (0.35 + 0.65 * self.throttle) * (1.8 if self.boost > 0 else 1)
        if self.stun > 0:
            speed *= 0.3
        wanted = heading_vector(self.rotation) * speed
        self.velocity += (wanted - self.velocity) * min(1.0, self.grip * dt)
        self.position += self.velocity * dt
        self.gun_timer -= dt
        self.stun -= dt
        self.boost -= dt
        self.trail.append(self.position - heading_vector(self.rotation) * self.radius)
        del self.trail[:-14]


class Round(Shot):
    """A cannon shell or guided missile."""

    def __init__(self, position, velocity, side, damage, target=None, life=1.4):
        super().__init__(position.x, position.y)
        self.radius = 5 if target else 3
        self.velocity = velocity
        self.side, self.damage, self.target, self.life = side, damage, target, life

    def update(self, dt: float):
        if self.target is not None and self.target.hp > 0:
            diff = angle_diff(bearing(pygame.Vector2(), self.velocity),
                              bearing(self.position, self.target.position))
            self.velocity = self.velocity.rotate(max(-200 * dt, min(200 * dt, diff)))
        self.life -= dt
        super().update(dt)  # original movement and off-screen removal
        if self.life <= 0:
            self.kill()


class Fragment(CircleShape):
    """Shard-Star debris. Splits like the original asteroids."""

    MIN = 18

    def __init__(self, x, y, radius, velocity, rng: random.Random):
        super().__init__(x, y, radius)
        self.velocity = velocity
        self.rng = rng
        self.outline = [rng.uniform(0.75, 1.15) for _ in range(11)]

    def update(self, dt: float):
        self.position += self.velocity * dt
        if self.position.x < 0 or self.position.x > W:
            self.velocity.x *= -1

    def split(self) -> list["Fragment"]:
        self.kill()
        if self.radius <= self.MIN:
            return []
        angle = self.rng.uniform(20, 50)
        return [Fragment(self.position.x, self.position.y, self.radius - self.MIN,
                         self.velocity.rotate(a) * 1.15, self.rng) for a in (angle, -angle)]


class Particle:
    def __init__(self, position, velocity, life, color, size):
        self.position, self.velocity = pygame.Vector2(position), velocity
        self.life = self.max_life = life
        self.color, self.size = color, size

    def update(self, dt):
        self.life -= dt
        self.position += self.velocity * dt
        self.velocity *= max(0.0, 1 - 1.8 * dt)
