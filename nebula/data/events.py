"""Living-world event templates. {a}/{b} are countries chosen at runtime.

effects keys: rel (a-b relation), trust (player trust with a), credits, materials,
fuel, research, threat (public threat awareness), weather.
"""

EVENTS = [
    ("political", "Election upset in {a}", "A new bloc takes power and reviews foreign policy.", {"trust": -4}),
    ("political", "{a} opens a cultural exchange", "Students and pilots from {home} are invited.", {"trust": 5}),
    ("border", "Border incident: {a} and {b}", "Patrol aircraft locked radar across the frontier.", {"rel": -10}),
    ("border", "{a} and {b} reopen a crossing", "Families cross for the first time in years.", {"rel": 8}),
    ("economy", "Market shock in {a}", "Prices spike and {home}'s trade income suffers.", {"credits": -60}),
    ("economy", "Trade boom through {a}", "New contracts reach {home}'s workshops.", {"credits": 90}),
    ("science", "Breakthrough shared by {a}", "A paper from {a} accelerates {home}'s research.", {"research": 25}),
    ("aviation", "{a} unveils a new engine", "Test flights hint at a jump in performance.", {"research": 10}),
    ("diplomatic", "{a} and {b} sign a protocol", "A modest agreement lowers tension.", {"rel": 12}),
    ("military", "{a} stages exercises near {b}", "{b} protests the scale of the drills.", {"rel": -8}),
    ("intelligence", "Intercepted traffic from {a}", "Analysts recover a fragment of order of battle.", {"intel": 1}),
    ("weather", "Storm front over {a}", "Flights through the region face poor visibility.", {"weather": "storm"}),
    ("disaster", "Earthquake in {a}", "Relief flights drain shared fuel reserves.", {"fuel": -40, "trust": 3}),
    ("threat", "Unexplained fire in the sky over {a}", "A fragment burns up. Observatories disagree on its origin.", {"threat": 4}),
]
