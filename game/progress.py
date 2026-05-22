"""Persistent scene-completion tracking.

Stores which scenes the player has finished (at least once) in a small JSON
file at the project root. Used by the main menu to gate the level select:
each scene unlocks when its predecessor is in the completed set.

The file is written lazily — it only appears on disk after the first
mark_complete() call.
"""

import json
import os

from settings import BASE_DIR


PROGRESS_PATH = os.path.join(BASE_DIR, "progress.json")

# scenes the player can actually unlock + play. 4-6 are storyboard placeholders
# until teammates implement them, so they're handled by is_coming_soon() below.
SCENE_IDS = ("scene1", "scene2", "scene3", "scene6")


def load_progress() -> set:
    """Read the saved completion set. Returns an empty set on any read/parse
    error so the game falls back to a fresh-start state instead of crashing.
    """
    try:
        with open(PROGRESS_PATH, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return set()
    except (json.JSONDecodeError, OSError, ValueError) as e:
        print(f"[progress] couldn't read {PROGRESS_PATH}: {e} — starting fresh")
        return set()

    raw = data.get("completed", []) if isinstance(data, dict) else []
    # filter to known scene ids — drops anything garbage / from a future version
    return {s for s in raw if isinstance(s, str) and s in SCENE_IDS}


def _save_progress(completed: set) -> None:
    """Persist the completion set. Failures are non-fatal — we print a warning
    and continue (the player just won't see progress survive a restart)."""
    payload = {"completed": sorted(completed)}
    try:
        with open(PROGRESS_PATH, "w") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        print(f"[progress] couldn't write {PROGRESS_PATH}: {e}")


def mark_complete(scene_id: str) -> None:
    """Record that the player has finished `scene_id` at least once.
    Idempotent — re-marking an already-completed scene is a no-op write."""
    if scene_id not in SCENE_IDS:
        return
    completed = load_progress()
    if scene_id in completed:
        return  # nothing changed; skip the write
    completed.add(scene_id)
    _save_progress(completed)


def is_unlocked(scene_id: str) -> bool:
    """True when the player is allowed to start `scene_id` from the menu.
    Scene 1 is always available; later scenes need the previous one beaten."""
    if scene_id == "scene1":
        return True
    completed = load_progress()
    if scene_id == "scene2":
        return "scene1" in completed
    if scene_id == "scene3":
        return "scene2" in completed
    if scene_id == "scene6":
        return "scene1" in completed #RESNOTE : CHANGE TO RETURN SCENE 5 WHEN IT'S READY OKAY
    
    return False  # scene4+ aren't unlockable yet


def is_coming_soon(scene_id: str) -> bool:
    """True for storyboard scenes that aren't implemented yet (4, 5, 6).
    The main menu uses this to label them differently from LOCKED entries."""
    return scene_id in ("scene4", "scene5")
