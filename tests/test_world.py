from nebula.data import geography as geo
from nebula.data.aircraft import ABILITIES, AIRCRAFT
from nebula.data.campaign import levels
from nebula.data.countries import COUNTRIES


def inside(point, polygon):
    x, y = point
    hit = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) / (by - ay) * (bx - ax):
            hit = not hit
    return hit


def test_adjacency_is_symmetric_and_island_has_no_land_border():
    for c in COUNTRIES:
        for other in geo.neighbours(c):
            assert c in geo.neighbours(other)
    assert geo.neighbours("thalmora") == []


def test_every_border_polyline_is_in_both_polygons():
    for pair, lines in geo.borders().items():
        for country in pair:
            points = {p for poly in geo.polygons(country) for p in poly}
            assert all(set(line) <= points for line in lines)


def test_capitals_cities_and_airbases_are_inside_their_country():
    for country, (x, y) in geo.CAPITALS.items():
        spots = [(x, y), *geo.CITIES[country]]
        for spot in spots:
            assert any(inside(spot, p) for p in geo.polygons(country)), (country, spot)
    for base in geo.AIRBASES:
        assert any(inside((base[3], base[4]), p) for p in geo.polygons(base[2])), base[1]


def test_land_disputes_are_between_neighbours():
    for d in geo.DISPUTES:
        assert d[3] in geo.neighbours(d[2]), d[1]


def test_roster():
    assert len(COUNTRIES) == 10
    for c in COUNTRIES:
        assert sum(a["country"] == c for a in AIRCRAFT.values()) == 3
    assert {a["category"] for a in AIRCRAFT.values()} == {
        "fighter", "interceptor", "reconnaissance", "bomber", "heavy", "support"}
    assert {a["ability"] for a in AIRCRAFT.values()} <= set(ABILITIES)
    stats = [tuple(a[k] for k in ("speed", "agility", "armour", "radar", "range")) for a in AIRCRAFT.values()]
    assert len(set(stats)) == len(stats)


def test_campaign_shape():
    data = levels()
    assert [m["level"] for m in data] == list(range(1, 101))
    assert len({m["title"] for m in data}) == 100
    for chapter in range(10):
        assert len({m["country"] for m in data[chapter * 10:chapter * 10 + 10]}) == 1
