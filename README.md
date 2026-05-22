# Gru's Grand Heist: Operation Moon Steal

CT029-3-2 Imaging & Special Effects — Group Assignment  
Asia Pacific University of Technology & Innovation, 2026

---

## Project Structure

```
Assignment/
├── assets/
│   ├── sprites/
│   │   ├── gru_spritesheet.png           ← Gru full animation sheet (walk, shoot, jump, hurt)
│   │   ├── carl_minion_spritesheet.png   ← Carl Minion animations
│   │   ├── vector_spritesheet.png        ← Vector Perkins animations
│   │   └── vfx/
│   │       ├── explosion_sheet_1–4.png   ← Full-size explosion animation sheets
│   │       ├── explosion_small_1–4.png   ← Half-size explosion sheets (small hits)
│   │       └── bullets_projectiles.png   ← Bullet/beam sprite collection
│   ├── backgrounds/
│   │   ├── moon_space/                   ← Level 2: star field + grey moon (parallax layers)
│   │   ├── moon_forest/                  ← Level 1: forest night + yellow moon
│   │   ├── moon_blood/                   ← Boss room: red moon + bare branches
│   │   ├── moon_clouds/                  ← Alternative: blue moon + clouds
│   │   └── _psd_source/                  ← Photoshop source files
│   ├── music/
│   │   ├── menu.wav / loading.wav / victory_jingle.wav
│   │   ├── level1_*.mp3                  ← Level 1 action tracks
│   │   ├── level2_*.ogg/.wav             ← Level 2 space ambient tracks
│   │   ├── boss_*.wav/.mp3               ← Boss fight music
│   │   └── loops/                        ← 33 CC0 genre loops (DarkDnB, EDM, 8Bit …)
│   └── sfx/
│       ├── minion_laugh/hit/taunt/yahoo_1–3.wav
│       ├── minion_voice_long.wav
│       ├── laser_freeze_ray.flac         ← ⚠️ Convert to OGG before use in Pygame
│       ├── alien_voice_1–3.wav
│       ├── character_scream.wav
│       └── level_start.wav
├── game/                                 ← Python source files (to be added)
└── documents/
    ├── assignment.pdf                    ← Original brief
    ├── assets.md                         ← Full asset reference with Pygame paths & notes
    └── initial_proposed_scenario.md      ← Game scenario, storyboard & special effects plan
```

---

## Pending Before Coding (OUTDATED)

- [ ] **Cut sprite sheets into frames** — use https://ezgif.com/sprite-cutter  
  Upload `gru_spritesheet.png`, `carl_minion_spritesheet.png`, `vector_spritesheet.png`
- [ ] **Remove backgrounds from character sprites** — teal (Gru), green (Carl), black (Vector)  
  Use https://ezgif.com/background-remover
- [ ] **Convert `sfx/laser_freeze_ray.flac` → OGG** — Pygame cannot load FLAC  
  Use https://cloudconvert.com/flac-to-ogg or `ffmpeg -i laser_freeze_ray.flac laser_freeze_ray.ogg`
- [ ] **Download Level 1 city night background** — not yet acquired  
  Search itch.io: "night city platformer background free"


## added info: 
- Bypass level 3,4,5 by playing and completing scene 1 to play scene 6 (temporary)