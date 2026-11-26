"""Joint air-command treaty terms. Each option: (id, label, burden on the partner)."""

TERMS = {
    "aircraft": ("Aircraft contribution", [("20", "A fifth of their air force", 10), ("30", "Three tenths", 18), ("40", "Two fifths", 28)]),
    "supplies": ("Shared fuel and ammunition", [("none", "None", 0), ("modest", "Modest supply", 6), ("large", "Large supply", 15)]),
    "intelligence": ("Intelligence sharing", [("none", "None", 0), ("limited", "Limited", 5), ("full", "Full", 14)]),
    "bases": ("Base access", [("none", "None", 0), ("selected", "Selected bases", 6), ("wide", "Wide access", 16)]),
    "command": ("Joint command authority", [("consultative", "Consultative", 0), ("joint", "Joint staff", 8), ("lumeris", "Lumeris decides", 24)]),
    "rules": ("Operational rules", [("defensive", "Defence, escort and relief only", 0), ("all", "Any mission", 14)]),
    "technology": ("Technology cooperation", [("none", "None", 0), ("shared", "Shared both ways", -4)]),
    "training": ("Training standards", [("partner", "Each keeps its own", 0), ("shared", "Common standard", -3)]),
    "defence": ("Mutual defence", [("none", "No commitment", 6), ("mutual", "Lumeris also defends them", -8)]),
    "duration": ("Duration", [("60", "60 days", 0), ("150", "150 days", 5), ("open", "No end date", 12)]),
    "withdrawal": ("Withdrawal", [("notice", "May leave if terms are broken", -6), ("none", "No right to leave", 14)]),
}
DEFAULT = {"aircraft": "30", "supplies": "modest", "intelligence": "limited", "bases": "selected",
           "command": "joint", "rules": "defensive", "technology": "shared", "training": "partner",
           "defence": "mutual", "duration": "150", "withdrawal": "notice"}

# The term each nation weighs double, and who voices objections to which terms.
PRIORITY = {"zorvania": "intelligence", "thalmora": "bases", "elyndra": "rules", "ostraven": "supplies",
            "frostara": "defence", "kryvos": "duration", "aerovant": "technology",
            "drakoria": "aircraft", "varkhen": "command"}
AIR_TERMS = ("aircraft", "rules", "training", "supplies", "bases")
OBJECTIONS = {
    "aircraft": "That is too many of my aircraft. My own skies still need defending.",
    "supplies": "Our stores cannot carry that level of supply.",
    "intelligence": "We will not open our files that far.",
    "bases": "Foreign aircraft will not have that much access to our fields.",
    "command": "Our people elected, or at least accepted, their own command. It does not pass to Elowen.",
    "rules": "My crews will not be sent on any mission you choose.",
    "technology": "Without a fair exchange of technology, we gain too little.",
    "training": "Training must respect how our crews fly.",
    "defence": "If we stand with you, you must stand with us.",
    "duration": "We will not sign away so many days.",
    "withdrawal": "No sovereign nation signs a treaty it cannot leave.",
}
DEFENSIVE_TYPES = ("defence", "airbase", "escort", "rescue", "emergency", "reconnaissance", "investigation")
