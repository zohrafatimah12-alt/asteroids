import pytest

from nebula.combat.sim import Sim, autopilot
from nebula.combat.ticket import practice_ticket
from nebula.data.campaign import levels

FIRST = {}
for m in levels():
    if m["type"] not in ("diplomacy", "intelligence", "economy", "research"):
        FIRST.setdefault(m["type"], m["level"])


def fly(level, bot=autopilot, aircraft="lm_wren"):
    sim = Sim(practice_ticket(level, aircraft))
    for _ in range(30 * 300):
        if sim.outcome is not None:
            break
        sim.step(bot(sim), 1 / 30)
    return sim


def test_there_are_ten_combat_types():
    assert len(FIRST) == 10


@pytest.mark.parametrize("kind,level", sorted(FIRST.items()))
def test_every_mission_type_reaches_a_valid_result(kind, level):
    sim = fly(level)
    assert sim.outcome is not None
    result = sim.result()
    assert 0 <= result["hits"] <= result["shots"]
    assert 0 <= result["damage_taken"] <= 100


def test_first_level_is_winnable():
    assert fly(1).outcome is True


def test_idle_pilot_fails():
    from nebula.combat.sim import Controls
    assert fly(1, bot=lambda sim: Controls()).outcome is False


def test_airframes_fly_differently():
    fast, slow = (Sim(practice_ticket(1, a)).player for a in ("fr_skua", "th_leviathan"))
    assert fast.max_speed > slow.max_speed and fast.turn_rate > slow.turn_rate


def test_renderer_draws_every_type():
    import pygame

    from nebula.combat.app import Renderer
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    view = Renderer(screen)
    for level in FIRST.values():
        sim = Sim(practice_ticket(level))
        for _ in range(240):
            sim.step(autopilot(sim), 1 / 30)
        view.draw(sim)
    pygame.quit()
