import os
import pygame
import pygame_menu
from settings import WIDTH, HEIGHT, FPS, ASSETS_DIR

PANEL_W = 440
PANEL_H = 340


def run_pause(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """Show a pause menu on top of a blurred snapshot of the game.

    The blurred frame is computed once before the loop since nothing underneath
    changes while paused. The menu uses the same theme as the main menu so
    the style is consistent across the whole game.

    Returns "resume", "restart", or "menu" — the calling scene decides what
    to do with each (resume = continue, restart = re-enter the scene fresh,
    menu = bail out to the main menu).
    """
    # cheap blur: downscale 6x then upscale back. computed once because nothing under us changes while paused.
    frozen  = screen.copy()
    small   = pygame.transform.smoothscale(frozen, (WIDTH // 6, HEIGHT // 6))
    blurred = pygame.transform.smoothscale(small,  (WIDTH, HEIGHT))

    # swap to menu music while paused. mixer.music only has one channel, so this
    # replaces the level track — the calling scene has to reload its own music on resume.
    pygame.mixer.music.load(os.path.join(ASSETS_DIR, "music", "menu.wav"))
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

    # buttons write into result[0]; the loop polls it. wrapped in a list so the
    # nested do_resume/do_menu closures can mutate it without `nonlocal`.
    result = [None]

    def do_resume():
        result[0] = "resume"

    def do_restart():
        result[0] = "restart"

    def do_menu():
        result[0] = "menu"

    # same theme as the main menu so the styling stays consistent
    theme = pygame_menu.Theme(
        background_color=(8, 12, 30, 220),
        title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
        widget_font=pygame_menu.font.FONT_8BIT,
        widget_font_color=(200, 220, 255),
        widget_font_size=20,
        selection_color=(100, 200, 255),
    )

    menu = pygame_menu.Menu(
        "",
        PANEL_W, PANEL_H,
        theme=theme,
        position=(50, 50, True),
        center_content=False,  # top-aligned widgets — lets us shrink PANEL_H without re-centering text
    )
    menu.add.vertical_margin(10)
    menu.add.label("PAUSED", font_size=28, font_color=(255, 255, 255))
    menu.add.vertical_margin(30)
    menu.add.button("RESUME",         do_resume)
    menu.add.vertical_margin(16)
    menu.add.button("RESTART",  do_restart)
    menu.add.vertical_margin(16)
    menu.add.button("EXIT TO MENU",   do_menu)

    while result[0] is None:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            # ESC is a quick "unpause" shortcut so you don't have to click the resume button
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                result[0] = "resume"

        screen.blit(blurred, (0, 0))
        menu.update(events)
        menu.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    return result[0]
