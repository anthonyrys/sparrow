def main():
    game = Game(clock, context)
    quit = False

    while not quit:
        quit = game.update()
        game.render()

        pygame.display.flip()

        # FPS is uncapped, but the game is designed for 60 FPS
        clock.tick()

if __name__ == '__main__':
    from scripts import (TITLE, VERSION, SCREEN_DIMENSIONS)
    from scripts.fonts import Fonts
    from scripts.game import Game
    from scripts.mixer import Sfx

    import moderngl
    import warnings
    import pygame
    import sys
    import os

    pygame.init()
    pygame.mixer.init()

    icon = pygame.image.load(os.path.join('resources', 'images', 'icon.png'))
    pygame.display.set_caption(f'{TITLE} v{VERSION}')
    pygame.display.set_icon(icon)
    pygame.mouse.set_visible(False)

    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)

        screen = pygame.display.set_mode(SCREEN_DIMENSIONS, pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN | pygame.SCALED)
        context = moderngl.create_context()

    clock = pygame.time.Clock()

    Sfx.init()
    Fonts.init()

    main()

    pygame.quit()
    pygame.mixer.quit()
    sys.exit()
