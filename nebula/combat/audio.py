"""Synthesised sound effects (no asset files, no numpy). Silent if no audio device."""

import array
import math
import random

import pygame

RATE = 22050
# name: (start Hz, end Hz, seconds, noise mix, volume)
_SPEC = {
    "gun": (420, 160, 0.06, 0.5, 0.12), "missile": (200, 900, 0.3, 0.4, 0.2),
    "boom": (140, 40, 0.45, 0.8, 0.3), "hit": (160, 90, 0.12, 0.6, 0.25),
    "ability": (500, 1200, 0.25, 0.0, 0.18), "win": (440, 880, 0.7, 0.0, 0.2),
    "lose": (330, 110, 0.8, 0.1, 0.2),
}


class Audio:
    def __init__(self, enabled: bool = True):
        self.sounds = {}
        if not enabled:
            return
        try:
            pygame.mixer.init(RATE, -16, 1, 512)
            channels = pygame.mixer.get_init()[2]
            for name, spec in _SPEC.items():
                self.sounds[name] = pygame.mixer.Sound(buffer=self._synth(spec, channels))
        except pygame.error:
            self.sounds = {}

    @staticmethod
    def _synth(spec, channels):
        start, end, seconds, noise, volume = spec
        rng, phase, data = random.Random(start), 0.0, array.array("h")
        total = int(RATE * seconds)
        for i in range(total):
            t = i / total
            phase += 2 * math.pi * (start + (end - start) * t) / RATE
            wave = (1 - noise) * math.sin(phase) + noise * rng.uniform(-1, 1)
            data.extend([int(wave * volume * (1 - t) * 32767)] * channels)
        return data.tobytes()

    def play(self, name: str):
        if name in self.sounds:
            self.sounds[name].play()
