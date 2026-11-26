"""Headless combat simulation: input in, state and events out. No rendering here."""

import random
from dataclasses import dataclass

import pygame

from constants import SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from nebula.combat.entities import (Aircraft, Fragment, Particle, Round, angle_diff, bearing,
                                    heading_vector)

V = pygame.Vector2
ABILITY_COOLDOWN = 14.0
TIME_LIMIT = 240.0
WEATHER_VISION = {"clear": 1.0, "cloud": 0.85, "wind": 0.95, "storm": 0.65}


@dataclass
class Controls:
    turn: float = 0.0      # -1 left, 1 right
    throttle: float = 0.0  # -1 slower, 1 faster
    fire: bool = False
    missile: bool = False
    ability: bool = False


class Sim:
    def __init__(self, ticket: dict):
        self.mission = m = ticket["mission"]
        p = ticket["plane"]
        self.rng = random.Random(ticket["seed"])
        self.kind, self.d, self.params = m["type"], m["difficulty"], m["params"]
        self.weather = ticket["weather"]
        self.wind = V(self.rng.choice([-18, 18]), 0) if self.weather == "wind" else V()
        self.vision = WEATHER_VISION[self.weather]

        hull = 70 + p["armour"]
        self.player = Aircraft(W * 0.18, H * 0.55, speed=110 + p["speed"] * 2.0,
                               turn=100 + p["agility"] * 2.1, grip=1.6 + p["agility"] / 28,
                               hp=hull, side="player", shape=p["silhouette"])
        self.player.max_hp = hull
        self.player.hp = hull * p["condition"] / 100
        self.start_hp = self.player.hp
        self.player.rotation = -90
        self.ability = p["ability"]
        self.ability_timer = 0.0
        self.effect_timer = 0.0
        self.ammo = self.start_ammo = p["ammo_now"]
        self.missiles = 2 + (p["category"] in ("fighter", "interceptor", "bomber"))
        self.missile_timer = 0.0
        self.fuel = float(p["fuel_now"])
        self.fuel_burn = 0.30 * (1.35 - p["range"] / 150)
        self.start_fuel = self.fuel
        # Detection radius in pixels, from the airframe's radar and the weather.
        self.radar = (260 + p["radar"] * 6) * self.vision
        self.ground_bonus = 1.8 if p["category"] in ("bomber", "heavy") else 1.0

        self.enemies, self.rounds, self.fragments = (pygame.sprite.Group() for _ in range(3))
        self.particles: list[Particle] = []
        self.sounds: list[str] = []
        self.time = 0.0
        self.spawned = self.kills = self.shots = self.hits = self.escaped = 0
        self.destroyed = 0
        self.spawn_timer = 1.0
        self.outcome: bool | None = None
        self.message = m["objectives"][0]
        self.structure = None  # protected installation or transport
        self.sites: list[dict] = []
        self.wingman = None
        if ticket["wingman"]:
            self.wingman = Aircraft(W * 0.12, H * 0.7, speed=210, turn=170, grip=3, hp=80,
                                    side="ally", shape="arrow")
        self._setup()

    # -- setup ---------------------------------------------------------------
    def _setup(self):
        k = self.kind
        if k == "escort":
            self.structure = Aircraft(40, H * 0.5, speed=22, turn=60, grip=3, hp=260 + 20 * self.d,
                                      radius=30, side="ally", shape="heavy")
            self.structure.rotation, self.structure.throttle = -90, 1.0
        elif k in ("defence", "airbase"):
            self.structure = Aircraft(W / 2, H - 90, speed=0, turn=0, grip=0, hp=300 + 20 * self.d,
                                      radius=46, side="ally", shape="base")
        elif k == "emergency":
            self.structure = Aircraft(W / 2, H + 200, speed=0, turn=0, grip=0, hp=100, radius=1,
                                      side="ally", shape="ground")
        elif k in ("reconnaissance", "investigation"):
            self.sites = [{"pos": V(self.rng.uniform(280, W - 120), self.rng.uniform(110, H - 110)),
                           "progress": 0.0, "done": False} for _ in range(self.params["n"])]
        elif k == "rescue":
            self.sites = [{"pos": V(W - 170, self.rng.uniform(150, H - 150)), "progress": 0.0, "done": False},
                          {"pos": V(130, H * 0.55), "progress": 0.0, "done": False}]
        elif k == "strike":
            for _ in range(self.params["n"]):
                gun = Aircraft(self.rng.uniform(W * 0.45, W - 80), self.rng.uniform(90, H - 90),
                               speed=0, turn=140, grip=0, hp=55 + 9 * self.d, radius=22, shape="ground")
                self._add_enemy(gun, "ground")

    def _add_enemy(self, plane: Aircraft, role: str):
        plane.role, plane.state, plane.state_timer = role, "patrol", 0.0
        self.enemies.add(plane)

    def _spawn_enemy(self, role="hunter"):
        ace = role == "ace"
        x, y = W + 20, self.rng.uniform(70, H - 70)
        if role == "hunter" and self.kind in ("defence", "airbase"):
            x, y = self.rng.choice([(W + 20, y), (-20, y), (self.rng.uniform(100, W - 100), -20)])
        plane = Aircraft(x, y, speed=(95 + 11 * self.d) * (1.2 if ace else 1),
                         turn=75 + 9 * self.d + (35 if ace else 0), grip=3.0,
                         hp=(22 + 6 * self.d) * (4 if ace else 1), radius=24 if ace else 15,
                         shape="needle" if role == "intruder" else "arrow" if ace else "delta")
        plane.rotation = 90
        plane.lane = y
        self._add_enemy(plane, role)
        self.spawned += 1

    # -- helpers -------------------------------------------------------------
    def burst(self, position, color, count=24, power=190):
        for _ in range(count):
            vel = V(1, 0).rotate(self.rng.uniform(0, 360)) * self.rng.uniform(20, power)
            self.particles.append(Particle(position, vel, self.rng.uniform(0.3, 0.9), color,
                                           self.rng.uniform(1.5, 4)))

    def detected(self, target) -> bool:
        return self.player.position.distance_to(target.position) <= self.radar

    def _fire(self, plane, side, damage, spread=0.0, speed=520, target=None):
        direction = heading_vector(plane.rotation + self.rng.uniform(-spread, spread))
        self.rounds.add(Round(plane.position + direction * (plane.radius + 6), direction * speed,
                              side, damage, target, life=2.6 if target else 1.2))

    # -- player --------------------------------------------------------------
    def _player_step(self, c: Controls, dt: float):
        p = self.player
        p.steer(c.turn, dt)
        p.throttle = max(0.0, min(1.0, p.throttle + c.throttle * dt * 1.2))
        p.fly(dt)
        p.position += self.wind * dt
        p.position.x = max(20, min(W - 20, p.position.x))
        p.position.y = max(20, min(H - 20, p.position.y))
        self.fuel = max(0.0, self.fuel - self.fuel_burn * (0.5 + p.throttle) * dt)
        if self.fuel <= 0:
            p.throttle = 0.0
        if c.fire and p.gun_timer <= 0 and self.ammo > 0:
            p.gun_timer = 0.14
            self.ammo -= 1
            self.shots += 1
            self._fire(p, "player", 11, spread=1.5, speed=640)
            self.sounds.append("gun")
        self.missile_timer -= dt
        if c.missile and self.missiles > 0 and self.missile_timer <= 0:
            locks = [e for e in self.enemies if self.detected(e)
                     and abs(angle_diff(p.rotation, bearing(p.position, e.position))) < 60]
            if locks:
                target = min(locks, key=lambda e: p.position.distance_to(e.position))
                self.missiles -= 1
                self.shots += 1
                self.missile_timer = 0.8
                self._fire(p, "player", 60 * (self.ground_bonus if target.role == "ground" else 1),
                           speed=430, target=target)
                self.sounds.append("missile")
        self.ability_timer -= dt
        self.effect_timer -= dt
        if c.ability and self.ability_timer <= 0:
            self._use_ability()

    def _use_ability(self):
        p, a = self.player, self.ability
        self.ability_timer = ABILITY_COOLDOWN
        self.sounds.append("ability")
        self.burst(p.position, (90, 230, 255), 18, 120)
        if a == "surge":
            p.boost = 2.5
        elif a == "chaff":
            for r in list(self.rounds):
                if r.side == "enemy" and r.position.distance_to(p.position) < 240:
                    r.kill()
        elif a in ("veil", "deepscan", "ironhull"):
            self.effect_timer = 6.0
        elif a == "pulse":
            for e in self.enemies:
                if e.position.distance_to(p.position) < 300:
                    e.stun = 3.5
        elif a == "patch":
            p.hp = min(p.max_hp, p.hp + p.max_hp * 0.25)
        elif a == "salvo":
            for offset in range(-24, 25, 8):
                direction = heading_vector(p.rotation + offset)
                self.rounds.add(Round(p.position + direction * 20, direction * 560, "player", 14))
                self.shots += 1

    def active(self, ability: str) -> bool:
        return self.ability == ability and self.effect_timer > 0

    # -- enemy AI ------------------------------------------------------------
    def _enemy_step(self, e: Aircraft, dt: float):
        e.state_timer -= dt
        if e.stun > 0:
            if e.role != "ground":
                e.fly(dt)
            else:
                e.stun -= dt
            return
        target = self.player
        sight = 520 * self.vision * (0.3 if self.active("veil") else 1)
        # Escort and base-defence raiders prefer the protected asset.
        if (self.structure is not None and self.kind in ("escort", "defence", "airbase")
                and e.position.distance_to(self.player.position) > 220):
            target, sight = self.structure, 2000
        elif self.wingman and self.wingman.alive_flag and self.rng.random() < 0.001:
            target = self.wingman
        distance = e.position.distance_to(target.position)
        if e.role == "intruder" and (e.hp >= e.max_hp or distance > 300):  # fights only when hit
            e.state = "run"
        elif e.state == "evade" and e.state_timer > 0:
            pass
        elif distance < 75 and e.role != "ground":
            e.state, e.state_timer = "evade", 1.1
            e.break_side = self.rng.choice((-1, 1))
        elif distance < sight:
            e.state = "attack"
        else:
            e.state = "patrol"

        if e.state == "run":
            e.turn_toward(V(e.position.x - 200, e.lane), dt)
        elif e.state == "evade":
            e.steer(e.break_side, dt)
        elif e.state == "attack":
            # Lead pursuit: aim where the target will be, better at higher difficulty.
            lead = target.velocity * (distance / 520) * min(1.0, self.d / 8)
            e.turn_toward(target.position + lead, dt)
        else:
            e.turn_toward(V(W / 2, H / 2) + V(240, 0).rotate(self.time * 25 + e.max_hp * 7), dt)
        if e.role != "ground":
            e.fly(dt)
        else:
            e.gun_timer -= dt
        aim = abs(angle_diff(e.rotation, bearing(e.position, target.position)))
        if e.state in ("attack", "run") and distance < 380 and aim < 14 and e.gun_timer <= 0:
            e.gun_timer = max(0.55, 1.7 - 0.13 * self.d) * (0.55 if e.role == "ace" else 1)
            self._fire(e, "enemy", 3.5 + 0.8 * self.d, spread=max(2, 10 - self.d), speed=360)
        if e.role == "intruder" and e.position.x < -25:
            e.kill()
            self.escaped += 1

    def _wingman_step(self, dt):
        w = self.wingman
        if not w or not w.alive_flag:
            return
        foes = list(self.enemies)
        goal = (min(foes, key=lambda e: w.position.distance_to(e.position)).position if foes
                else self.player.position + V(-70, 60))
        w.turn_toward(goal, dt)
        w.fly(dt)
        if foes and w.gun_timer <= 0 and w.position.distance_to(goal) < 340 \
                and abs(angle_diff(w.rotation, bearing(w.position, goal))) < 12:
            w.gun_timer = 0.8
            self._fire(w, "ally", 7)

    # -- collisions ----------------------------------------------------------
    def _damage_player(self, amount: float):
        if self.active("ironhull"):
            amount *= 0.35
        self.player.hp -= amount
        self.sounds.append("hit")
        self.burst(self.player.position, (255, 170, 80), 6, 110)

    def _destroy(self, enemy, by_player: bool):
        enemy.hp = 0
        enemy.kill()
        self.destroyed += 1
        self.kills += by_player
        self.sounds.append("boom")
        self.burst(enemy.position, (255, 130, 60), 34, 240)

    def _collisions(self):
        for r in list(self.rounds):
            if r.side == "enemy":
                victims = [self.player]
                if self.structure is not None and self.kind in ("escort", "defence", "airbase"):
                    victims.append(self.structure)
                if self.wingman and self.wingman.alive_flag:
                    victims.append(self.wingman)
                for v in victims:
                    if r.collides_with(v):
                        r.kill()
                        if v is self.player:
                            self._damage_player(r.damage)
                        else:
                            v.hp -= r.damage
                        break
                continue
            for e in list(self.enemies):
                if r.collides_with(e):
                    r.kill()
                    e.hp -= r.damage
                    self.hits += r.side == "player"
                    self.burst(r.position, (255, 220, 120), 5, 90)
                    if e.hp <= 0:
                        self._destroy(e, r.side == "player")
                    break
            else:
                for f in list(self.fragments):
                    if r.collides_with(f):
                        r.kill()
                        self.hits += r.side == "player"
                        self.burst(f.position, (190, 160, 255), 14, 130)
                        self.fragments.add(*f.split())
                        self.destroyed += 1
                        self.sounds.append("boom")
                        break
        for f in list(self.fragments):
            if f.collides_with(self.player):
                self._damage_player(14)
                f.kill()
            elif f.position.y > H + f.radius:
                self.structure.hp -= f.radius / 3
                f.kill()
        for e in list(self.enemies):
            if e.collides_with(self.player) and e.role != "ground":
                self._damage_player(18)
                self._destroy(e, True)
        if self.wingman and self.wingman.hp <= 0 and self.wingman.alive_flag:
            self.wingman.alive_flag = False
            self.burst(self.wingman.position, (120, 200, 255))

    # -- objectives ----------------------------------------------------------
    def _spawn_wave(self, dt, role, limit, total=None, interval=3.0):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.enemies) < limit and (total is None or self.spawned < total):
            self.spawn_timer = interval
            self._spawn_enemy(role)

    def _scan(self, site, dt, hold):
        if self.player.position.distance_to(site["pos"]) < 70:
            site["progress"] += dt * (2.5 if self.active("deepscan") else 1) / hold
        else:
            site["progress"] = max(0.0, site["progress"] - dt * 0.15)
        if site["progress"] >= 1:
            site["progress"], site["done"] = 1.0, True
            self.sounds.append("ability")

    def _objective_step(self, dt):
        k, n = self.kind, self.params["n"]
        limit = 2 + int(self.d // 3)
        if k == "interception":
            self._spawn_wave(dt, "intruder", limit, n)
            allowed = self.params["m"]
            self.message = f"Intercept: {self.destroyed} down, {self.escaped}/{allowed} slipped past"
            if self.escaped >= allowed:
                self.outcome = False
            elif self.spawned >= n and not self.enemies:
                self.outcome = True
        elif k == "battle":
            if self.spawned < n - 1:
                self._spawn_wave(dt, "hunter", limit, n - 1, 2.5)
            elif self.spawned < n and len(self.enemies) < 2:
                self._spawn_enemy("ace")
                self.message = "The enemy ace has arrived"
            if self.spawned < n:
                self.message = f"Hostiles defeated: {self.destroyed}/{n}"
            elif not self.enemies:
                self.outcome = True
        elif k == "strike":
            self._spawn_wave(dt, "hunter", max(1, limit - 2), None, 9)
            left = sum(e.role == "ground" for e in self.enemies)
            self.message = f"Emplacements remaining: {left}"
            if not left:
                self.outcome = True
        elif k in ("defence", "airbase", "escort"):
            self._spawn_wave(dt, "hunter", max(2, limit - 1), None, 4.5)
            s = self.structure
            if s.hp <= 0:
                self.outcome = False
                self.burst(s.position, (255, 120, 60), 90, 320)
            elif k == "escort":
                s.fly(dt)
                self.message = f"Transport hull {max(0, s.hp):.0f} | crossing {s.position.x / W:.0%}"
                if s.position.x > W - 40:
                    self.outcome = True
            else:
                left = self.params["s"] - self.time
                self.message = f"Hold {max(0, left):.0f}s | installation {max(0, s.hp):.0f}"
                if left <= 0:
                    self.outcome = True
        elif k in ("reconnaissance", "investigation"):
            pending = [s for s in self.sites if not s["done"]]
            if pending:
                for s in pending:
                    self._scan(s, dt, 3.0)
            ambush = k == "investigation" and len(pending) < len(self.sites)
            self._spawn_wave(dt, "hunter", limit - 1 if ambush else max(1, limit - 2), None, 6 if ambush else 11)
            self.message = f"Sites scanned: {len(self.sites) - len(pending)}/{len(self.sites)}"
            if all(s["done"] for s in self.sites):
                self.outcome = True
        elif k == "rescue":
            beacon, home = self.sites
            self._spawn_wave(dt, "hunter", max(1, limit - 1), None, 6)
            if not beacon["done"]:
                self._scan(beacon, dt, 4.0)
                self.message = "Reach the beacon and hold for pickup"
            else:
                self._scan(home, dt, 1.0)
                self.message = "Survivors aboard. Return to the extraction point"
                self.outcome = True if home["done"] else None
        elif k == "emergency":
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = max(1.1, 2.8 - 0.18 * self.d)
                velocity = V(self.rng.uniform(-35, 35), self.rng.uniform(35, 55 + 6 * self.d))
                self.fragments.add(Fragment(self.rng.uniform(80, W - 80), -40,
                                            Fragment.MIN * self.rng.randint(1, 3), velocity, self.rng))
            goal = n * 2
            self.message = f"Fragments broken: {self.destroyed}/{goal} | ground integrity {max(0, self.structure.hp):.0f}%"
            if self.structure.hp <= 0:
                self.outcome = False
            elif self.destroyed >= goal:
                self.outcome = True

    # -- main step -----------------------------------------------------------
    def step(self, controls: Controls, dt: float):
        if self.outcome is not None:
            self._effects(dt)
            return
        self.time += dt
        self._player_step(controls, dt)
        for e in list(self.enemies):
            self._enemy_step(e, dt)
        self._wingman_step(dt)
        self.rounds.update(dt)
        self.fragments.update(dt)
        self._collisions()
        self._objective_step(dt)
        self._effects(dt)
        out_of_options = self.ammo <= 0 and self.missiles <= 0 and self.kind in ("strike", "battle", "emergency")
        if self.player.hp <= 0:
            self.outcome = False
            self.message = "Aircraft lost. The crew ejected safely."
            self.burst(self.player.position, (255, 90, 60), 80, 300)
        elif self.time >= TIME_LIMIT or (out_of_options and not self.rounds):
            self.outcome = False

    def _effects(self, dt):
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.life > 0][-600:]

    def result(self) -> dict:
        lost = (self.start_hp - max(0, self.player.hp)) / self.player.max_hp * 100
        return {"success": bool(self.outcome), "kills": self.kills, "shots": self.shots,
                "hits": min(self.hits, self.shots), "damage_taken": max(0, round(lost * 0.8)),
                "duration": round(self.time, 1),
                "fuel_used": round(self.start_fuel - self.fuel),
                "ammo_used": self.start_ammo - self.ammo}


def autopilot(sim: Sim) -> Controls:
    """A simple bot used for automated tests and the --autopilot demo."""
    p = sim.player
    goal, shoot = None, False
    pending = [s for s in sim.sites if not s["done"]]
    foes = list(sim.enemies) + list(sim.fragments)
    if pending:
        goal = pending[0]["pos"]
    elif foes:
        goal = min(foes, key=lambda e: p.position.distance_to(e.position)).position
    goal = goal if goal is not None else V(W / 2, H / 2)
    diff = angle_diff(p.rotation, bearing(p.position, goal))
    near_site = bool(pending) and p.position.distance_to(goal) < 110
    nearby = [e for e in foes if p.position.distance_to(e.position) < 450
              and abs(angle_diff(p.rotation, bearing(p.position, e.position))) < 9]
    shoot = bool(nearby)
    throttle = -1.0 if near_site or p.position.distance_to(goal) < 160 else 1.0
    return Controls(turn=max(-1.0, min(1.0, diff / 12)), throttle=throttle, fire=shoot,
                    missile=shoot and sim.rng.random() < 0.03, ability=p.hp < p.max_hp * 0.7)
