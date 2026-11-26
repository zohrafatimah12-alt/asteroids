"""Thirty original airframes, three per air force."""

# id, name, country, category, speed, agility, armour, radar, range, ammo, ability, cost, silhouette
_ROWS = [
    ("lm_wren", "LW-2 Wren", "lumeris", "fighter", 46, 62, 34, 30, 40, 220, "patch", 120, "delta"),
    ("lm_lantern", "LR-5 Lantern", "lumeris", "reconnaissance", 50, 48, 26, 58, 62, 120, "deepscan", 150, "glider"),
    ("lm_dawn", "LX-9 Dawnspire", "lumeris", "fighter", 76, 80, 55, 70, 60, 320, "pulse", 520, "arrow"),
    ("ae_zephyr", "Zephyr VII", "aerovant", "fighter", 80, 86, 44, 68, 55, 300, "surge", 430, "arrow"),
    ("ae_halcyon", "Halcyon", "aerovant", "reconnaissance", 74, 60, 32, 90, 78, 130, "deepscan", 380, "glider"),
    ("ae_atlas", "Skyframe Atlas", "aerovant", "support", 48, 36, 70, 72, 84, 180, "patch", 360, "heavy"),
    ("vk_fang", "VK-44 Redfang", "varkhen", "fighter", 78, 70, 62, 55, 52, 420, "salvo", 470, "delta"),
    ("vk_maul", "Warmaul", "varkhen", "bomber", 52, 30, 84, 46, 70, 380, "ironhull", 520, "heavy"),
    ("vk_lance", "Cinder Lance", "varkhen", "interceptor", 90, 54, 40, 60, 44, 260, "surge", 440, "needle"),
    ("el_ibex", "Ibex Guard", "elyndra", "interceptor", 68, 82, 66, 58, 38, 280, "ironhull", 360, "delta"),
    ("el_lammer", "Lammergeier", "elyndra", "fighter", 62, 88, 56, 52, 44, 300, "chaff", 340, "arrow"),
    ("el_bastion", "Bastion Kite", "elyndra", "support", 44, 50, 78, 66, 50, 200, "patch", 320, "heavy"),
    ("zv_shade", "Shade-3", "zorvania", "reconnaissance", 82, 72, 28, 94, 66, 150, "veil", 480, "glider"),
    ("zv_whisper", "Whisper", "zorvania", "interceptor", 84, 76, 36, 76, 48, 220, "veil", 450, "needle"),
    ("zv_murmur", "Murmur Relay", "zorvania", "support", 52, 40, 48, 96, 72, 100, "pulse", 330, "heavy"),
    ("th_petrel", "Petrel", "thalmora", "fighter", 64, 74, 50, 62, 76, 280, "chaff", 330, "delta"),
    ("th_tern", "Tideglass Tern", "thalmora", "reconnaissance", 60, 62, 40, 80, 88, 140, "deepscan", 300, "glider"),
    ("th_leviathan", "Leviathan Boat", "thalmora", "heavy", 40, 24, 90, 64, 94, 360, "patch", 420, "heavy"),
    ("kr_sirocco", "Sirocco", "kryvos", "fighter", 72, 66, 48, 54, 82, 300, "salvo", 360, "delta"),
    ("kr_sunreach", "Sunreach", "kryvos", "bomber", 58, 34, 66, 58, 98, 340, "ironhull", 450, "heavy"),
    ("kr_mirage", "Mirage Courser", "kryvos", "interceptor", 86, 64, 34, 56, 70, 240, "veil", 400, "needle"),
    ("fr_skua", "Skua Interceptor", "frostara", "interceptor", 92, 68, 46, 74, 46, 260, "surge", 440, "needle"),
    ("fr_aurora", "Aurora Warden", "frostara", "fighter", 70, 70, 64, 72, 58, 300, "chaff", 390, "arrow"),
    ("fr_icebreak", "Icebreaker", "frostara", "heavy", 46, 28, 88, 68, 80, 300, "patch", 380, "heavy"),
    ("dr_anvil", "Anvil Mk-IX", "drakoria", "heavy", 50, 32, 96, 50, 66, 440, "ironhull", 500, "heavy"),
    ("dr_hammer", "Foundry Hammer", "drakoria", "bomber", 56, 36, 82, 48, 72, 400, "salvo", 480, "heavy"),
    ("dr_rivet", "Rivet", "drakoria", "fighter", 66, 58, 72, 52, 50, 360, "salvo", 330, "delta"),
    ("os_ledger", "Goldmouth Ledger", "ostraven", "support", 54, 46, 60, 70, 86, 160, "patch", 300, "heavy"),
    ("os_corsair", "Delta Corsair", "ostraven", "fighter", 74, 72, 54, 60, 62, 300, "chaff", 390, "arrow"),
    ("os_vault", "Vaultwing", "ostraven", "bomber", 60, 40, 74, 62, 78, 320, "ironhull", 430, "heavy"),
]
_FIELDS = "id name country category speed agility armour radar range ammo ability cost silhouette".split()

AIRCRAFT = {row[0]: dict(zip(_FIELDS, row)) for row in _ROWS}

ABILITIES = {
    "surge": "Overdrive: a short burst of extreme speed",
    "chaff": "Chaff cloud: destroys nearby incoming fire",
    "veil": "Signal veil: enemies lose track of you",
    "pulse": "EMP pulse: stuns nearby hostiles",
    "patch": "Field repair: restores part of the hull",
    "salvo": "Salvo: a wide fan of shells",
    "deepscan": "Deep scan: completes scans much faster",
    "ironhull": "Hardened hull: briefly cuts damage taken",
}

# key: (label, stat boosted, bonus per tier, max tier)
UPGRADES = {
    "engine": ("Engine tuning", "speed", 5, 3),
    "controls": ("Flight controls", "agility", 5, 3),
    "plating": ("Composite plating", "armour", 6, 3),
    "sensors": ("Sensor suite", "radar", 6, 3),
    "tanks": ("Extended tanks", "range", 6, 3),
    "magazine": ("Expanded magazine", "ammo", 40, 3),
}
