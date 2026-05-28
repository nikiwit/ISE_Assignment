"""main.py — Entry point for Gru's Grand Heist: Operation Moon Steal.

I structured this the same way as the multi-level menu game from the lab:
a state string controls which screen is active, and each scene is a separate
function that runs its own loop and returns the next state when it's done.
pygame_menu handles the main menu so we get a polished look with minimal code.
"""

import os
import pygame
import pygame_menu

from settings import WIDTH, HEIGHT, FPS, DARK, ASSETS_DIR
from scene1_lab      import scene1
from scene2_fortress import scene2
from scene4_asteroid import scene4
from scene6_stealmoon import scene6

from progress import load_progress, mark_complete, is_unlocked, is_coming_soon

MENU   = "menu"
SCENE1 = "scene1"
SCENE2 = "scene2"
SCENE3 = "scene3"  # placeholder for the boss fight — teammates plug their scene in here
SCENE4 = "scene4"
SCENE6 = "scene6"  # final scene, gru steals the moon


# scene id (display label, scene state constant or None for placeholders)
_SCENE_BUTTONS = (
    ("scene1", "1 LAB BRIEFING",      SCENE1),
    ("scene2", "2 VECTORS FORTRESS",  SCENE2),
    ("scene3", "3 BOSS FIGHT",        SCENE3),
    ("scene4", "4 ASTEROID DODGE",    SCENE4),
    ("scene5", "5 LUNAR SURFACE",     None),
    ("scene6", "6 STEAL THE MOON",    SCENE6),
)


def _build_main_menu(menu_theme, start_scene_cb, quit_cb):
    """Build the main-menu Menu fresh from current progress.

    Called every time we (re)enter the MENU state, so unlocks reflect immediately
    after a scene is completed without needing to relaunch the game.
    """
    menu = pygame_menu.Menu(
        "",
        550, 420,
        theme=menu_theme,
        position=(50, 8, False),
        center_content=False,
    )
    menu.add.vertical_margin(6)
    menu.add.label("GRUS GRAND HEIST",       font_size=28, font_color=(255, 255, 255))
    menu.add.vertical_margin(8)
    menu.add.label("Operation Steal the Moon", font_size=16)
    menu.add.vertical_margin(20)

    DIM = (110, 110, 130)  # disabled-button text colour

    for sid, label, scene_const in _SCENE_BUTTONS:
        if is_coming_soon(sid):
            # dimmed + unselectable is enough — no need for an extra label
            btn = menu.add.button(label, lambda: None)
            btn.is_selectable = False
            btn.readonly = True
            btn.update_font({"color": DIM})
        elif not is_unlocked(sid):
            btn = menu.add.button(f"{label}  [LOCKED]", lambda: None)
            btn.is_selectable = False
            btn.readonly = True
            btn.update_font({"color": DIM})
        else:
            # default-arg trick freezes the current scene_const into the closure
            menu.add.button(label, lambda s=scene_const: start_scene_cb(s))
        menu.add.vertical_margin(4)

    menu.add.vertical_margin(12)
    menu.add.button("EXIT", quit_cb)
    return menu


def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    WINDOW_TITLE = "Gru's Grand Heist: Operation Moon Steal"
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    state      = MENU
    prev_state = None  # we compare state against prev_state each frame to detect scene transitions (mainly for music)

    # menu background, loaded and scaled once at startup
    bg_path = os.path.join(ASSETS_DIR, "backgrounds", "menu_bg.png")
    menu_bg = pygame.image.load(bg_path).convert()
    menu_bg = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))

    menu_music = os.path.join(ASSETS_DIR, "music", "menu.wav")

    def start_scene(scene_const):
        nonlocal state
        state = scene_const

    def quit_game():
        pygame.quit()
        raise SystemExit

    # custom theme — no title bar so we can place the title as a centered label widget instead
    menu_theme = pygame_menu.Theme(
        background_color=(8, 12, 30, 190),
        title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
        widget_font=pygame_menu.font.FONT_8BIT,
        widget_font_color=(200, 220, 255),
        widget_font_size=20,
        selection_color=(100, 200, 255),
    )

    # initial build for the very first frame; rebuilt on every menu re-entry below
    main_menu = _build_main_menu(menu_theme, start_scene, quit_game)

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # (re)start the menu music whenever we land back in the menu state from somewhere else.
        # each scene loads its own track on entry, so we only have to act on the transition itself.
        # rebuilding the menu here picks up any unlocks the player just earned.
        if state == MENU and prev_state != MENU:
            pygame.display.set_caption(WINDOW_TITLE)  # scenes overwrite the caption, so restore it on the way back
            pygame.mixer.music.load(menu_music)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # -1 means loop forever
            main_menu = _build_main_menu(menu_theme, start_scene, quit_game)

        prev_state = state

        screen.fill(DARK)

        if state == MENU:
            screen.blit(menu_bg, (0, 0))
            main_menu.update(events)
            main_menu.draw(screen)

        elif state == SCENE1:
            # scene1 loads its own music on entry, which auto-stops the menu track for us
            next_state = scene1(screen, clock)
            # cutscene always plays through to the end → mark complete on any non-menu return
            if next_state == SCENE2:
                mark_complete("scene1")
            state = next_state

        elif state == SCENE2:
            next_state = scene2(screen, clock)
            if next_state == SCENE3:
                # only the win path (transition to scene3) counts as completion;
                # death-restart and pause-exit don't unlock anything
                mark_complete("scene2")
            elif next_state == "restart":
                # pause menu's RESTART LEVEL — re-enter the same scene fresh
                next_state = SCENE2
            state = next_state

        elif state == SCENE3:
            # temporary holding screen so scene2's "scene3" return value doesn't
            # crash the state machine. teammates: drop your boss-fight scene in here.
            font  = pygame.font.Font(None, 48)
            msg   = font.render("Scene 3 — Coming soon (Boss Fight)", True, (255, 255, 255))
            small = pygame.font.Font(None, 28)
            hint  = small.render("ESC to return to menu", True, (160, 160, 160))
            screen.blit(msg,  msg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
            for ev in events:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    state = MENU

        elif state == SCENE4:
            next_state = scene4(screen, clock)
            if next_state == "victory":
                mark_complete(SCENE4)
                state = MENU
            elif next_state == "restart":
                state = SCENE4
            else:
                state = MENU

        # --- for scene6 ---
        elif state == SCENE6:
            # Call scene6 function
            next_state = scene6(screen, clock)
            state = MENU


        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
