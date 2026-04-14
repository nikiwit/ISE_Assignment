# Gru's Grand Heist — Master Asset Reference

> All assets downloaded, renamed, and organized.
> Use the paths below directly in your Python/Pygame code.

---

## Folder Structure

```
assets/
├── sprites/
│   ├── gru_spritesheet.png
│   ├── carl_minion_spritesheet.png
│   ├── vector_spritesheet.png
│   └── vfx/
│       ├── explosion_sheet_1.png   ← full-size, multiple explosion styles
│       ├── explosion_sheet_2.png
│       ├── explosion_sheet_3.png
│       ├── explosion_sheet_4.png
│       ├── explosion_small_1.png   ← half-size versions (better for on-hit FX)
│       ├── explosion_small_2.png
│       ├── explosion_small_3.png
│       ├── explosion_small_4.png
│       └── bullets_projectiles.png ← colorful bullet/beam sprite collection
├── backgrounds/
│   ├── moon_space/                 ← Level 2: pure space, grey moon
│   ├── moon_forest/                ← Level 1 end / cinematic: forest night, yellow moon
│   ├── moon_blood/                 ← alternative: red moon + bare branches (boss scene?)
│   ├── moon_clouds/                ← alternative: blue moon + clouds
│   └── _psd_source/                ← Photoshop source files (editing only)
├── music/
│   ├── menu.wav
│   ├── loading.wav
│   ├── level1_doomed.mp3
│   ├── level1_flags.mp3
│   ├── level1_great_mission.mp3
│   ├── level2_space_ambient.ogg
│   ├── level2_space_travel.wav
│   ├── level2_spacetime.mp3
│   ├── boss_battle.wav
│   ├── boss_waking_devil.mp3
│   ├── cutscene.wav
│   ├── dramatic.wav
│   ├── victory_jingle.wav
│   ├── misc_twists.mp3
│   ├── misc_warped.mp3
│   └── loops/                      ← 33 CC0 genre loops (DarkDnB, EDM, 8Bit, etc.)
└── sfx/
    ├── minion_laugh_1/2/3.wav
    ├── minion_hit_1/2/3.wav
    ├── minion_taunt_1/2/3.wav
    ├── minion_yahoo_1/2/3.wav
    ├── minion_voice_long.wav
    ├── alien_voice_1/2/3.wav
    ├── laser_freeze_ray.flac
    ├── character_scream.wav
    └── level_start.wav
```

---

## SPRITES

| File | What it is | Notes |
|------|-----------|-------|
| `sprites/gru_spritesheet.png` | Gru — full animation sheet | Walk, shoot freeze ray, crouch, jump, hurt, death. Teal background. Ripped from DM J2ME game, no credit needed. |
| `sprites/carl_minion_spritesheet.png` | Carl Minion — full animation sheet | Small sprites, bright green background. Use EZGif to cut. |
| `sprites/vector_spritesheet.png` | Vector Perkins — full animation sheet | Walk, shoot, idle. Black background. Credit VectorVideo64 if used. |

### VFX Sprites (`sprites/vfx/`)

| File | What it is | Use in game |
|------|-----------|-------------|
| `explosion_sheet_1.png` | Red fire explosion — 9 rows × 7 cols | On-hit effect for enemy defeated |
| `explosion_sheet_2.png` | Expanding fireball — 9 rows × 7 cols | Larger explosion, asteroid hit |
| `explosion_sheet_3.png` | Not yet viewed — check before use | — |
| `explosion_sheet_4.png` | Not yet viewed — check before use | — |
| `explosion_small_1–4.png` | Half-size versions of above | Better for freeze ray impact, small hits |
| `bullets_projectiles.png` | Colorful bullet/beam collection | Freeze Ray projectiles, enemy shots |

> To cut sprite sheets into frames: https://ezgif.com/sprite-cutter
> Upload PNG → set tile size → download ZIP of individual frames

---

## BACKGROUNDS

Each scene has separate parallax layers — load them at different scroll speeds in Pygame.

### `backgrounds/moon_space/` — Level 2 space scene (grey moon, stars)
| File | What it is | Pygame use |
|------|-----------|-----------|
| `layer_far_stars.png` | Star field only — dark purple sky | Scroll slowest (parallax layer 1) |
| `moon_sprite.png` | Moon isolated on white background | **Use as the game's moon object** — this is the sprite that gets shrunk by the Shrink Ray |
| `bg_composed.png` | Full scene composed (stars + moon) | Static background if not doing parallax |
| `bg_composed_large.png` | Larger version of above | Higher resolution option |

### `backgrounds/moon_forest/` — Level 1 end / cinematic (yellow moon, forest)
| File | What it is | Pygame use |
|------|-----------|-----------|
| `layer_far_stars.png` | Dark star field | Scroll slowest |
| `layer_moon.png` | Yellow moon isolated | Mid layer |
| `layer_trees_fg.png` | Pine tree silhouettes on white | Scroll fastest (foreground) |
| `bg_composed.png` | Full composed scene | Static option |

### `backgrounds/moon_blood/` — Boss room / cinematic (red moon, bare branches)
| File | What it is | Pygame use |
|------|-----------|-----------|
| `layer_far_stars.png` | Sky layer | Scroll slowest |
| `layer_moon.png` | Red moon | Mid layer |
| `layer_branches_fg.png` | Bare tree branches foreground | Scroll fastest |
| `bg_composed.png` | Full scene | Static option |

### `backgrounds/moon_clouds/` — Alternative (blue moon, clouds)
| File | What it is | Pygame use |
|------|-----------|-----------|
| `layer_far_stars.png` | Sky layer | Scroll slowest |
| `layer_moon.png` | Blue moon | Mid layer |
| `layer_clouds_fg.png` | Cloud bank foreground | Scroll fastest |
| `bg_composed.png` | Full scene | Static option |

> **Which background for which level:**
> - Level 1 (city night) → still needed, search itch.io "night city platformer background"
> - Level 2 space flight → `moon_space/bg_composed.png` or parallax layers
> - Level 2 moon surface → `moon_forest/bg_composed.png` (forest = lunar terrain look)
> - Boss room → `moon_blood/bg_composed.png`

---

## MUSIC

All tracks are CC0 except where marked ⚠️.

### Ready to use directly
| File | Use for | Style |
|------|---------|-------|
| `music/menu.wav` | Main menu | Atmospheric |
| `music/loading.wav` | Loading / transition screen | — |
| `music/level1_doomed.mp3` | Level 1 — tense action | Dark orchestral |
| `music/level1_flags.mp3` | Level 1 — alternative | Upbeat action |
| `music/level1_great_mission.mp3` | Level 1 — heroic chase | Epic |
| `music/level2_space_ambient.ogg` | Level 2 — space ambient | Calm space (4 min loop) |
| `music/level2_space_travel.wav` | Level 2 — travel section | Slow, moody |
| `music/level2_spacetime.mp3` | Level 2 — alternative | Sci-fi |
| `music/boss_battle.wav` | Boss fight | Intense |
| `music/boss_waking_devil.mp3` | Boss fight — alternative | Heavy |
| `music/cutscene.wav` | Between-level cutscene | Soft/narrative |
| `music/dramatic.wav` | Dramatic moment | Cinematic |
| `music/victory_jingle.wav` | Victory / level complete | Short jingle |
| `music/misc_twists.mp3` | Spare / gameplay moment | — |
| `music/misc_warped.mp3` | Spare / menu alt | — |

### Loops (`music/loops/`) — 33 CC0 loops
Good for: flexible background music, pick one per level and loop it.
Genres available: `8Bit`, `80sRetro`, `Chillstep`, `DarkDnB`, `DirtyElectroHouse`, `DnB`, `EDM`, `Formant`, `FutureAmbient`, `HipHopNoir`, `House`, `MelodicHouse`

> **Recommendation:**
> - Menu: `loops/Chillstep_1.wav` or `music/menu.wav`
> - Level 1: `music/level1_great_mission.mp3`
> - Level 2 space: `music/level2_space_ambient.ogg`
> - Boss: `music/boss_battle.wav`
> - Victory: `music/victory_jingle.wav`

---

## SOUND EFFECTS

| File | Use for |
|------|---------|
| `sfx/minion_laugh_1.wav` | Minion collected — celebration |
| `sfx/minion_laugh_2.wav` | Minion collected — alt |
| `sfx/minion_laugh_3.wav` | Minion collected — alt |
| `sfx/minion_hit_1.wav` | Gru takes damage |
| `sfx/minion_hit_2.wav` | Gru takes damage — alt |
| `sfx/minion_hit_3.wav` | Enemy hit |
| `sfx/minion_taunt_1.wav` | Vector taunts (boss phase) |
| `sfx/minion_taunt_2.wav` | Vector taunts — alt |
| `sfx/minion_taunt_3.wav` | Vector taunts — alt |
| `sfx/minion_yahoo_1.wav` | Level complete / victory |
| `sfx/minion_yahoo_2.wav` | Collectible picked up |
| `sfx/minion_yahoo_3.wav` | Collectible picked up — alt |
| `sfx/minion_voice_long.wav` | Ambient / cutscene minion chatter |
| `sfx/alien_voice_1.wav` | Space section — background chatter |
| `sfx/alien_voice_2.wav` | Space section — alt |
| `sfx/alien_voice_3.wav` | Space section — alt |
| `sfx/laser_freeze_ray.flac` | Freeze Ray fired ⚠️ FLAC — convert to WAV/OGG first |
| `sfx/character_scream.wav` | Gru hurt badly / fall death |
| `sfx/level_start.wav` | Level intro sting |

> ⚠️ `laser_freeze_ray.flac` — Pygame cannot play FLAC directly.
> Convert to OGG or WAV using: https://cloudconvert.com/flac-to-ogg (free, browser)
> Or run: `ffmpeg -i laser_freeze_ray.flac laser_freeze_ray.ogg`

---

## TOOLS FOR EDITING ASSETS

| Tool | Link | Use for |
|------|------|---------|
| EZGif Sprite Cutter | https://ezgif.com/sprite-cutter | Cut sprite sheets into individual frames |
| EZGif Background Remover | https://ezgif.com/background-remover | Remove teal/green BG from Gru & Carl sheets |
| CloudConvert | https://cloudconvert.com/flac-to-ogg | Convert FLAC → OGG for Pygame |
| Piskel | https://www.piskelapp.com/ | Draw new sprites (Dr. Nefario, Agnes) |
| Libresprite | https://libresprite.github.io/ | Full sprite editor, free |
| GIMP | https://www.gimp.org/ | Crop, recolour, resize |

---

## ATTRIBUTION (copy into report References section)

```
Sprites:
- Gru & Minion sprite sheet. HydraProDev via The Spriters Resource.
  No credit required. https://www.spriters-resource.com/mobile/despicablemethegamej2me/sheet/220372/
- Carl Minion sprite sheet. The Spriters Resource (DS/DSi — Minion Mayhem).
  https://www.spriters-resource.com/ds_dsi/despicablememinionmayhem
- Vector Perkins sprite sheet. VectorVideo64 on DeviantArt. Credit required.
  https://www.deviantart.com/vectorvideo/art/Vector-Perkins-sprites-Despicable-Me-1162018048

Backgrounds:
- Free Moon Pixel Game Backgrounds (4 scenes + parallax layers). CraftPix / itch.io.

Music (CC0 — no credit required):
- Alexander Ehlers — Free Music Pack. OpenGameArt.org. CC0.
  https://opengameart.org/content/free-music-pack
- Space Music: Out There. yd on OpenGameArt.org. CC0.
  https://opengameart.org/content/space-music-out-there
- Game Music Loops (33 loops). Pudgyplatypus on OpenGameArt.org. CC0.
  https://opengameart.org/content/royalty-free-game-music-loops

Sound Effects (CC0 — no credit required):
- Minion-like voice sounds. ManuelGraf on Freesound.org.
  https://freesound.org/people/yummie/packs/13333/
- Minion voice. fattirewhitey on Freesound.org. CC0.
  https://freesound.org/people/fattirewhitey/sounds/326247/
- Laser Weapon Sounds. unfa on Freesound.org. CC0.
  https://freesound.org/people/unfa/sounds/187119/
- Space fiction sound effects. Robinhood76 on Freesound.org.
  https://freesound.org/people/Robinhood76/packs/6080/

Visual Effects Sprites:
- Free Explosion Animations 2. OpenGameArt.org.
- M484 Bullet Collection. OpenGameArt.org.
```
