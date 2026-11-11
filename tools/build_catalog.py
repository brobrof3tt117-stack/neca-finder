#!/usr/bin/env python3
"""Builds site/data/catalog.json from the readable list below.

Each figure line is: (id, tab, section, name, match, not)
  match: alternatives split by "|", words that must ALL appear joined by "+"
         e.g. "jungle hunter|jungle+predator" means: has "jungle hunter", OR has both "jungle" and "predator"
  not:   words or phrases that stop this figure from matching (comma separated)
Titles are checked against the figures from top to bottom. The first match wins.
"""
import json
from pathlib import Path

TABS = [
    {"id": "alien", "name": "Alien", "title": "Alien", "tagline": "Xenomorphs, Colonial Marines and the Nostromo crew",
     "sections": ["Alien (1979)", "Aliens (1986)", "Alien 3, Resurrection and Isolation", "Prometheus, Covenant, Romulus and Earth",
                  "Kenner Tribute creatures", "Alien vs. Predator", "Video games", "Everything else"]},
    {"id": "predator", "name": "Predator", "title": "Predator", "tagline": "Every hunter NECA has made, from the jungle to the Badlands",
     "sections": ["Predator (1987)", "Predator 2 (1990)", "Alien vs. Predator", "Predators (2010) and The Predator (2018)",
                  "Prey and Badlands", "Games, comics and concepts", "Everything else"]},
    {"id": "robocop", "name": "RoboCop", "title": "RoboCop", "tagline": "Dead or alive, you're coming with me",
     "sections": ["RoboCop (1987)", "RoboCop 2 and 3", "Video games", "Everything else"]},
    {"id": "terminator", "name": "Terminator", "title": "Terminator", "tagline": "T-800s, T-1000s and the Connors",
     "sections": ["The Terminator (1984)", "Terminator 2: Judgment Day (1991)", "Later films", "Video games", "Everything else"]},
    {"id": "thing", "name": "The Thing", "title": "The Thing (1982)", "tagline": "John Carpenter's The Thing, Outpost 31",
     "sections": ["The Thing (1982)", "Everything else"]},
    {"id": "efny", "name": "Escape From New York", "title": "Escape From New York", "tagline": "Snake Plissken, Manhattan 1997",
     "sections": ["Escape From New York (1981)", "Everything else"]},
]

NOT_ADDAMS = "addams,wednesday,fantastic four,marvel"
P = "predator"

FIGURES = [
    # ===== Escape From New York =====
    ("efny-snake", "efny", "Escape From New York (1981)", "Snake Plissken", "plissken|escape from new york|escape from ny", ""),

    # ===== The Thing =====
    ("thing-dog", "thing", "The Thing (1982)", "Dog Creature (Ultimate Deluxe)", "dog creature|the thing+dog", NOT_ADDAMS),
    ("thing-poster", "thing", "The Thing (1982)", "The Thing (Poster Series, light up)", "the thing+poster|thing+lenticular|the thing+40th", NOT_ADDAMS + ",robocop,predator"),
    ("thing-laststand", "thing", "The Thing (1982)", "MacReady (Last Stand)", "macready+last stand|the thing+last stand|macready+v3|macready+v 3", "outpost,station"),
    ("thing-station", "thing", "The Thing (1982)", "MacReady (Station Survival)", "station survival|macready+v2|macready+version 2|macready+v 2", "outpost,last stand"),
    ("thing-outpost", "thing", "The Thing (1982)", "MacReady (Outpost 31)", "macready+outpost|outpost 31|macready+v1|macready+version 1", "last stand,station"),
    ("thing-macready", "thing", "The Thing (1982)", "MacReady (version not in title)", "macready", ""),

    # ===== RoboCop vs Terminator (shows on both tabs) =====
    ("rvt", "robocop,terminator", "Video games", "RoboCop vs. The Terminator (game figures)",
     "robocop+terminator|endocop|endoskeleton assault|heavy gunner|terminator dog|robocop+rocket launcher|robocop+flamethrower|robocop+flame thrower|future robocop|plasma rifle",
     "endoglow,endo glow,sarah,lot"),

    # ===== Terminator =====
    ("term-darkfate", "terminator", "Later films", "Terminator: Dark Fate (T-800 and Sarah Connor)", "dark fate", ""),
    ("term-genisys", "terminator", "Later films", "Terminator Genisys (T-800 Guardian, T-1000)", "genisys", ""),
    ("term-connors", "terminator", "Terminator 2: Judgment Day (1991)", "Sarah and John Connor", "sarah|john connor|connor", ""),
    ("term-reese", "terminator", "The Terminator (1984)", "Kyle Reese", "kyle reese|reese", ""),
    ("term-endo", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Endoskeleton (all versions)", "endoskeleton|endoglow|endo glow|metal mash", ""),
    ("term-t1000", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 (all versions)", "t 1000|t 100|motorcycle cop|liquid metal|liquid nitrogen|white hot", ""),
    ("term-t800-t2", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 (Terminator 2)",
     "pescadero|cyberdyne|steel mill|final battle|galleria|man or machine|battle across time|power arm|terminator 2|t2|judgment day", "t 1000,predator,dutch"),
    ("term-t800-video", "terminator", "Video games", "T-800 (8-bit video game)", "t 800+video game|t 800+8 bit|terminator+nes", ""),
    ("term-t800", "terminator", "The Terminator (1984)", "T-800 (The Terminator)", "tech noir|police station|tanker|t 800|schwarzenegger|the terminator", "predator,dutch"),

    # ===== RoboCop =====
    ("robo-ed209", "robocop", "RoboCop (1987)", "ED-209", "ed 209", ""),
    ("robo-3", "robocop", "RoboCop 2 and 3", "RoboCop 3 (Jetpack and Assault Cannon)", "jetpack|jet pack|robocop 3|assault cannon", ""),
    ("robo-night", "robocop", "RoboCop (1987)", "Night Fighter RoboCop (glow in the dark)", "night fighter|robocop+glow|robocop+gitd|glowinthedark", ""),
    ("robo-chair", "robocop", "RoboCop (1987)", "Ultimate Battle Damaged RoboCop with Chair", "robocop+chair|omni consumer|ocp+chair", ""),
    ("robo-murphy", "robocop", "RoboCop (1987)", "Ultimate Alex Murphy (OCP Uniform)", "uniform|alex j murphy|alex murphy|murphey", "poster,jetpack,holster,battle damage,battle damaged"),
    ("robo-video", "robocop", "Video games", "RoboCop (8-bit NES video game)", "robocop+nes|robocop+8 bit|robocop+video game|robocop+nintendo|robocop+1989", ""),
    ("robo-bd", "robocop", "RoboCop (1987)", "Battle Damaged RoboCop (2012)", "robocop+battle damaged|robocop+battle damage", ""),
    ("robo-holster", "robocop", "RoboCop (1987)", "RoboCop with Spring Loaded Holster", "robocop+holster", ""),
    ("robo-poster", "robocop", "RoboCop (1987)", "RoboCop (Poster Series)", "robocop+poster|robocop+red suit|robocop+future of law enforcement", ""),
    ("robo-ultimate", "robocop", "RoboCop (1987)", "Ultimate RoboCop", "ultimate+robocop", ""),
    ("robo-classic", "robocop", "RoboCop (1987)", "RoboCop (2011 original release)", "robocop+2011|robocop+25th|robocop+first series", ""),

    # ===== Predator =====
    ("pred-rivalry", "predator,alien", "Alien vs. Predator", "Celtic vs. Grid (Rivalry Reborn 2-pack)", "celtic+grid|rivalry reborn", ""),
    ("pred-dutch-linn", P, "Games, comics and concepts", "Dutch and Linn (Arcade 2-pack)", "dutch+linn", ""),
    ("pred-dutch", P, "Predator (1987)", "Dutch Schaefer (all versions)", "dutch|schaefer|schaeffer|predator+schwarzenegger|predator+arnold", ""),
    ("pred-city-demon", P, "Predator 2 (1990)", "City Demon Predator", "city demon", ""),
    ("pred-jungle-demon", P, "Predator (1987)", "Jungle Demon Predator", "jungle demon", ""),
    ("pred-city", P, "Predator 2 (1990)", "City Hunter Predator", "city hunter|predator 2+city", ""),
    ("pred-alpha", P, "Games, comics and concepts", "Alpha Predator (100th Edition)", "alpha+predator|100th", ""),
    ("pred-feral", P, "Prey and Badlands", "Feral Predator (Prey)", "feral|ferel|camo reveal|prey+predator|prey+ultimate", ""),
    ("pred-dek", P, "Prey and Badlands", "Dek (Badlands)", "dek", "kwei"),
    ("pred-thia", P, "Prey and Badlands", "Thia and Bud (Badlands)", "thia|bud+badlands", ""),
    ("pred-kwei", P, "Prey and Badlands", "Kwei (Badlands)", "kwei", ""),
    ("pred-badlands", P, "Prey and Badlands", "Other Badlands figures", "badlands", ""),
    ("pred-samurai", P, "Games, comics and concepts", "Samurai Predator (Hunting Grounds)", "samurai", ""),
    ("pred-concrete", P, "Games, comics and concepts", "Concrete Jungle (Stone Heart, Clan Leader)", "stone heart|clan leader|concrete jungle|scarface", "bone throne,diorama"),
    ("pred-arcade", P, "Games, comics and concepts", "Arcade Predators (Lasershot, Warrior, Hunter)", "arcade+predator|lasershot", "razor claws,razor claw,arachnoid,chrysalis,alien warrior,warrior alien"),
    ("pred-ancient", P, "Alien vs. Predator", "Ancient Warrior Predator", "ancient warrior", ""),
    ("pred-scar", P, "Alien vs. Predator", "Scar Predator", "scar", ""),
    ("pred-celtic", P, "Alien vs. Predator", "Celtic Predator", "celtic", ""),
    ("pred-chopper", P, "Alien vs. Predator", "Chopper Predator", "chopper", ""),
    ("pred-wolf", P, "Alien vs. Predator", "Wolf Predator (AvP Requiem)", "wolf|requiem+predator|avpr+predator", "hybrid,predalien"),
    ("pred-elder", P, "Predator 2 (1990)", "Elder Predator (Golden Angel, Greyback, AvP)", "elder|golden angel|greyback", ""),
    ("pred-scout", P, "Predator 2 (1990)", "Scout Predator", "scout+predator", "cinemachines"),
    ("pred-snake", P, "Predator 2 (1990)", "Snake Predator", "snake+predator", ""),
    ("pred-lost", P, "Predator 2 (1990)", "Lost Predator", "lost+predator", ""),
    ("pred-guardian", P, "Predator 2 (1990)", "Guardian Predator", "guardian+predator", ""),
    ("pred-boar", P, "Predator 2 (1990)", "Boar Predator", "boar", ""),
    ("pred-stalker", P, "Predator 2 (1990)", "Stalker Predator", "stalker", ""),
    ("pred-shaman", P, "Predator 2 (1990)", "Shaman Predator", "shaman", ""),
    ("pred-warrior", P, "Predator 2 (1990)", "Warrior Predator (Predator 2)", "warrior+predator 2|ultimate warrior+predator", ""),
    ("pred-berserker", P, "Predators (2010) and The Predator (2018)", "Berserker Predator", "berserker", ""),
    ("pred-falconer", P, "Predators (2010) and The Predator (2018)", "Falconer Predator", "falconer", ""),
    ("pred-tracker", P, "Predators (2010) and The Predator (2018)", "Tracker Predator", "tracker", ""),
    ("pred-fugitive", P, "Predators (2010) and The Predator (2018)", "Fugitive Predator (Lab Escape)", "fugitive|lab escape", ""),
    ("pred-emissary", P, "Predators (2010) and The Predator (2018)", "Emissary Predator", "emissary", ""),
    ("pred-assassin", P, "Predators (2010) and The Predator (2018)", "Assassin Predator (Deluxe)", "assassin", ""),
    ("pred-badblood", P, "Predators (2010) and The Predator (2018)", "Bad Blood vs. Enforcer 2-pack", "bad blood|enforcer", ""),
    ("pred-ahab", P, "Games, comics and concepts", "Ahab Predator", "ahab", ""),
    ("pred-tusk", P, "Games, comics and concepts", "Cracked Tusk Predator", "cracked tusk", ""),
    ("pred-spiked", P, "Games, comics and concepts", "Spiked Tail Predator", "spiked tail", ""),
    ("pred-temple", P, "Alien vs. Predator", "Temple Guard Predator", "temple guard", ""),
    ("pred-serpent", P, "Alien vs. Predator", "Serpent Hunter Predator", "serpent hunter", ""),
    ("pred-youngblood", P, "Alien vs. Predator", "Youngblood Predator", "youngblood|young blood", ""),
    ("pred-machiko", P, "Games, comics and concepts", "Machiko Noguchi", "machiko", ""),
    ("pred-lasershot", P, "Games, comics and concepts", "Lasershot Predator (Kenner Tribute)", "laser shot", ""),
    ("pred-renegade", P, "Games, comics and concepts", "Renegade Predator", "renegade", ""),
    ("pred-hivewars", P, "Games, comics and concepts", "Hive Wars Predator", "hive wars", ""),
    ("pred-lava", P, "Games, comics and concepts", "Lava Planet Predator", "lava planet", ""),
    ("pred-water", P, "Games, comics and concepts", "Water Emergence Predator", "water emergence", ""),
    ("pred-ghost", P, "Games, comics and concepts", "Ghost Predator", "ghost+predator", ""),
    ("pred-albino", P, "Games, comics and concepts", "Albino Predator", "albino+predator", ""),
    ("pred-viper", P, "Games, comics and concepts", "Viper Predator", "viper", ""),
    ("pred-wasp", P, "Games, comics and concepts", "Wasp Predator", "wasp", ""),
    ("pred-ambush", P, "Games, comics and concepts", "Ambush Predator", "ambush", ""),
    ("pred-8bit", P, "Games, comics and concepts", "Predator (8-bit video game)", "predator+8 bit|predator+video game|predator+nes", ""),
    ("pred-avp2pack", "predator,alien", "Alien vs. Predator", "Alien vs. Predator 2-packs (Toys R Us)", "vs predator+2 pack|vs predator+two pack|vs predator+toys r us|vs predator+tru|ultimate battle+vs predator|ultimate battle+2 pack", "battle damaged,battle damage"),
    ("pred-jungle", P, "Predator (1987)", "Jungle Hunter Predator (all versions)", "jungle|thermal vision|predator+1987|classic predator|unmasked+predator|predator+30th", "predator 2,warrior alien,alien warrior"),

    # ===== Alien =====
    ("alien-earth", "alien", "Prometheus, Covenant, Romulus and Earth", "Alien: Earth figures", "alien earth|wendy", ""),
    ("alien-romulus", "alien", "Prometheus, Covenant, Romulus and Earth", "Alien: Romulus Xenomorph (all versions)", "romulus|xx121", ""),
    ("alien-neomorph", "alien", "Prometheus, Covenant, Romulus and Earth", "Neomorph", "neomorph", ""),
    ("alien-covenant", "alien", "Prometheus, Covenant, Romulus and Earth", "Alien: Covenant Xenomorph", "covenant", ""),
    ("alien-prometheus", "alien", "Prometheus, Covenant, Romulus and Earth", "Prometheus (Engineer, David, Fifield and more)", "prometheus|engineer|fifield|deacon", ""),
    ("alien-isolation", "alien", "Alien 3, Resurrection and Isolation", "Alien: Isolation (Amanda Ripley and more)", "isolation|amanda", ""),
    ("alien-fireteam", "alien", "Video games", "Fireteam Elite aliens (Burster, Spitter, Runner, Prowler)", "fireteam|fire team|prowler|spitter|burster", ""),
    ("alien-resurrection", "alien", "Alien 3, Resurrection and Isolation", "Alien Resurrection (Ripley 8, Warrior)", "resurrection|ripley 8|newborn", ""),
    ("alien-3", "alien", "Alien 3, Resurrection and Isolation", "Alien 3 (Dog Alien, Ripley and more)", "alien 3|alien3|dog alien", ""),
    ("alien-genocide", "alien", "Video games", "Genocide (red Xenomorphs, Red Queen)", "genocide|red queen", ""),
    ("alien-hybrid", "alien", "Alien vs. Predator", "Predalien (AvP Requiem Hybrid)", "predalien|hybrid+requiem|hybrid+avpr|hybrid+avp", ""),
    ("alien-thermal", "alien", "Alien vs. Predator", "Thermal Vision Warrior Alien (glow in the dark)", "thermal vision+alien+warrior|thermal vision+warrior alien", ""),
    ("alien-razor", "alien", "Alien vs. Predator", "Razor Claws Alien", "razor claw|razor claws", ""),
    ("alien-arachnoid", "alien", "Alien vs. Predator", "Arachnoid Alien", "arachnoid|arachinoid", ""),
    ("alien-chrysalis", "alien", "Alien vs. Predator", "Chrysalis Alien", "chrysalis", ""),
    ("alien-grid", "alien", "Alien vs. Predator", "Grid Alien", "grid", ""),
    ("alien-panther", "alien", "Kenner Tribute creatures", "Panther Alien", "panther+alien|panther+aliens|panther+kenner", ""),
    ("alien-cougar", "alien", "Kenner Tribute creatures", "Night Cougar Alien", "night cougar|cougar+alien", ""),
    ("alien-rhino", "alien", "Kenner Tribute creatures", "Rhino Alien", "rhino", ""),
    ("alien-gorilla", "alien", "Kenner Tribute creatures", "Gorilla Alien", "gorilla", ""),
    ("alien-snake", "alien", "Kenner Tribute creatures", "Snake Alien", "snake alien|snake+kenner", "predator"),
    ("alien-scorpion", "alien", "Kenner Tribute creatures", "Scorpion Alien", "scorpion", ""),
    ("alien-mantis", "alien", "Kenner Tribute creatures", "Mantis Alien", "mantis", ""),
    ("alien-qfh", "alien", "Kenner Tribute creatures", "Queen Facehugger", "queen facehugger", ""),
    ("alien-bull", "alien", "Kenner Tribute creatures", "Bull Alien", "bull alien|bull+kenner", ""),
    ("alien-crab", "alien", "Kenner Tribute creatures", "Crab Alien", "crab+alien", ""),
    ("alien-ripley-newt", "alien", "Aliens (1986)", "Ripley and Newt (2-pack)", "ripley+newt", ""),
    ("alien-ripley", "alien", "Aliens (1986)", "Ellen Ripley (all versions)", "ripley", ""),
    ("alien-newt", "alien", "Aliens (1986)", "Newt", "newt", ""),
    ("alien-hicks", "alien", "Aliens (1986)", "Corporal Hicks", "hicks", ""),
    ("alien-hudson", "alien", "Aliens (1986)", "Private Hudson", "hudson", ""),
    ("alien-vasquez", "alien", "Aliens (1986)", "Private Vasquez", "vasquez|vasques", ""),
    ("alien-apone", "alien", "Aliens (1986)", "Sergeant Apone", "apone", ""),
    ("alien-drake", "alien", "Aliens (1986)", "Private Drake", "drake", ""),
    ("alien-gorman", "alien", "Aliens (1986)", "Lieutenant Gorman", "gorman", ""),
    ("alien-frost", "alien", "Aliens (1986)", "Private Frost", "frost", ""),
    ("alien-bishop", "alien", "Aliens (1986)", "Bishop", "bishop", ""),
    ("alien-burke", "alien", "Aliens (1986)", "Burke", "burke", ""),
    ("alien-windrix", "alien", "Aliens (1986)", "Sergeant Windrix", "windrix", ""),
    ("alien-cameron", "alien", "Aliens (1986)", "Colonel Cameron (director tribute)", "cameron", ""),
    ("alien-creaturepack", "alien", "Aliens (1986)", "Creature Pack (30th Anniversary)", "creature pack", ""),
    ("alien-queen", "alien", "Aliens (1986)", "Alien Queen", "queen", "facehugger"),
    ("alien-loader", "alien", "Aliens (1986)", "Power Loader", "power loader|p 5000", ""),
    ("alien-albino", "alien", "Kenner Tribute creatures", "Albino Drone Alien", "albino", ""),
    ("alien-kane", "alien", "Alien (1979)", "Kane", "kane", ""),
    ("alien-dallas", "alien", "Alien (1979)", "Dallas", "dallas", ""),
    ("alien-lambert", "alien", "Alien (1979)", "Lambert", "lambert", ""),
    ("alien-ash", "alien", "Alien (1979)", "Ash", "ash", ""),
    ("alien-parker", "alien", "Alien (1979)", "Parker", "parker", ""),
    ("alien-brett", "alien", "Alien (1979)", "Brett", "brett", ""),
    ("alien-bigchap", "alien", "Alien (1979)", "Big Chap Xenomorph (Alien 1979)", "big chap|alien+40th|alien+1979|alien+35th|xenomorph+35th|51646", ""),
    ("alien-warrior", "alien", "Aliens (1986)", "Xenomorph Warrior (Aliens, blue and brown)", "aliens+ultimate edition|aliens+warrior|aliens+xenomorph|alien+warrior|aliens+40th|aliens+1986|blue+warrior|brown+warrior", ""),
]

# Anything that passes every check but matches no figure lands in the "Everything else" tile of its tab.
OTHER = {
    "alien": "Other Alien figures",
    "predator": "Other Predator figures",
    "robocop": "Other RoboCop figures",
    "terminator": "Other Terminator figures",
    "thing": "Other The Thing figures",
    "efny": "Other Escape From New York figures",
}

# A title must contain one of its tab's words before it can match any figure on that tab, so a
# Gargoyles "Hudson" or an Evil Dead "Ash" never lands on the Alien tab.
# Order matters too: the first tab whose words appear in the title gets a leftover listing.
TAB_WORDS = [
    ("efny", ["plissken", "escape from new york", "escape from ny"]),
    ("thing", ["macready", "outpost 31", "the thing+carpenter", "the thing+1982", "the thing+ultimate", "the thing+alien",
               "the thing+poster", "the thing+lenticular", "the thing+sdcc", "the thing+40th", "the thing+light up", "dog creature"]),
    ("robocop", ["robocop", "ed 209", "ocp", "endocop"]),
    ("terminator", ["terminator", "t 800", "t 1000", "endoskeleton", "skynet", "judgment day", "dark fate", "genisys"]),
    ("predator", ["predator", "predators", "yautja", "prey", "badlands", "avp", "avpr", "hunting grounds", "concrete jungle", "dek", "feral"]),
    ("alien", ["alien", "aliens", "xenomorph", "prometheus", "covenant", "romulus", "facehugger", "chestburster", "nostromo", "ripley",
               "space marine", "colonial marine"]),
]


def alts(spec):
    return [[w.strip() for w in a.split("+") if w.strip()] for a in spec.split("|") if a.strip()]


def main():
    tab_ids = [t["id"] for t in TABS]
    figures, seen = [], set()
    for fid, tabs, section, name, match, nots in FIGURES:
        assert fid not in seen, fid
        seen.add(fid)
        tabs = [t.strip() for t in tabs.split(",")]
        for t in tabs:
            assert t in tab_ids, (fid, t)
            assert section in next(x for x in TABS if x["id"] == t)["sections"], (fid, section)
        figures.append({
            "id": fid, "tabs": tabs, "section": section, "name": name,
            "match": alts(match), "not": [n.strip() for n in nots.split(",") if n.strip()],
        })
    for tid, name in OTHER.items():
        figures.append({"id": tid + "-other", "tabs": [tid], "section": "Everything else", "name": name,
                        "match": [], "not": [], "other": True})
    out = {
        "_read_me": "Made by tools/build_catalog.py. Edit that file and run it, rather than editing this one by hand.",
        "tabs": TABS,
        "figures": figures,
        "tab_words": [{"tab": t, "match": alts("|".join(w))} for t, w in TAB_WORDS],
    }
    path = Path(__file__).resolve().parent.parent / "site" / "data" / "catalog.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(figures)} figures to {path}")


if __name__ == "__main__":
    main()
