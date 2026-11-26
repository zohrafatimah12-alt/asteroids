"""Pygame front end for the combat simulation: input, rendering, cinematics."""

import math
import random

import pygame

from constants import SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from nebula.combat.audio import Audio
from nebula.combat.entities import heading_vector
from nebula.combat.sim import Controls, Sim, autopilot

V = pygame.Vector2
NAVY, CYAN, GOLD, WHITE = (6, 10, 28), (80, 220, 240), (240, 200, 110), (232, 238, 255)
RED, VIOLET, DIM = (255, 92, 92), (160, 125, 255), (120, 135, 170)
# Hull outlines in local coordinates; +y is the nose, matching the original Player.
SHAPES = {
    "delta": [(0, 1.3), (.95, -.9), (.25, -.55), (-.25, -.55), (-.95, -.9)],
    "arrow": [(0, 1.5), (.22, .3), (1.1, -.5), (.25, -.45), (.5, -1.1), (-.5, -1.1), (-.25, -.45), (-1.1, -.5), (-.22, .3)],
    "needle": [(0, 1.7), (.18, .1), (.75, -.95), (0, -.65), (-.75, -.95), (-.18, .1)],
    "glider": [(0, 1.1), (.18, .2), (1.6, -.1), (1.5, -.35), (.15, -.3), (.45, -1.1), (-.45, -1.1), (-.15, -.3), (-1.5, -.35), (-1.6, -.1), (-.18, .2)],
    "heavy": [(0, 1.25), (.35, .55), (1.4, 0), (1.35, -.4), (.35, -.3), (.35, -.9), (.75, -1.2), (-.75, -1.2), (-.35, -.9), (-.35, -.3), (-1.35, -.4), (-1.4, 0), (-.35, .55)],
}
PALETTE = {"player": CYAN, "ally": GOLD, "enemy": RED}


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.big = pygame.font.Font(None, 76)
        self.mid = pygame.font.Font(None, 34)
        rng = random.Random(7)
        self.stars = [(rng.uniform(0, W), rng.uniform(0, H), rng.choice((1, 1, 1, 2)), rng.uniform(5, 30))
                      for _ in range(150)]
        self.clouds = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(90, 220)) for _ in range(9)]
        self.sky = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            pygame.draw.line(self.sky, (int(5 + 20 * t), int(8 + 18 * t), int(24 + 44 * t)), (0, y), (W, y))
        self.glow = pygame.Surface((W, H), pygame.SRCALPHA)

    def text(self, value, pos, color=WHITE, font=None, center=False):
        image = (font or self.font).render(value, True, color)
        rect = image.get_rect(**({"center": pos} if center else {"topleft": pos}))
        self.screen.blit(image, rect)

    def aircraft(self, plane, color):
        if plane.shape == "base":
            for radius in (46, 30, 12):
                pygame.draw.circle(self.screen, color, plane.position, radius, 2)
            pygame.draw.line(self.screen, color, plane.position - V(70, 0), plane.position + V(70, 0), 3)
            return
        if plane.shape == "ground":
            r = plane.radius
            pygame.draw.rect(self.screen, color, (*(plane.position - V(r, r)), r * 2, r * 2), 2)
            pygame.draw.line(self.screen, color, plane.position,
                             plane.position + heading_vector(plane.rotation) * (r + 12), 4)
            return
        for i, point in enumerate(plane.trail):
            pygame.draw.circle(self.screen, [c * (i + 1) // 22 + 12 for c in color], point, max(1, i // 5))
        points = [plane.position + V(x, y).rotate(plane.rotation) * plane.radius for x, y in SHAPES[plane.shape]]
        pygame.draw.polygon(self.screen, [c // 4 for c in color], points)
        pygame.draw.polygon(self.screen, color, points, 2)

    def bar(self, x, y, label, ratio, color):
        self.text(label, (x, y), DIM)
        pygame.draw.rect(self.screen, (40, 48, 76), (x + 74, y + 3, 160, 9))
        pygame.draw.rect(self.screen, color, (x + 74, y + 3, int(160 * max(0, min(1, ratio))), 9))

    def draw(self, sim: Sim):
        s = self.screen
        s.blit(self.sky, (0, 0))
        for x, y, size, speed in self.stars:
            pygame.draw.circle(s, (150, 165, 215), ((x - sim.time * speed) % W, y), size)
        self.glow.fill((0, 0, 0, 0))
        if sim.weather in ("cloud", "storm"):
            for x, y, r in self.clouds:
                pygame.draw.ellipse(self.glow, (120, 135, 180, 28), ((x - sim.time * 14) % (W + r) - r, y, r * 2, r * .7))
        pygame.draw.circle(self.glow, (255, 214, 140, 22), (W - 130, 90), 90)
        pygame.draw.circle(self.glow, (255, 232, 180, 200), (W - 130, 90), 16)
        s.blit(self.glow, (0, 0))
        if sim.weather in ("storm", "wind"):
            for i in range(90):
                x = (i * 137 + sim.time * 500) % W
                y = (i * 71 + sim.time * (700 if sim.weather == "storm" else 40)) % H
                pygame.draw.line(s, (90, 120, 180), (x, y), (x + 6, y + (14 if sim.weather == "storm" else 1)))

        for index, site in enumerate(sim.sites):
            if sim.kind == "rescue" and index == 1 and not sim.sites[0]["done"]:
                continue
            color = GOLD if site["done"] else VIOLET
            pygame.draw.circle(s, color, site["pos"], 70, 1)
            pygame.draw.circle(s, color, site["pos"], 6 + 3 * math.sin(sim.time * 5))
            if site["progress"] > 0:
                pygame.draw.arc(s, CYAN, (*(site["pos"] - V(56, 56)), 112, 112), 0, site["progress"] * math.tau, 5)
        for f in sim.fragments:
            points = [f.position + V(f.radius * k, 0).rotate(i * 360 / len(f.outline) + sim.time * 30)
                      for i, k in enumerate(f.outline)]
            pygame.draw.polygon(s, (48, 30, 74), points)
            pygame.draw.polygon(s, VIOLET, points, 2)
        if sim.structure is not None and sim.kind != "emergency":
            self.aircraft(sim.structure, GOLD)
        for e in sim.enemies:
            visible = sim.detected(e) or e.role == "ground"
            if visible:
                self.aircraft(e, VIOLET if e.role == "ace" else RED)
                if e.hp < e.max_hp:
                    pygame.draw.rect(s, RED, (e.position.x - 18, e.position.y - e.radius - 14, 36 * max(0, e.hp) / e.max_hp, 3))
                if e.stun > 0:
                    pygame.draw.circle(s, CYAN, e.position, e.radius + 8, 1)
        if sim.wingman and sim.wingman.alive_flag:
            self.aircraft(sim.wingman, GOLD)
        for r in sim.rounds:
            color = (255, 150, 90) if r.side == "enemy" else (190, 250, 255)
            pygame.draw.line(s, color, r.position, r.position - r.velocity * (0.04 if r.target else 0.018), 4 if r.target else 2)
        if sim.player.hp > 0:
            self.aircraft(sim.player, CYAN)
            if sim.effect_timer > 0:
                pygame.draw.circle(s, CYAN, sim.player.position, 32, 1)
        for p in sim.particles:
            fade = max(0.0, p.life / p.max_life)
            pygame.draw.circle(s, [int(c * fade) for c in p.color], p.position, max(1, p.size * fade))
        self.hud(sim)

    def hud(self, sim: Sim):
        s, m = self.screen, sim.mission
        self.text(f"LEVEL {m['level']}  {m['title'].upper()}  |  {m['type_label']}  |  {m['location']}  |  {sim.weather}", (16, 12), GOLD)
        self.text(sim.message, (16, 36))
        self.bar(16, H - 92, "HULL", sim.player.hp / sim.player.max_hp, RED if sim.player.hp < sim.player.max_hp * .3 else CYAN)
        self.bar(16, H - 72, "FUEL", sim.fuel / 100, GOLD)
        self.bar(16, H - 52, "THRUST", sim.player.throttle, VIOLET)
        ready = max(0.0, sim.ability_timer)
        self.text(f"GUNS {sim.ammo}   MISSILES {sim.missiles}   [Q] {sim.ability.upper()} "
                  + ("READY" if ready == 0 else f"{ready:.0f}s"), (16, H - 30))
        # Radar: contacts appear only inside the airframe's detection range.
        center, radius = V(W - 100, H - 100), 82
        pygame.draw.circle(s, (8, 22, 34), center, radius)
        for ring in (radius, radius * .62, radius * .3):
            pygame.draw.circle(s, (36, 95, 112), center, ring, 1)
        pygame.draw.line(s, CYAN, center, center + V(radius, 0).rotate(sim.time * 150), 2)
        for e in sim.enemies:
            if sim.detected(e):
                pygame.draw.circle(s, RED, center + (e.position - sim.player.position) * (radius / sim.radar), 3)
        pygame.draw.circle(s, CYAN, center, 3)
        self.text("W/S throttle  A/D turn  SPACE guns  F missile  Q ability  P pause  ESC abort", (16, 60), DIM)

    def overlay(self, title, lines, footer):
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((*NAVY, 214))
        self.screen.blit(shade, (0, 0))
        self.text(title, (W / 2, 230), GOLD, self.big, center=True)
        for i, line in enumerate(lines):
            self.text(line, (W / 2, 320 + i * 38), WHITE, self.mid, center=True)
        self.text(footer, (W / 2, 530), CYAN, center=True)


def wrap(text, width=72):
    lines = [""]
    for word in text.split():
        if len(lines[-1]) + len(word) >= width:
            lines.append("")
        lines[-1] = f"{lines[-1]} {word}".strip()
    return lines


def run(ticket: dict, auto: bool = False, sound: bool = True) -> dict | None:
    """Fly one sortie. Returns the result, or None if the player closed the briefing."""
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("NEBULA: Air Combat")
    clock = pygame.time.Clock()
    sim, view, audio = Sim(ticket), Renderer(screen), Audio(sound)
    phase, elapsed, paused, dt = "briefing", 0.0, False, 0.0
    try:
        while True:
            pressed = set()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if phase == "briefing":
                        return None
                    # Leaving mid-flight counts as an abort, so it cannot dodge a defeat.
                    sim.outcome = bool(sim.outcome)
                    return sim.result()
                if event.type == pygame.KEYDOWN:
                    pressed.add(event.key)
            m = sim.mission
            if phase == "briefing":
                elapsed += dt
                sim.time += dt * 0.4
                view.draw(sim)
                lines = wrap(m["story"])[: 1 + int(elapsed * 2)]  # typed-in briefing
                view.overlay(m["title"], lines + ["", m["objectives"][0]], "ENTER to launch   ESC to stand down")
                if pygame.K_ESCAPE in pressed:
                    return None
                if pygame.K_RETURN in pressed or (auto and elapsed > 1):
                    phase, sim.time = "flight", 0.0
            elif phase == "flight":
                if pygame.K_p in pressed:
                    paused = not paused
                if pygame.K_ESCAPE in pressed:
                    sim.outcome = False
                    sim.message = "Mission aborted"
                if not paused:
                    keys = pygame.key.get_pressed()
                    controls = autopilot(sim) if auto else Controls(
                        turn=(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
                        throttle=(keys[pygame.K_w] or keys[pygame.K_UP]) - (keys[pygame.K_s] or keys[pygame.K_DOWN]),
                        fire=keys[pygame.K_SPACE], missile=pygame.K_f in pressed, ability=pygame.K_q in pressed)
                    sim.step(controls, dt)
                    for name in set(sim.sounds):
                        audio.play(name)
                    sim.sounds.clear()
                view.draw(sim)
                if paused:
                    view.overlay("PAUSED", [], "P to resume")
                if sim.outcome is not None:
                    phase, elapsed = "debrief", 0.0
                    audio.play("win" if sim.outcome else "lose")
            else:
                elapsed += dt
                sim.step(Controls(), dt)
                view.draw(sim)
                if elapsed > 1.2:
                    r = sim.result()
                    accuracy = f"{r['hits'] / r['shots']:.0%}" if r["shots"] else "n/a"
                    view.overlay("MISSION COMPLETE" if r["success"] else "MISSION FAILED",
                                 [f"Kills {r['kills']}    Accuracy {accuracy}", f"Hull damage {r['damage_taken']}%    Time {r['duration']}s"],
                                 "ENTER to return to command")
                    if pygame.K_RETURN in pressed or (auto and elapsed > 3):
                        return sim.result()
            pygame.display.flip()
            dt = min(0.05, clock.tick(60) / 1000)  # original delta-time loop, clamped
    finally:
        pygame.quit()
