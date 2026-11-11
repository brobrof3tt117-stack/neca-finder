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
    ("rvt-endocop", "robocop,terminator", "Video games", "EndoCop and Terminator Dog", "endocop|terminator dog", "endoglow,endo glow,sarah,lot"),
    ("rvt-assault", "robocop,terminator", "Video games", "Endoskeleton Assault 2-pack", "endoskeleton assault", "endoglow,endo glow,sarah,lot"),
    ("rvt-gunner", "robocop,terminator", "Video games", "Heavy Gunner Endoskeleton", "heavy gunner", "endoglow,endo glow,sarah,lot"),
    ("rvt-future", "robocop,terminator", "Video games", "Future RoboCop", "future robocop", "endoglow,endo glow,sarah,lot"),
    ("rvt-rocket", "robocop,terminator", "Video games", "RoboCop with Rocket Launcher", "robocop+rocket launcher|rocket launcher+robocop", "endoglow,endo glow,sarah,lot"),
    ("rvt-flame", "robocop,terminator", "Video games", "RoboCop with Flamethrower", "robocop+flamethrower|robocop+flame thrower", "endoglow,endo glow,sarah,lot"),
    ("rvt-plasma", "robocop,terminator", "Video games", "T-800 with Plasma Rifle", "plasma rifle", "endoglow,endo glow,sarah,lot"),
    ("rvt", "robocop,terminator", "Video games", "Other RoboCop vs. Terminator figures",
     "robocop+terminator|endocop|endoskeleton assault|heavy gunner|terminator dog|robocop+rocket launcher|robocop+flamethrower|robocop+flame thrower|future robocop|plasma rifle",
     "endoglow,endo glow,sarah,lot"),

    # ===== Terminator =====
    ("term-darkfate", "terminator", "Later films", "Terminator: Dark Fate (T-800 and Sarah Connor)", "dark fate", ""),
    ("term-genisys", "terminator", "Later films", "Terminator Genisys (T-800 Guardian, T-1000)", "genisys", ""),
    ("term-connors", "terminator", "Terminator 2: Judgment Day (1991)", "Sarah and John Connor", "sarah|john connor|connor", ""),
    ("term-reese", "terminator", "The Terminator (1984)", "Kyle Reese", "kyle reese|reese", ""),
    ("term-endoglow", "terminator", "Terminator 2: Judgment Day (1991)", "Endoglow Endoskeleton (glow in the dark)", "endoglow|endo glow|endoskeleton+glow", ""),
    ("term-metalmash", "terminator", "Terminator 2: Judgment Day (1991)", "Future War Metal Mash Endoskeleton (Kenner Tribute)", "metal mash", ""),
    ("term-endo-quarter", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Endoskeleton 1/4 Scale (18 inch)", "endoskeleton+1 4|endoskeleton+18|endoskeleton+light up eyes|endoskeleton+quarter", ""),
    ("term-endo-bd", "terminator", "Terminator 2: Judgment Day (1991)", "Battle Damaged Endoskeleton", "endoskeleton+battle damaged|endoskeleton+battle damage", ""),
    ("term-endo-cult", "terminator", "Terminator 2: Judgment Day (1991)", "T2 Endoskeleton (Cult Classics, 2005)", "endoskeleton+cult classics|endoskeleton+2005", ""),
    ("term-endo-1984", "terminator", "The Terminator (1984)", "T-800 Endoskeleton (The Terminator)", "the terminator+endoskeleton", "terminator 2,t2,judgment,cult classics"),
    ("term-endo", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Endoskeleton (other releases)", "endoskeleton|endoglow|endo glow|metal mash", ""),
    ("term-t1000-whitehot", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 White Hot (Kenner Tribute)", "white hot", ""),
    ("term-t1000-metal", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 Liquid Metal (SDCC 2010)", "liquid metal", ""),
    ("term-t1000-nitrogen", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 Liquid Nitrogen (20th Anniversary)", "liquid nitrogen", ""),
    ("term-t1000-galleria", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 Galleria Mall", "t 1000+galleria|t 100+galleria", ""),
    ("term-t1000-pescadero", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 Pescadero Hospital", "t 1000+pescadero|t 100+pescadero", ""),
    ("term-t1000-steelmill", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 Steel Mill", "t 1000+steel mill|t 100+steel mill", ""),
    ("term-t1000-moto", "terminator", "Terminator 2: Judgment Day (1991)", "Ultimate T-1000 (Motorcycle Cop)", "motorcycle cop|motocycle cop|mottorcycle cop|t 1000+ultimate", ""),
    ("term-t1000", "terminator", "Terminator 2: Judgment Day (1991)", "T-1000 (other releases)", "t 1000|t 100|motorcycle cop|liquid metal|liquid nitrogen|white hot", ""),
    ("term-t2-pescadero", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Pescadero Escape", "pescadero", "t 1000,predator,dutch"),
    ("term-t2-cyberdyne", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Cyberdyne Showdown", "cyberdyne", "t 1000,predator,dutch"),
    ("term-t2-steelmill", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Steel Mill", "steel mill", "t 1000,predator,dutch"),
    ("term-t2-final", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Final Battle (12 inch)", "final battle", "t 1000,predator,dutch"),
    ("term-t2-3d", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 3D Release (Galleria)", "galleria|t 800+3d|terminator 2+3d", "t 1000,predator,dutch"),
    ("term-t2-mom", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Man or Machine", "man or machine", "t 1000,predator,dutch"),
    ("term-t2-bat", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Battle Across Time", "battle across time", "t 1000,predator,dutch"),
    ("term-t2-powerarm", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 Power Arm (Kenner Tribute)", "power arm", "t 1000,predator,dutch"),
    ("term-t2-ultimate", "terminator", "Terminator 2: Judgment Day (1991)", "Ultimate T-800 (Terminator 2)", "t 800+ultimate+terminator 2|t 800+ultimate+t2|t 800+ultimate+judgment day", "t 1000,predator,dutch"),
    ("term-t800-t2", "terminator", "Terminator 2: Judgment Day (1991)", "T-800 (Terminator 2, other releases)",
     "pescadero|cyberdyne|steel mill|final battle|galleria|man or machine|battle across time|power arm|terminator 2|t2|judgment day", "t 1000,predator,dutch"),
    ("term-t800-video", "terminator", "Video games", "T-800 (8-bit video game)", "t 800+video game|t 800+8 bit|terminator+nes", ""),
    ("term-t800-technoir", "terminator", "The Terminator (1984)", "Ultimate T-800 (Tech Noir)", "tech noir|tech nior", "predator,dutch"),
    ("term-t800-police", "terminator", "The Terminator (1984)", "Ultimate T-800 (Police Station Assault)", "police station", "predator,dutch"),
    ("term-t800-tanker", "terminator", "The Terminator (1984)", "T-800 Tanker Truck Pursuit", "tanker", "predator,dutch"),
    ("term-t800-bd", "terminator", "The Terminator (1984)", "T-800 Battle Damaged (Cult Classics)", "t 800+battle damaged|t 800+battle damage|terminator+battle damaged", "predator,dutch"),
    ("term-t800-ultimate", "terminator", "The Terminator (1984)", "Ultimate T-800 (The Terminator, 2015)", "ultimate+t 800|ultimate+schwarzenegger|the terminator+ultimate|the terminator+2015|51911|the terminator+schwarzenegger", "terminator 2,t2,judgment,endoskeleton,predator,dutch,tech noir,tech nior,police,tanker,battle damaged,video game,8 bit,club"),
    ("term-t800", "terminator", "The Terminator (1984)", "T-800 (The Terminator, other releases)", "tech noir|police station|tanker|t 800|schwarzenegger|the terminator", "predator,dutch"),

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
    ("pred-2pack-tru", P, "Predator 2 (1990)", "Toys R Us 2-packs (City Hunter with Jungle Hunter or Berserker)", "city hunter+jungle hunter|city hunter+berserker|city hunter+2 pack|city hunter+toys r us", ""),
    ("pred-dc", P, "Games, comics and concepts", "Green Lantern vs. Predator (DC 2-pack)", "green lantern|sinestro", ""),
    ("alien-dc", "alien", "Alien vs. Predator", "Superman vs. Alien (DC 2-pack)", "superman", ""),
    ("pred-quarter-excl", P, "Games, comics and concepts", "1/4 Scale Exclusives (Gort Mask, Big Red)", "gort|big red", ""),
    ("pred-bladefighter", P, "Games, comics and concepts", "Blade Fighter Vehicle", "blade fighter", ""),
    ("pred-hound", P, "Predators (2010) and The Predator (2018)", "Predator Hound", "hound", ""),
    ("pred-hawkins", P, "Predator 2 (1990)", "Rick Hawkins", "hawkins", ""),
    ("pred-rivalry", "predator,alien", "Alien vs. Predator", "Celtic vs. Grid (Rivalry Reborn 2-pack)", "celtic+grid|rivalry reborn", ""),
    ("pred-dutch-linn", P, "Games, comics and concepts", "Dutch and Linn (Arcade 2-pack)", "dutch+linn", ""),
    ("pred-dutch-vs", P, "Predator (1987)", "Dutch vs. Jungle Hunter (Final Battle 2-pack)", "dutch+jungle hunter+final battle|dutch+vs+jungle hunter", ""),
    ("pred-dutch-disguise", P, "Predator (1987)", "Dutch (Jungle Disguise)", "dutch+disguise|jungle disguise", ""),
    ("pred-dutch-extraction", P, "Predator (1987)", "Dutch (Jungle Extraction)", "dutch+extraction|jungle extraction", ""),
    ("pred-dutch-patrol", P, "Predator (1987)", "Dutch (Jungle Patrol)", "dutch+patrol|jungle patrol", ""),
    ("pred-dutch-quarter", P, "Predator (1987)", "Dutch 1/4 Scale (18 inch)", "dutch+1 4|dutch+18|dutch+quarter", ""),
    ("pred-dutch-lava", P, "Predator (1987)", "Dutch (Lava Planet)", "dutch+lava", ""),
    ("pred-dutch", P, "Predator (1987)", "Dutch Schaefer (other releases)", "dutch|schaefer|schaeffer|predator+schwarzenegger|predator+arnold", ""),
    ("pred-city-demon", P, "Predator 2 (1990)", "City Demon Predator", "city demon", ""),
    ("pred-jungle-demon", P, "Predator (1987)", "Jungle Demon Predator", "jungle demon", ""),
    ("pred-city-stealth", P, "Predator 2 (1990)", "Stealth City Hunter (SDCC 2012)", "city hunter+stealth|city hunter+cloaked|city hunter+sdcc", ""),
    ("pred-city-video", P, "Games, comics and concepts", "City Hunter (8-bit and 16-bit video game)", "city hunter+video game|city hunter+8 bit|city hunter+16 bit|city hunter+nes", ""),
    ("pred-city-quarter", P, "Predator 2 (1990)", "City Hunter 1/4 Scale (18 inch)", "city hunter+1 4|city hunter+18|city hunter+led|city hunter+quarter|predator 2+1 4", ""),
    ("pred-city-bd", P, "Predator 2 (1990)", "Ultimate Battle Damaged City Hunter", "city hunter+battle damaged|city hunter+battle damage", ""),
    ("pred-city-poster", P, "Predator 2 (1990)", "City Hunter (Poster Series)", "city hunter+poster|predator 2+poster", ""),
    ("pred-city-ultimate", P, "Predator 2 (1990)", "Ultimate City Hunter", "city hunter+ultimate", ""),
    ("pred-city", P, "Predator 2 (1990)", "City Hunter (other releases)", "city hunter|predator 2+city", ""),
    ("pred-alpha", P, "Games, comics and concepts", "Alpha Predator (100th Edition)", "alpha+predator|100th", ""),
    ("pred-feral-bear", P, "Prey and Badlands", "Ultimate Feral Predator (Bear Blood)", "bear blood|feral+bear", ""),
    ("pred-feral-camo", P, "Prey and Badlands", "Feral Predator (Camo Reveal)", "camo reveal|feral+camo", ""),
    ("pred-feral-ultramate", P, "Prey and Badlands", "ULTRAmate Feral Predator", "ultramate", ""),
    ("pred-feral", P, "Prey and Badlands", "Ultimate Feral Predator (Prey)", "feral|ferel|camo reveal|prey+predator|prey+ultimate", ""),
    ("pred-dek-bone", P, "Prey and Badlands", "Ultimate Dek (Bone Bison Armor)", "dek+bone|dek+bison", "kwei"),
    ("pred-dek-training", P, "Prey and Badlands", "Ultimate Dek (Training Armor)", "dek+training", "kwei"),
    ("pred-dek", P, "Prey and Badlands", "Dek (other releases)", "dek", "kwei"),
    ("pred-thia", P, "Prey and Badlands", "Thia and Bud (Badlands)", "thia|bud+badlands", ""),
    ("pred-kwei", P, "Prey and Badlands", "Kwei (Badlands)", "kwei", ""),
    ("pred-badlands", P, "Prey and Badlands", "Other Badlands figures", "badlands", ""),
    ("pred-samurai", P, "Games, comics and concepts", "Samurai Predator (Hunting Grounds)", "samurai", ""),
    ("pred-stoneheart", P, "Games, comics and concepts", "Stone Heart Predator (Concrete Jungle)", "stone heart", "bone throne,diorama"),
    ("pred-clanleader", P, "Games, comics and concepts", "Clan Leader Predator (Concrete Jungle)", "clan leader", "bone throne,diorama"),
    ("pred-scarface", P, "Games, comics and concepts", "Scarface Predator (Concrete Jungle)", "scarface", "bone throne,diorama"),
    ("pred-concrete", P, "Games, comics and concepts", "Other Concrete Jungle figures", "stone heart|clan leader|concrete jungle|scarface", "bone throne,diorama"),
    ("pred-arcade-hunter", P, "Games, comics and concepts", "Hunter Predator (Arcade)", "arcade+hunter|hunter predator+alien vs predator", "razor claws,razor claw,arachnoid,chrysalis,alien warrior,warrior alien"),
    ("pred-arcade-warrior", P, "Games, comics and concepts", "Warrior Predator (Arcade)", "arcade+warrior+predator", "razor claws,razor claw,arachnoid,chrysalis,alien warrior,warrior alien"),
    ("pred-arcade", P, "Games, comics and concepts", "Other Arcade Predators (Lasershot, Mad)", "arcade+predator|lasershot", "razor claws,razor claw,arachnoid,chrysalis,alien warrior,warrior alien"),
    ("pred-ancient", P, "Alien vs. Predator", "Ancient Warrior Predator", "ancient warrior", ""),
    ("pred-scar", P, "Alien vs. Predator", "Scar Predator", "scar", ""),
    ("pred-celtic", P, "Alien vs. Predator", "Celtic Predator", "celtic", ""),
    ("pred-chopper", P, "Alien vs. Predator", "Chopper Predator", "chopper", ""),
    ("pred-wolf", P, "Alien vs. Predator", "Wolf Predator (AvP Requiem)", "wolf|requiem+predator|avpr+predator", "hybrid,predalien"),
    ("pred-elder-golden", P, "Predator 2 (1990)", "Elder: The Golden Angel", "golden angel|elder+golden", ""),
    ("pred-elder-greyback", P, "Predator 2 (1990)", "Elder Greyback (Predator 2)", "greyback|predator 2+elder", ""),
    ("pred-elder-avp", P, "Alien vs. Predator", "Elder Predator (AvP)", "elder+avp|elder+alien vs predator|elder+series 17", ""),
    ("pred-elder", P, "Predator 2 (1990)", "Elder Predator (other releases)", "elder|golden angel|greyback", ""),
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
    ("pred-alienhunter", P, "Games, comics and concepts", "Ultimate Alien Hunter Predator", "ultimate alien hunter|alien hunter+predator", "hive wars,ghost,viper,spiked,blade fighter"),
    ("pred-jungle-quarter", P, "Predator (1987)", "Jungle Hunter 1/4 Scale (18 inch)", "jungle hunter+1 4|jungle hunter+18|jungle hunter+quarter|jungle hunter+led|predator+1 4+led|jungle hunter+19|predator+19 inch", "predator 2,city"),
    ("pred-jungle-25th", P, "Predator (1987)", "Jungle Hunter (25th Anniversary)", "jungle hunter+25th|predator+25th+jungle", "city hunter"),
    ("pred-jungle-ultimate", P, "Predator (1987)", "Ultimate Jungle Hunter", "jungle hunter+ultimate|ultimate+jungle", "predator 2,dutch,city"),
    ("pred-jungle-30th", P, "Predator (1987)", "Jungle Hunter (30th Anniversary)", "jungle hunter+30th|jungle+30th", "predator 2,dutch"),
    ("pred-jungle-classic", P, "Predator (1987)", "Classic Jungle Hunter (Series 1, Classics)", "classic+predator|jungle hunter+series 1|unmasked+predator", "predator 2"),
    ("pred-jungle", P, "Predator (1987)", "Jungle Hunter (other releases)", "jungle|thermal vision|predator+1987|classic predator|unmasked+predator|predator+30th", "predator 2,warrior alien,alien warrior"),

    # ===== Alien =====
    ("alien-earth", "alien", "Prometheus, Covenant, Romulus and Earth", "Alien: Earth figures", "alien earth|wendy", ""),
    ("alien-romulus", "alien", "Prometheus, Covenant, Romulus and Earth", "Alien: Romulus Xenomorph (all versions)", "romulus|xx121", ""),
    ("alien-neomorph", "alien", "Prometheus, Covenant, Romulus and Earth", "Neomorph", "neomorph", ""),
    ("alien-covenant", "alien", "Prometheus, Covenant, Romulus and Earth", "Alien: Covenant Xenomorph", "covenant", ""),
    ("alien-engineer", "alien", "Prometheus, Covenant, Romulus and Earth", "Engineer (Prometheus)", "engineer", ""),
    ("alien-david", "alien", "Prometheus, Covenant, Romulus and Earth", "David (Prometheus)", "david", ""),
    ("alien-fifield", "alien", "Prometheus, Covenant, Romulus and Earth", "Fifield (Prometheus)", "fifield", ""),
    ("alien-shaw", "alien", "Prometheus, Covenant, Romulus and Earth", "Shaw (Prometheus)", "shaw", ""),
    ("alien-deacon", "alien", "Prometheus, Covenant, Romulus and Earth", "Deacon and Trilobite (Prometheus)", "deacon|trilobite", ""),
    ("alien-prometheus", "alien", "Prometheus, Covenant, Romulus and Earth", "Other Prometheus figures", "prometheus|engineer|fifield|deacon", ""),
    ("alien-isolation", "alien", "Alien 3, Resurrection and Isolation", "Alien: Isolation (Amanda Ripley and more)", "isolation|amanda", ""),
    ("alien-ft-burster", "alien", "Video games", "Burster Alien (Fireteam Elite)", "burster", ""),
    ("alien-ft-spitter", "alien", "Video games", "Spitter Alien (Fireteam Elite)", "spitter", ""),
    ("alien-ft-runner", "alien", "Video games", "Runner Alien (Fireteam Elite)", "runner+fireteam|runner+fire team|runner+firestream|runner alien+elite", ""),
    ("alien-ft-prowler", "alien", "Video games", "Prowler Alien (Fireteam Elite)", "prowler", ""),
    ("alien-fireteam", "alien", "Video games", "Other Fireteam Elite aliens", "fireteam|fire team|prowler|spitter|burster|firestream", ""),
    ("alien-resurrection", "alien", "Alien 3, Resurrection and Isolation", "Alien Resurrection (Ripley 8, Warrior)", "resurrection|ripley 8|newborn", ""),
    ("alien-commando", "alien", "Alien 3, Resurrection and Isolation", "Weyland-Yutani Commando (Alien 3)", "weyland yutani commando|commando+alien 3", ""),
    ("alien-3-8bit", "alien", "Video games", "Dog Alien (Alien 3, 8-bit video game)", "alien 3+8 bit|alien 3+video game|alien3+8 bit|dog+video game|dog xenomorph+video game", ""),
    ("alien-3-ripley", "alien", "Alien 3, Resurrection and Isolation", "Ripley (Fiorina 161 Prisoner)", "fiorina|161+ripley|prisoner+ripley|bald+ripley", ""),
    ("alien-3-ultimate", "alien", "Alien 3, Resurrection and Isolation", "Ultimate Dog Alien (Alien 3, 2019)", "alien 3+ultimate|dog alien+ultimate|dog xenomorph+ultimate", ""),
    ("alien-3", "alien", "Alien 3, Resurrection and Isolation", "Dog Alien (Alien 3)", "alien 3|alien3|dog alien", ""),
    ("alien-redqueen", "alien", "Video games", "Genocide Red Queen Mother", "red queen|genocide+queen", ""),
    ("alien-genocide", "alien", "Video games", "Genocide Xenomorph Warriors", "genocide|red queen", ""),
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
    ("alien-ripley-compression", "alien", "Alien (1979)", "Ripley (Compression Suit)", "ripley+compression", "amanda"),
    ("alien-ripley-jumpsuit", "alien", "Alien (1979)", "Ripley (Jumpsuit, 40th Anniversary)", "ripley+jumpsuit|ripley+40th", "amanda"),
    ("alien-ripley-kenner", "alien", "Aliens (1986)", "Ripley (Kenner Tribute)", "ripley+kenner", ""),
    ("alien-ripley-bomber", "alien", "Aliens (1986)", "Ripley (Bomber Jacket)", "ripley+bomber", ""),
    ("alien-ripley", "alien", "Aliens (1986)", "Ellen Ripley (other releases)", "ripley", ""),
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
    ("alien-warrior-translucent", "alien", "Aliens (1986)", "Translucent Blue Warrior Alien", "translucent+warrior|translucent blue", ""),
    ("alien-warrior-kenner", "alien", "Aliens (1986)", "Warrior Alien (Kenner-style, 2017)", "vicious alien attacker|warrior alien+2017", "translucent"),
    ("alien-prototype-quarter", "alien", "Alien (1979)", "Translucent Prototype Suit 1/4 Scale", "translucent+1 4|prototype+1 4|translucent+22|prototype+quarter", ""),
    ("alien-prototype-40th", "alien", "Alien (1979)", "The Alien (Prototype Suit, 40th Anniversary)", "prototype+40th", "translucent"),
    ("alien-prototype", "alien", "Alien (1979)", "The Alien (Translucent Prototype Suit)", "translucent|prototype suit|prototype+xenomorph|prototype+concept", ""),
    ("alien-quarter", "alien", "Alien (1979)", "Big Chap Xenomorph 1/4 Scale (18 inch)", "alien+1 4|xenomorph+1 4|xenomorph+18|alien+18 inch|alien+18|biggest chap|big chap+1 4|big chap+22|xenomorph+22", "queen,ripley,hicks,predator,warrior,aliens 1986"),
    ("alien-bigchap-40th", "alien", "Alien (1979)", "Ultimate Big Chap (40th Anniversary)", "big chap+40th|alien+40th+ultimate", ""),
    ("alien-bigchap-ue", "alien", "Alien (1979)", "Big Chap Ultimate Edition (2015)", "big chap+ultimate edition|big chap+ultimate|alien+ultimate edition+xenomorph", "aliens"),
    ("alien-bigchap-35th", "alien", "Alien (1979)", "Big Chap (35th Anniversary)", "alien+35th|xenomorph+35th", ""),
    ("alien-early", "alien", "Alien (1979)", "Original 9-inch Xenomorph (2008 to 2010)", "alien+9 inch|xenomorph+9 inch|alien+9|xenomorph+2008|alien+2008|alien+cult classics|extendable inner jaw|bendable tail|alien+2009", "aliens,predator,series 9"),
    ("alien-40th-bloody", "alien", "Alien (1979)", "The Alien (Bloody, 40th Anniversary)", "alien+40th+bloody|bloody+xenomorph|alien+bloody", "aliens 1986"),
    ("alien-40th-giger", "alien", "Alien (1979)", "The Alien (Giger, 40th Anniversary)", "alien+40th+giger|the alien+40th|alien+40th+xenomorph|alien 1979+40th|alien+40th anniversary+7", "ripley,kane,dallas,lambert,parker,ash,brett,facehugger,chestburster,egg,space jockey,1 4,22,prototype,translucent,ultimate,big chap,warrior,queen,nostromo"),
    ("alien-bigchap-s2", "alien", "Alien (1979)", "Big Chap (Series 2, 2014 clamshell)", "big chap+series 2|xenomorph+series 2+alien|big chap+clamshell", ""),
    ("alien-bigchap", "alien", "Alien (1979)", "Big Chap Xenomorph (other releases)", "big chap|alien+40th|alien+1979|alien+35th|xenomorph+35th|51646", ""),
    ("alien-warrior-40th", "alien", "Aliens (1986)", "Ultimate Xenomorph Warrior (40th Anniversary)", "aliens+40th|warrior+40th", "queen"),
    ("alien-warrior-arcade", "alien", "Video games", "Xenomorph Warrior (Arcade, pink)", "arcade+warrior|arcade+xenomorph|aliens+arcade", ""),
    ("alien-warrior-bd", "alien", "Aliens (1986)", "Battle Damaged Xenomorph Warrior", "warrior+battle damaged|xenomorph+battle damaged|warrior+battle damage", ""),
    ("alien-warrior-blue", "alien", "Aliens (1986)", "Ultimate Xenomorph Warrior (Blue)", "warrior+blue|xenomorph+blue|ultimate edition+blue|blue+alien", "brown"),
    ("alien-warrior-brown", "alien", "Aliens (1986)", "Ultimate Xenomorph Warrior (Brown)", "warrior+brown|xenomorph+brown|ultimate edition+brown|brown+alien", "blue"),
    ("alien-warrior-ue", "alien", "Aliens (1986)", "Ultimate Edition Xenomorph Warrior (with facehugger)", "aliens+ultimate edition|aliens+ultimate+xenomorph|alien+ultimate+warrior|ultimate edition+facehugger", "blue,brown,big chap,dog,alien 3,40th"),
    ("alien-warrior-2013", "alien", "Aliens (1986)", "Xenomorph Warrior (Series 1 and 2, 2013)", "warrior+2013|xenomorph+2013+aliens|warrior+series 1|warrior+series 2|51394", ""),
    ("alien-warrior", "alien", "Aliens (1986)", "Xenomorph Warrior (other releases)", "aliens+ultimate edition|aliens+warrior|aliens+xenomorph|alien+warrior|aliens+40th|aliens+1986|blue+warrior|brown+warrior", ""),
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
