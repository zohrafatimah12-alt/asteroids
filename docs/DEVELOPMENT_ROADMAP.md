# Roadmap and known limitations

## Limitations today
- **Joint ranking:** the competitive rank is stage progression, not a strength ordering, so strength numbers on the ladder need not follow rank order. A later withdrawal or expiry lowers actual strength but keeps the earned place. National military scores are fixed data; nothing in play changes them yet.
- **Treaties:** proposals are menu choices with templated objections; the player cannot write a custom counter. Command authority changes only acceptance. Aircraft basing locations, weapons stocks and army cooperation are not modelled. "Ammunition" supply is delivered as materials.
- **Peaceful routes** exist for Level 1 and for interception, strike and major-battle levels against a stage opponent.
- **Old saves:** campaigns started before the stage reorder keep their completed level numbers, which now refer to different missions. Start a new campaign.
- **Characters:** 21 exist (10 Lumeris, 3 Zorvania, one leader for each other nation). There are 8 messages, mostly early-game. Later conversations do not yet recall past choices; the philosophy changes starting values, intro reactions and adviser advice, not later dialogue or briefings.
- **Not built:** International Council, news network, army screen, weapons and bombs inventory, misinformation, achievements, combat restart.
- **Wing sorties** do not track enemy or wingman losses or ammunition detail; defensive patrol only affects flown sorties.
- **Not yet play-tested by a person.** Combat balance was checked only with a simple autopilot. It completed all ten mission types at low levels and lost several high-level defence, airbase and battle missions with un-upgraded aircraft.
- **Browser clicking is not covered by tests.** Screens were rendered in headless Chrome without script errors; actions are tested through the API.
- **Audio** is synthesised effects only, with no music, and has not been checked by ear.
- **Strategic missions are templated:** each of the four types has three choices shared across its levels, and each level story is short. Many reward "pick the right approach and keep trust up".
- **Choices affect the future** through relations, trust, treaties, peaceful options, aircraft access, intelligence and endings. The campaign does not branch into different missions.
- **Short sorties:** many combat levels take under a minute; combat types share enemy behaviour.
- **World events** come from 14 templates. Natural disasters and threat events are simple resource, trust or awareness changes.
- **Other countries** have no turn-based strategy of their own.
- **Endings** are timed text sequences, not animated scenes.
- Economy tuning has only been checked by a scripted strategist.
- Local, single-player; no PostgreSQL port.

## Next
0. Play-test and tune treaty burdens and aircraft inventories.
1. Human play-test and retune difficulty, mission length and economy.
2. Unique choices and consequences for key story levels; branching missions.
3. Enemy aircraft that use their nation's own airframes and abilities.
4. AI nation agendas and event chains.
5. Illustrated ending and chapter cinematics; music.
6. Browser end-to-end tests.
7. Optional React/TypeScript client; PostgreSQL.
