"""Original characters. `private` motives are never sent to the client."""

# id, country, role, name, personality, public goal, private motive
_ROWS = [
    ("lu_pres", "lumeris", "President", "Isaveth Orrin", "measured, humane", "Keep Lumeris free without a war", "Fears the Council will not survive one defeat"),
    ("lu_def", "lumeris", "Defence Minister", "Corvan Aldery", "cautious, exact", "Rebuild the defences", "Wants the budget the observatories get"),
    ("lu_army", "lumeris", "Army Commander", "Brannoc Teale", "blunt, loyal", "Hold the valleys", "Distrusts reliance on aircraft"),
    ("lu_air", "lumeris", "Air Force Commander", "Maelis Quenby", "dry, protective of crews", "Bring every pilot home", "Lost a wing in the last border patrol"),
    ("lu_intel", "lumeris", "Intelligence Director", "Sorrel Vane", "guarded, sceptical", "See threats early", "Doubts one of their own sources"),
    ("lu_sci", "lumeris", "Chief Scientist", "Dr. Ilo Ferran", "curious, restless", "Reopen the observatories", "Has seen something in old sky plates"),
    ("lu_dip", "lumeris", "Chief Diplomat", "Neris Calloway", "patient, warm", "Make partners of neighbours", "Kept a back channel to Zorvek"),
    ("lu_econ", "lumeris", "Economic Strategist", "Tamsin Roe", "practical, wry", "Keep the treasury solvent", "Expects a fuel shortage"),
    ("lu_officer", "lumeris", "Senior Officer", "Col. Hadric Mune", "old-school, steady", "Train the new commander", "Wanted your post"),
    ("lu_civic", "lumeris", "Civilian Representative", "Wenna Pike", "direct, anxious", "Protect border towns", "Family farms near Calix Reach"),
    ("zv_head", "zorvania", "Chancellor", "Evander Sule", "courteous, opaque", "Secure the south-eastern frontier", "Is hiding what Zorvanian telescopes found"),
    ("zv_def", "zorvania", "Defence Minister", "Ossa Virell", "calculating", "Deterrence through knowledge", "Wants Lumeris' sky archive"),
    ("zv_air", "zorvania", "Air Force Commander", "Marshal Teodric Nahl", "precise, proud", "Control the listening corridor", "Disagrees with the drone flights"),
    ("ae_head", "aerovant", "First Engineer", "Liora Castellane", "idealistic, brisk", "Open skies for research", "Needs a partner against Varkhen"),
    ("vk_head", "varkhen", "Marshal", "Dravek Hollin", "forceful, formal", "No nation starves again", "Knows the fuel reserves are failing"),
    ("el_head", "elyndra", "Speaker of the Passes", "Anwe Torrask", "principled", "Honour shelter law", "Cannot afford a war"),
    ("th_head", "thalmora", "Tide Arbiter", "Kaiara Moen", "even-handed", "Keep sea lanes open", "Reefs are failing"),
    ("kr_head", "kryvos", "First of the Houses", "Zahir Quellan", "shrewd, generous", "Honour water debts", "The Houses are divided"),
    ("fr_head", "frostara", "Senior Warden", "Sigrun Alvessen", "grave, direct", "Leave nobody outside", "The archive frightens her"),
    ("dr_head", "drakoria", "Syndic-General", "Borin Mastrel", "gruff, honest", "Keep the foundries lit", "Labour unrest is worse than reported"),
    ("os_head", "ostraven", "Doge of Accounts", "Celandine Voss", "charming, transactional", "Trade over conflict", "Has bought secrets from both sides"),
    ("th_air", "thalmora", "Air Force Commander", "Commodore Rua Silvane", "calm, exacting", "Cover the sea lanes", "Short of spare engines"),
    ("el_air", "elyndra", "Air Force Commander", "Warden-General Petra Ilvash", "protective, stubborn", "Never fly an offensive war", "Her pilots are ageing"),
    ("os_air", "ostraven", "Air Force Commander", "Air Comptroller Dario Venn", "polished, careful", "Keep losses affordable", "Pilots are underpaid"),
    ("fr_air", "frostara", "Air Force Commander", "Flight Warden Eirik Solne", "quiet, fearless", "Bring every crew home", "Lost a brother on patrol"),
    ("kr_air", "kryvos", "Air Force Commander", "Long-Captain Nadira Hosh", "patient, sharp", "Protect the long routes", "Answers to rival Houses"),
    ("ae_air", "aerovant", "Air Force Commander", "Wing Director Casimir Vell", "analytical", "Prove the new designs", "Fears espionage"),
    ("dr_air", "drakoria", "Air Force Commander", "Forgemaster Hedda Krull", "gruff, fair", "Waste no airframe", "Production is behind"),
    ("vk_air", "varkhen", "Air Force Commander", "Strike General Ruvan Kesh", "proud, disciplined", "Keep Varkhen unbeaten", "Doubts the Marshal"),
]
_RESIDENTS = {"aerovant": "Mira Tolland", "varkhen": "Osk Veremin", "elyndra": "Hanne Corvel", "zorvania": "Pell Sarrow",
              "thalmora": "Noa Brisk", "kryvos": "Samir Adelane", "frostara": "Ylva Torn", "drakoria": "Gunnar Hesk",
              "ostraven": "Lucan Ferre"}
_ROWS += [(f"civ_{c}", c, "Civilian Representative", n, "worried, plain-spoken", "Keep families safe",
           "Has relatives across the border") for c, n in _RESIDENTS.items()]
CHARACTERS = {r[0]: dict(zip(("id", "country", "role", "name", "personality", "goal", "private"), r)) for r in _ROWS}


def public(cid: str) -> dict:
    return {k: v for k, v in CHARACTERS[cid].items() if k != "private"}


LEADERS = {c["country"]: i for i, c in reversed(list(CHARACTERS.items()))}
CIVILIANS = {c["country"]: i for i, c in CHARACTERS.items() if c["role"] == "Civilian Representative"}
AIR_CHIEFS = {c["country"]: i for i, c in CHARACTERS.items() if c["role"] == "Air Force Commander"}
