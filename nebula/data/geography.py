"""VEYRA's map as a shared-vertex mesh.

Countries are lists of vertex ids. A land border exists exactly when two
polygons share a mesh edge, so adjacency can never disagree with the drawing.
Edges are roughened deterministically from their endpoint names, which means
both neighbours receive the identical coastline or border polyline.
"""

import hashlib

WIDTH, HEIGHT = 1600, 900

VERTICES = {
    "a": (140, 200), "b": (420, 105), "c": (720, 85), "d": (1020, 115), "e": (1250, 205),
    "f": (115, 360), "g": (400, 285), "h": (700, 270), "i": (980, 295), "j": (1275, 375),
    "k": (440, 465), "l": (320, 585), "m": (125, 545), "n": (725, 425), "o": (580, 465),
    "p": (1255, 595), "q": (935, 495), "r": (620, 615), "s": (430, 640), "t": (850, 635),
    "u": (535, 785), "v": (320, 825), "w": (140, 720), "x": (805, 795), "y": (1175, 765),
    "z": (990, 830),
    # Thalmoran isles
    "A": (1390, 380), "B": (1475, 410), "C": (1455, 490), "D": (1375, 465),
    "E": (1430, 545), "F": (1525, 580), "G": (1490, 670), "H": (1400, 640),
    "I": (1360, 715), "J": (1425, 735), "K": (1390, 790),
}

SHAPES = {
    "frostara": ["abcdejihgf"],
    "drakoria": ["fgklm"],
    "aerovant": ["ghnok"],
    "varkhen": ["hijpqn"],
    "lumeris": ["korsl"],
    "elyndra": ["onqtr"],
    "ostraven": ["mlsuvw"],
    "zorvania": ["srtxu"],
    "kryvos": ["tqpyzx"],
    "thalmora": ["ABCD", "EFGH", "IJK"],
}

# kind, name, x, y
FEATURES = [
    ("mountain", "The Spine", 760, 540), ("mountain", "Emberback Range", 1080, 420),
    ("mountain", "Iron Teeth", 230, 450), ("forest", "Lantern Forest", 450, 555),
    ("forest", "Verdance", 270, 730), ("desert", "Glass Desert", 1040, 690),
    ("polar", "Aurora Shelf", 700, 170), ("forest", "Mistwood", 660, 720),
]
OCEANS = [("Pale Ocean", 1450, 270), ("Western Deep", 70, 860), ("Boreal Sea", 1360, 90),
          ("Southern Reach", 760, 875)]

# id, name, country, x, y, role
AIRBASES = [
    ("elw", "Elowen Field", "lumeris", 470, 530, "home"),
    ("cal", "Calix Reach Strip", "lumeris", 560, 590, "forward"),
    ("aet", "Aetheris Skyport", "aerovant", 590, 350, "research"),
    ("vrk", "Varkora Bastion", "varkhen", 1130, 470, "strike"),
    ("emb", "Ember Gate", "varkhen", 880, 370, "forward"),
    ("hgm", "Highmere Eyrie", "elyndra", 750, 505, "defence"),
    ("zrk", "Zorvek Array", "zorvania", 700, 680, "recon"),
    ("tha", "Thalass Harbour Wing", "thalmora", 1440, 615, "maritime"),
    ("khv", "Kharvek Longstrip", "kryvos", 1090, 610, "long-range"),
    ("isk", "Iskelle Ice Base", "frostara", 560, 195, "intercept"),
    ("nlm", "Northlamp Radar", "frostara", 960, 180, "radar"),
    ("drv", "Dravorn Works", "drakoria", 260, 400, "factory"),
    ("ost", "Ostra Treasury Field", "ostraven", 330, 700, "logistics"),
]

CAPITALS = {
    "lumeris": (500, 525), "aerovant": (560, 380), "varkhen": (1100, 440),
    "elyndra": (730, 540), "zorvania": (650, 700), "thalmora": (1435, 440),
    "kryvos": (1090, 650), "frostara": (640, 205), "drakoria": (260, 440),
    "ostraven": (300, 680),
}
_OFFSETS = [(55, 45), (-55, 30)]
# Positions of each nation's two other cities; island cities need their own isles.
CITIES = {c: [(x + dx, y + dy) for dx, dy in _OFFSETS] for c, (x, y) in CAPITALS.items()}
CITIES["thalmora"] = [(1440, 610), (1394, 742)]

TRADE_ROUTES = [
    ("lumeris", "aerovant"), ("lumeris", "elyndra"), ("ostraven", "thalmora"),
    ("ostraven", "lumeris"), ("drakoria", "varkhen"), ("kryvos", "zorvania"),
    ("aerovant", "frostara"), ("kryvos", "thalmora"),
]

# id, name, claimant, claimant, x, y
DISPUTES = [
    ("windward", "Windward Plateau", "aerovant", "varkhen", 712, 350),
    ("orun", "Orun Pass", "elyndra", "varkhen", 830, 460),
    ("saltline", "Saltline Delta", "ostraven", "zorvania", 478, 712),
    ("calix", "Calix Headwaters", "lumeris", "drakoria", 380, 525),
    ("glassrim", "Glass Rim", "kryvos", "varkhen", 1095, 545),
]

# Strategic territories: id, name, x, y, why it matters
STRATEGIC = [
    ("meridian", "Meridian Gap", 610, 468, "Crossroads of every central air corridor"),
    ("polarlens", "Polar Lens Site", 800, 190, "Best place on Veyra to study the sky"),
    ("deeprelay", "Deeprelay Atoll", 1330, 640, "Controls the ocean cable and sea lanes"),
]


def _jag(a: str, b: str, depth: int = 3) -> list[tuple[float, float]]:
    """Rough polyline from vertex a to b, identical (reversed) from b to a."""
    lo, hi = sorted((a, b))
    seed = hashlib.sha256(f"{lo}{hi}".encode()).digest()
    pts = [VERTICES[lo], VERTICES[hi]]
    n = 0
    for level in range(depth):
        out = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            off = (seed[n % len(seed)] / 255 - 0.5) * (0.24 / (1 + level * 0.35))
            n += 1
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            out += [(round(mx - (q[1] - p[1]) * off, 1), round(my + (q[0] - p[0]) * off, 1)), q]
        pts = out
    return pts if a == lo else pts[::-1]


def _edges(ring: str):
    return [(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))]


def polygons(country: str) -> list[list[tuple[float, float]]]:
    return [[p for a, b in _edges(ring) for p in _jag(a, b)[:-1]] for ring in SHAPES[country]]


def borders() -> dict[frozenset, list]:
    """{frozenset(country pair): [shared polylines]} derived from the mesh."""
    owners: dict[frozenset, list[str]] = {}
    for country, rings in SHAPES.items():
        for ring in rings:
            for a, b in _edges(ring):
                owners.setdefault(frozenset((a, b)), []).append(country)
    result: dict[frozenset, list] = {}
    for edge, who in owners.items():
        if len(who) == 2:
            result.setdefault(frozenset(who), []).append(_jag(*sorted(edge)))
    return result


def neighbours(country: str) -> list[str]:
    return sorted(next(iter(pair - {country})) for pair in borders() if country in pair)


def map_payload() -> dict:
    return {
        "width": WIDTH, "height": HEIGHT,
        "shapes": {c: polygons(c) for c in SHAPES},
        "borders": [{"countries": sorted(k), "lines": v} for k, v in borders().items()],
        "capitals": CAPITALS, "features": FEATURES, "oceans": OCEANS, "airbases": AIRBASES,
        "trade_routes": TRADE_ROUTES, "disputes": DISPUTES, "strategic": STRATEGIC,
        "cities": CITIES,
    }
