"""The 100-level campaign. One line per level: Title | type | story.

Stages 1-9 face nations from national rank 9 up to rank 1; stage 10 is the global crisis.
Everything else (difficulty, rewards, objectives, consequences) is derived by
rules in nebula.core.missions so that balancing lives in one place.
"""

CHAPTERS = [
    ("zorvania", "The Eastern Corridor", """
First Watch|interception|Zorvanian survey drones are crossing the south-eastern border toward Calix Reach. Zorvek calls them research flights. The Skywatch has little to stop them with.
Eyes on the Reach|reconnaissance|Map the damaged strips around Calix Reach before the rains.
Relief Run|escort|A medical transport must reach Marrowfen through a corridor the Zorvanian drones keep crossing.
The Corridor Question|diplomacy|Zorvania claims survey rights over the south-eastern corridor. The Council asks you to carry an answer.
Lights Over the Fen|investigation|Farmers report falling lights. The old astronomers' notes predict nothing there.
Hold the Strip|airbase|Aircraft with no markings target Calix Reach, Lumeris' only forward airstrip. Zorvek denies them.
A Budget for the Sky|economy|Spend scarce funds: repair the airbase, or reopen the observatory.
Beacon in the Hills|rescue|A survey crew is down in the lantern forest with a storm closing in.
The Glass Sample|research|The fallen fragment is warmer than it should be, and older than Veyra.
The Skywatch Stands|battle|Zorvania's corridor wing arrives in strength. Lumeris must prove it can defend itself.
"""),
    ("thalmora", "Open Harbours", """
Harbour Court|diplomacy|The Commonwealth arbitrates sea disputes. Ask it to host all ten.
Storm Patrol|emergency|Unexplained sky-stones raise waves; clear the air above the harbour lanes.
Lost Fleet Beacon|rescue|A research vessel sends a fading signal.
Deeprelay Watch|airbase|Defend Deeprelay Atoll and the world's cable.
Sea Lane Guard|escort|Escort deuterium tankers, fuel for something larger than war.
Under the Crater|investigation|An ocean impact left a pattern on the seabed.
Tide Treaty|diplomacy|Settle fishing and fuel rights to keep the sea lanes shared.
Pirate Skies|interception|Mercenaries prey on relief flights.
Reactor Water|research|Thalmoran heavy water behaves strangely beside the glass sample. Measure why.
Breakwater|battle|A fleet of hijacked drones converges on Thalass.
"""),
    ("elyndra", "The Passes", """
The Law of Shelter|diplomacy|Elyndra receives you as a traveller. Earn the right to stay as a partner.
Through Orun Pass|escort|Guide civilian haulers through the narrow pass.
Echo Valleys|reconnaissance|Chart the radar shadows of the Spine.
Avalanche Season|emergency|A quake buries towns; falling debris threatens the relief corridor.
Shots at Orun|defence|Hold the Elyndran relay while both claimants mass at the pass.
Who Fired First|investigation|Gather flight evidence on the Orun incident.
The Mountain Accord|diplomacy|Offer Elyndra and Varkhen a way to step back from Orun.
Eyrie Alarm|interception|Night intruders approach Highmere.
Crystal for the Lens|economy|The deep-sky lens needs Elyndran crystal. Decide what Lumeris will pay.
The Pass Holds|battle|An armoured air column forces the passes.
"""),
    ("ostraven", "The Merchant Sky", """
Contracts Are Sung|diplomacy|The Merchant Republic will talk, if you can say what Lumeris brings to market.
Goldmouth Convoy|escort|Escort a grain convoy that Ostran underwriters refuse to insure.
The Bought Secret|intelligence|Ostraven has sold the same intelligence twice. Find out who else holds it.
Delta Watch|reconnaissance|Chart the flood channels where unregistered aircraft are landing.
Treasury Intercept|interception|Treasury Guard pilots under private contract challenge your flight.
Vault Shield|airbase|Mercenaries strike Ostra Treasury Field while its owners argue over the fee.
The Price of Grain|economy|A shortage is coming. Decide what Lumeris will pay to steady the markets.
Smuggler Lanes|investigation|Isotope shipments vanish between Veyle and the sea.
Hostile Tender|defence|Hold the exchange relay against a faction trying to buy the war it wants.
Ledger of Wings|battle|The contracted squadrons make their final bid for the southern sky.
"""),
    ("frostara", "The Polar Record", """
The Wardens' Archive|intelligence|Four hundred years of sky logs reveal the object's true course.
Whiteout Rescue|rescue|Find a warden team under the aurora.
Boreal Scramble|interception|Intercept bombers using the polar night as cover.
The Countdown|research|Calculate the day the Shard-Star reaches Veyra.
Telling the World|diplomacy|Decide how the nations learn the truth.
Ice Lens Defence|defence|Panic breeds sabotage. Protect the Polar Lens.
First Rain|emergency|The leading fragments arrive. Shoot them apart before they land.
Signal from the Dark|investigation|The fragments carry a regular pulse. Learn what it means.
Shelter Law|diplomacy|Frostara asks every nation to swear nobody is left outside.
Under the Aurora|battle|A faction that wants the shelters for itself assaults Iskelle.
"""),
    ("kryvos", "Long Wings", """
Water Debt|diplomacy|The Oasis Houses help those who help them first.
Glass Horizon|reconnaissance|Survey an impact field that turned sand to mirror.
Caravan of the Sky|escort|Move solar cells across the open desert.
Dust and Fire|emergency|A fragment swarm falls over Mirrorwell.
Glass Rim|diplomacy|Kryvos and Varkhen both claim the rim. Find terms that last.
Mirage Hunters|interception|Fast raiders ride the heat shimmer.
Launch Valley|research|The canyon could host a launch rail. Test the numbers.
Longstrip Siege|airbase|Isolationists attack Kharvek to stop the programme.
Rations of the Future|economy|Decide how water and lithium are shared among allies.
The Endless Flight|defence|Keep the high-altitude tanker alive on its record flight.
"""),
    ("aerovant", "Borrowed Wings", """
Invitation to Aetheris|diplomacy|Aerovant will share engineering, if Lumeris can show why it matters.
Windward Patrol|defence|Guard an Aerovant research platform over the disputed plateau.
Prototype Down|rescue|A test pilot ejects over contested ground.
The Quiet Thief|intelligence|Design files are leaking. Find the source before blame lands on Varkhen.
Plateau Intercept|interception|An Aerovant test wing disputes your right to the Windward line.
Joint Laboratory|research|Aerovant and Lumeris scientists compare fragment samples.
Convoy of Instruments|escort|Move the great lens components to the Polar Lens Site.
Line on the Map|diplomacy|Broker a flight corridor across the Windward Plateau.
High Thin Air|reconnaissance|Photograph the debris trail from the edge of the stratosphere.
Skyport Under Fire|airbase|A rogue wing attacks Aetheris to bury the research.
"""),
    ("drakoria", "The Forge", """
The Senate of Smoke|diplomacy|Only Drakoria's foundries can build at planetary scale.
Foundry Strike|economy|Workers down tools. Choose how the great build is staffed.
Titanium Road|escort|Protect the ore trains of the sky.
Saboteurs Above|interception|Stop raiders targeting the assembly yards.
Two Blueprints|research|Shield lattice or evacuation ark: set the engineers' priority.
Works Under Siege|airbase|Defend Dravorn Works.
Stress Test|reconnaissance|Inspect the first orbital segments.
Meltdown Sky|emergency|Fragments hit the furnaces; clear the air.
The Headwaters Return|diplomacy|Close the oldest wound between Lumeris and Drakoria.
Iron Sunrise|battle|Hardliners seize heavy aircraft to claim the first launch.
"""),
    ("varkhen", "Iron Oaths", """
Words with the Marshal|diplomacy|Varkhen agrees to listen. Strength is the only introduction it respects.
Ember Gate Shadow|reconnaissance|Count the aircraft gathering at Ember Gate.
Defectors' Flight|escort|Escort engineers who carry proof of a coming offensive.
The War Ledger|intelligence|Learn why Varkhen is stockpiling fuel: conquest, or fear.
Broken Formation|interception|A splinter wing launches without orders.
Steel Port Fire|emergency|Burning wreckage rains over Kharsund. Help a rival nation.
The Marshal's Dilemma|diplomacy|Show the Directorate the sky data. Ask for an end to mobilisation.
Strike the Silo Line|strike|Hardliners arm a doomsday battery. Destroy its launchers.
Oath of the Ace|battle|The Redfang champion challenges you above the basalt uplands.
Standing Down|diplomacy|Negotiate what Varkhen's air force will do instead of war.
"""),
    ("ostraven", "Global Crisis", """
What Survival Costs|economy|Ostraven holds the isotopes. Everyone must give something up.
Convoy of Ten Flags|escort|The final cargo flies under every flag willing to join.
The Last Market Day|diplomacy|The Merchant Republic votes on opening its vaults.
Delta Evacuation|rescue|Floods trap families in the delta.
Sky of Stones|emergency|The second swarm darkens the southern sky.
The Final Council|diplomacy|Call the nations of Veyra to one table.
Launch Window|defence|Hold the launch corridor.
Hands on the Switch|research|Integrate everything Veyra has learned.
Shatterfront|battle|The densest wave arrives. Whatever alliance you built flies with you.
NEBULA|battle|The Shard-Star fills the sky. Beyond it, Nebula still shines.
"""),
]


# Shorter briefings used when the player commands a nation other than Lumeris.
TEMPLATES = {
    "interception": ("Contact", "{foe} aircraft cross toward {place}. Turn them back."),
    "escort": ("Safe Passage", "Bring a transport through contested skies near {place}."),
    "reconnaissance": ("Long Look", "Survey the approaches to {place}."),
    "defence": ("The Line", "Hold a relay station near {place}."),
    "rescue": ("Beacon", "A crew is down near {place}. Bring them home."),
    "strike": ("Silent Guns", "Disable hostile emplacements near {place}."),
    "airbase": ("Home Strip", "An airbase near {place} is under attack."),
    "investigation": ("Cold Trail", "Something unexplained is moving near {place}."),
    "emergency": ("Falling Sky", "Debris is falling toward {place}. Break it apart."),
    "battle": ("Proving Day", "{foe}'s main wing takes the field near {place}."),
    "diplomacy": ("The Table", "{foe} agrees to talk. Choose how {home} answers."),
    "intelligence": ("Hidden File", "{foe} knows something {home} needs."),
    "economy": ("The Price", "Decide what {home} will spend on this relationship."),
    "research": ("Shared Sky", "New observations need a research choice."),
}


def levels() -> list[dict]:
    result = []
    for ci, (country, chapter, block) in enumerate(CHAPTERS):
        for line in block.strip().splitlines():
            title, kind, story = line.split("|")
            result.append({"level": len(result) + 1, "chapter": ci + 1, "chapter_title": chapter,
                           "country": country, "title": title, "type": kind, "story": story})
    return result
