# Gru's Grand Heist: Operation Moon Steal
## Game Scenario & Storyboard

**Engine:** Pygame 2D  
**Genre:** Side-scrolling platformer  
**Theme:** Moon heist (moon theft — directly from Despicable Me plot)

---

## Synopsis

> Gru, the world's greatest villain, has one last shot at glory: **steal the Moon**.
> Armed with his Freeze Ray and a half-built Shrink Ray, he must first fight through
> Vector's heavily fortified pyramid, collect the missing Shrink Ray components,
> blast off into space, and finally fire the Shrink Ray at the Moon itself.

---

## Characters

### Gru (Player)
- Moves left/right, jumps
- **Freeze Ray** — fires a slow blue projectile that freezes enemies for 3 seconds
- **Shrink Ray** — charged weapon, only usable in Level 2 climax
- 3 lives; collect Minions to regain a life

### Minions (Collectibles / NPCs)
- Scattered through levels as glowing yellow pickups
- Collecting one = +1 life + "Bee-do!" SFX
- 3 minions per level

### Vector (Level 1 Boss)
- Fires 3-round bursts of fish/shark projectiles
- Moves back and forth on a platform
- Defeated after 3 freeze hits
- Death animation: frozen in block of ice

### Moon Guards (Level 2 Enemies)
- Small robot sentinels on the lunar surface
- Patrol back and forth
- Defeated by Freeze Ray (1 hit)

### Dr. Nefario (NPC — dialogue only)
- Appears as a talking head in the HUD between levels
- Delivers story text and hints

### Agnes (End-game cameo)
- Appears in the victory screen holding the tiny stolen moon
- Voice clip: "It's so fluffy!"

---

## Level 1 — "Vector's Fortress"

### Setting
- **Time:** Night
- **Environment:** Dark city skyline (parallax scrolling background) → Vector's pyramid fortress
- **Background:** Dark urban skyline + pyramid silhouette
- **Platform style:** Stone/metal platforms inside the fortress

### Scene Flow

```
[INTRO CUTSCENE]
Dr. Nefario (dialogue box):
"Gru! Vector has ze Shrink Ray components hidden in his fortress.
 Ve need all three before ve can steal ze Moon. GO!"

[GAMEPLAY BEGINS]
Gru starts at left edge of the city.
```

### Gameplay Loop
1. Walk right through the city exterior (parallax background scrolls)
2. Enter Vector's pyramid — platforms go upward
3. **3 Shrink Ray parts** hidden on platforms (glowing purple collectibles)
4. **Henchmen** patrol each section — dodge or freeze them
5. **Falling platforms** — step on them and they crack + fall after 1 second
6. **Vector's turrets** — stationary, fire projectiles every 3 seconds

### Boss Fight — Vector
```
[CUTSCENE]
Vector appears on a raised platform.
Vector: "YOU?! A villain? Please. I have PYRAMIDS."

[BOSS MECHANICS]
- Vector fires 3 fish at a time (dodge by jumping)
- Gru must land a Freeze Ray hit while Vector is in motion
- After 3 hits → frozen block of ice → level complete!

[LEVEL COMPLETE]
Dr. Nefario: "Ze components are secured! Ze rocket awaits, Gru!"
Screen fades to black → LEVEL 2 loads
```

### Event-Driven Actions (Level 1)
| Trigger | Action |
|---------|--------|
| Step on cracked platform | Platform shakes → falls after 1s → SFX: crack + thud |
| Freeze Ray hits enemy | Enemy frozen in blue ice block for 3s → ice particle burst |
| Collect Shrink Ray part | Purple glow + "bzzzt" SFX + HUD counter updates |
| Collect Minion | "Bee-do!" voice clip + +1 life popup |
| Freeze Ray hits Vector | Ice crystal explosion + Vector health bar decreases |
| Vector health = 0 | Victory animation + ice-block freeze on Vector |

---

## Level 2 — "Operation Moon Steal"

### Setting
- **Section A:** Space — rocket dodging asteroids (vertical or horizontal scroll)
- **Section B:** Lunar surface — run-and-gun with moon gravity
- **Background:** Deep space star field (3-layer parallax) → grey moon surface

### Scene Flow

```
[INTRO CUTSCENE]
Gru in rocket: "Lightbulb... the Moon will be MINE!"

[SECTION A — SPACE FLIGHT]
Rocket flies through asteroid belt.
Player steers rocket (left/right or up/down) to dodge.

[SECTION B — MOON SURFACE]
Rocket lands → Gru exits → side-scrolling on lunar surface.

[CLIMAX]
Gru reaches centre of the Moon → charges Shrink Ray → fires.
```

### Section A — Asteroid Dodge
- Rocket controlled with arrow keys
- Asteroids come from the right at random heights
- Fuel canisters appear — collect to keep moving
- Comet passes occasionally (faster, diagonal — harder dodge)
- If rocket takes 3 hits → level restarts
- **Special effect:** Asteroid glow trail (radial light per Week 6)

### Section B — Lunar Surface
- Side-scrolling platformer (like Level 1)
- **Moon gravity:** jump height increased, fall speed reduced (gravity = 0.3 instead of 0.6)
- **Floor fracture:** some moon tiles crack under Gru's feet → sink after 2 seconds
- **Moon Guards** patrol — freeze them (1 hit each)
- **3 fuel cells** to collect before Shrink Ray fully charges

### Climax — Steal the Moon
```
[CUTSCENE TRIGGER — reach Moon centre]
Gru holds up the Shrink Ray.
Gru: "And now... the Moon is MINE!"

[GAMEPLAY — charge mechanic]
Hold SPACE to charge the Shrink Ray.
Charge bar fills over 3 seconds (glowing green bar).
Release → green laser beam fires at Moon sprite.

[ANIMATION]
Moon sprite scales from full size → 0 over 2 seconds.
(pygame.transform.scale — same as Week 5 exercise)
SFX: sci-fi zap + descending pitch.
Gru catches the tiny moon in his hand.

[VICTORY SCREEN]
Agnes appears: "IT'S SO FLUFFY!"
Music: upbeat victory jingle.
Score and stats displayed.
```

### Event-Driven Actions (Level 2)
| Trigger | Action |
|---------|--------|
| Rocket hits asteroid | Screen shake + SFX + damage flash |
| Collect fuel canister | Glow pickup + SFX + fuel bar updates |
| Land on moon (rocket) | Dust cloud particle burst + thud SFX |
| Step on fracture tile | Tile cracks → sinks in 2s → respawn if falls |
| Moon Guard hit by Freeze Ray | Frozen + falls → ice break SFX |
| Hold SPACE (charge) | Green glow builds up on Shrink Ray sprite |
| Fire Shrink Ray | Green laser beam particle effect → moon shrinks |
| Moon fully shrunk | Victory cutscene triggers |

---

## Special Effects Summary

| Effect | Level | Asset to use | How to implement |
|--------|-------|-------------|-----------------|
| Freeze Ray beam (blue trail) | 1 & 2 | `sprites/vfx/bullets_projectiles.png` — pick a blue beam frame | List of particle dicts — each moves forward, alpha fades per frame |
| Ice crystal burst on hit | 1 & 2 | `sprites/vfx/explosion_small_1.png` — tinted blue | 8 particles explode outward radially from hit point |
| Enemy hit / defeat explosion | 1 & 2 | `sprites/vfx/explosion_sheet_1.png` or `explosion_small_1.png` | Animate through sheet frames on hit event |
| Platform crack + fall | 1 & 2 | Drawn procedurally | Animation state: normal → cracked → falling (y += fall_speed) |
| Asteroid glow trail | 2 | `sprites/vfx/explosion_small_2.png` — loop first few frames | Circle drawn at last 5 positions with decreasing alpha |
| Rocket thruster flames | 2 | `sprites/vfx/explosion_sheet_1.png` — bottom rows only | Orange/red particles emitted upward from rocket base |
| Star parallax (3 layers) | 2 | `backgrounds/moon_space/layer_far_stars.png` | 3 copies scrolled at different x speeds |
| Moon glow aura | 2 | `backgrounds/moon_space/moon_sprite.png` | Radial light surface drawn over moon sprite (Week 6 technique) |
| Shrink Ray charge glow | 2 | `sprites/vfx/bullets_projectiles.png` — green glow frame | Green overlay circle on Gru sprite that grows as bar fills |
| Green laser beam | 2 | `sprites/vfx/bullets_projectiles.png` — green beam frame | Thick green line from Gru to Moon + particle burst at impact |
| Moon scale-down | 2 | `backgrounds/moon_space/moon_sprite.png` | pygame.transform.scale(moon_img, (w, h)) reducing each frame |
| Victory dust cloud | 2 | `sprites/vfx/explosion_small_2.png` — desaturated | White/grey particles burst outward on landing |

---

## HUD Elements

```
┌─────────────────────────────────────────────────────────┐
│  ❤ ❤ ❤   LIVES: 3        SCORE: 000000      LEVEL: 1   │
│  [===FREEZE===]  cooldown bar                           │
│  Parts: 0/3  ██░░░░░░░░                                 │
└─────────────────────────────────────────────────────────┘
```

- Lives (heart icons, top-left)
- Score counter (top-center)
- Freeze Ray cooldown bar (below lives)
- Parts collected counter (level 1) / Fuel bar (level 2)

---

## Controls

| Key | Action |
|-----|--------|
| Arrow Left / Right | Move |
| Arrow Up / Space | Jump |
| Z | Fire Freeze Ray |
| Hold Z (Level 2 climax) | Charge Shrink Ray |
| ESC | Pause |

---

## Screen Flow

```
[MAIN MENU]
    ↓ Press ENTER
[OPENING CUTSCENE — Dr. Nefario briefing]
    ↓ Auto
[LEVEL 1 — Vector's Fortress]
    ↓ Beat Vector
[BETWEEN-LEVEL CUTSCENE — Dr. Nefario: "Ze rocket is ready!"]
    ↓ Auto
[LEVEL 2A — Asteroid Dodge]
    ↓ Reach moon
[LEVEL 2B — Lunar Surface]
    ↓ Charge & fire Shrink Ray
[VICTORY SCREEN — Agnes cameo + score]
    ↓ Press ENTER
[MAIN MENU]
```

---

## Actual Asset Paths (use these in code)

> All assets are downloaded and organized in `assets/`. Use paths below directly.

### Sprites
```
assets/sprites/gru_spritesheet.png           ← Gru full sheet (walk, shoot, jump, hurt, death)
assets/sprites/carl_minion_spritesheet.png   ← Carl minion animations
assets/sprites/vector_spritesheet.png        ← Vector full sheet (walk, shoot, idle)
assets/sprites/vfx/explosion_sheet_1.png     ← Explosion animation (spiky red fire, full size)
assets/sprites/vfx/explosion_sheet_2.png     ← Explosion animation (expanding fireball, full size)
assets/sprites/vfx/explosion_small_1.png     ← Same as above, half size (use for small hits)
assets/sprites/vfx/explosion_small_2.png     ← Same as above, half size
assets/sprites/vfx/bullets_projectiles.png   ← Bullet/beam sprite collection (freeze ray, enemy shots)
```

> Still needed (not yet downloaded):
> - Gru individual frames cut from sheet → use EZGif: https://ezgif.com/sprite-cutter
> - Moon guard / henchmen sprites → draw in Piskel or find on itch.io
> - City night background for Level 1 → search itch.io "night city platformer background free"

### Backgrounds
```
assets/backgrounds/moon_space/layer_far_stars.png   ← Level 2 star field (parallax far)
assets/backgrounds/moon_space/moon_sprite.png        ← THE MOON — use this for the Shrink Ray target
assets/backgrounds/moon_space/bg_composed.png        ← Level 2 full background (static option)
assets/backgrounds/moon_forest/layer_far_stars.png   ← Level 1 night sky layer
assets/backgrounds/moon_forest/layer_moon.png        ← Level 1 moon layer (yellow)
assets/backgrounds/moon_forest/layer_trees_fg.png    ← Level 1 foreground trees
assets/backgrounds/moon_forest/bg_composed.png       ← Level 1 full composed scene
assets/backgrounds/moon_blood/bg_composed.png        ← Boss room background (red moon)
assets/backgrounds/moon_clouds/bg_composed.png       ← Alternative / cutscene background
```

### Music
```
assets/music/menu.wav                    ← Main menu
assets/music/level1_great_mission.mp3   ← Level 1 background (recommended)
assets/music/level1_doomed.mp3          ← Level 1 alternative (darker)
assets/music/level2_space_ambient.ogg   ← Level 2 space flight (4 min loop)
assets/music/level2_space_travel.wav    ← Level 2 moon surface section
assets/music/boss_battle.wav            ← Vector boss fight
assets/music/victory_jingle.wav         ← Level complete / win screen
assets/music/cutscene.wav               ← Dr. Nefario dialogue scenes
assets/music/loops/DarkDnB_1.wav        ← Alternative boss music
assets/music/loops/FutureAmbient_1.wav  ← Alternative space music
```

### Sound Effects
```
assets/sfx/laser_freeze_ray.flac    ← Freeze Ray fire  ⚠️ convert to OGG before use
assets/sfx/minion_laugh_1.wav       ← Minion collected
assets/sfx/minion_yahoo_1.wav       ← Level complete / pickup
assets/sfx/minion_hit_1.wav         ← Player takes damage
assets/sfx/minion_taunt_1.wav       ← Vector boss dialogue
assets/sfx/minion_voice_long.wav    ← Ambient minion chatter
assets/sfx/alien_voice_1.wav        ← Space section atmosphere
assets/sfx/character_scream.wav     ← Player death
assets/sfx/level_start.wav          ← Level intro sting
```

> ⚠️ Convert `laser_freeze_ray.flac` → OGG before loading in Pygame:
> https://cloudconvert.com/flac-to-ogg  (free, no install)
