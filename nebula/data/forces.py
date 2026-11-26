"""National airframe inventories, listed in the order the aircraft appear in aircraft.py."""

from nebula.data.aircraft import AIRCRAFT

_COUNTS = {"lumeris": (1, 1, 0), "zorvania": (2, 2, 1), "thalmora": (2, 2, 2), "elyndra": (3, 3, 1), "ostraven": (2, 4, 2),
           "frostara": (3, 4, 2), "kryvos": (4, 4, 4), "aerovant": (5, 5, 2), "drakoria": (5, 5, 7),
           "varkhen": (8, 6, 6)}

INVENTORY = {country: dict(zip((k for k, a in AIRCRAFT.items() if a["country"] == country), counts))
             for country, counts in _COUNTS.items()}
