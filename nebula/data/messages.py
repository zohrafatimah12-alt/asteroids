"""Written conversations. Each reply has different effects and its own follow-up.

Reply effects: relation/trust (with the sender's nation), reputation, resources.
A message appears when `after` (message id, reply id or None) or `level` is met.
"""


def _r(key, text, response, cost=None, **effects):
    return {"id": key, "text": text, "response": response, "cost": cost or {}, "effects": effects}


MESSAGES = [
    {"id": "welcome", "from": "lu_pres", "network": "military", "priority": "high",
     "subject": "Your first morning", "body": "Commander, the Council gave you a thin air force and a restless border. Tell me where you will start.",
     "replies": [
         _r("crews", "With the crews. I want them ready.", "Then Commander Quenby will have your support. And mine.", reputation=1, materials=30),
         _r("facts", "With the facts. I need to know what is out there.", "Wise. Director Vane will open the signals room.", research=20),
         _r("neighbours", "With our neighbours. We cannot stand alone.", "Neris will be pleased. I am too.", reputation=3)]},
    {"id": "envoy", "from": "zv_head", "network": "diplomatic", "priority": "urgent",
     "subject": "Regarding the south-eastern corridor",
     "body": "Commander. Our survey aircraft will continue near Calix Reach. We would regret any misunderstanding. How do you intend to receive them?",
     "replies": [
         _r("talk", "Share your flight plans and we will not treat them as hostile.", "A reasonable request. I will consider what we can share.", relation=14, trust=14),
         _r("firm", "Unannounced aircraft will be intercepted.", "Clear, at least. Our crews will be told.", relation=-6, trust=5, reputation=2),
         _r("gift", "Send an envoy. We will cover the costs of a joint hotline.", "Unexpected. A hotline would serve us both.", {"credits": 100}, relation=20, trust=18, reputation=2)]},
    {"id": "envoy_talk", "from": "zv_head", "network": "diplomatic", "priority": "normal", "after": ("envoy", "talk"),
     "subject": "A partial flight plan", "body": "I attach tomorrow's routes. Not all of them. Trust is built in instalments.",
     "replies": [_r("thank", "Received. We will honour them.", "Then we may speak again.", relation=4, trust=4),
                 _r("verify", "We will verify these ourselves.", "In your place, so would I.", trust=2, research=10)]},
    {"id": "envoy_firm", "from": "zv_air", "network": "personal", "priority": "high", "after": ("envoy", "firm"),
     "subject": "Between aviators", "body": "Marshal Nahl here. I did not order these flights close to your towns. If your pilots fire first, I cannot hold mine back.",
     "replies": [_r("restraint", "We fire only if fired upon.", "Then we understand each other.", relation=6, trust=8),
                 _r("warn", "Keep your aircraft out and no one fires.", "I will pass that upward.", relation=-3, reputation=1)]},
    {"id": "envoy_gift", "from": "lu_dip", "network": "diplomatic", "priority": "normal", "after": ("envoy", "gift"),
     "subject": "The hotline is live", "body": "Zorvek accepted. If you want a peace treaty, this is the best moment we will get.",
     "replies": [_r("good", "Good work. Keep the channel open.", "I will.", relation=3, trust=3)]},
    {"id": "readiness", "from": "lu_air", "network": "military", "priority": "high",
     "subject": "Readiness before launch",
     "body": "Two airframes, one tired ground crew. I can run a full readiness drill now, or save the supplies. Your call, but I will remember if my pilots go up short.",
     "replies": [
         _r("drill", "Run the drill.", "Thank you. The crews noticed.", {"materials": 40}, reputation=2, research=10),
         _r("save", "Save the supplies for repairs.", "Understood. I will make do.", materials=10)]},
    {"id": "intercept", "from": "lu_intel", "network": "intelligence", "priority": "urgent", "after": ("welcome", None),
     "subject": "Intercept: reliability unconfirmed",
     "body": "We caught a fragment suggesting Zorvania is preparing an operation. One source, and I do not fully trust it. Do I act on it?",
     "replies": [
         _r("check", "Corroborate it first.", "Good. A second source takes money, not guesses.", {"credits": 40}, intel=0.35),
         _r("brief", "Warn the border towns now.", "Done. If this is false, we have spent some credibility.", reputation=-1, relation=-3)]},
    {"id": "aero", "from": "ae_head", "network": "diplomatic", "priority": "normal", "level": 1,
     "subject": "We watched your sortie", "body": "Lumeris held its sky. Aerovant would like to know what kind of neighbour you intend to be.",
     "replies": [_r("science", "A research partner.", "Then Aetheris has a seat for your scientists.", relation=8, trust=6, research=20),
                 _r("defence", "One that can defend itself.", "A fair answer. We respect it.", trust=3, materials=30)]},
]
