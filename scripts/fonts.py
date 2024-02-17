from scripts.utils import load_spritesheet

import pygame
import os

class Fonts:
    FONT_PATH = os.path.join('resources', 'images', 'fonts')
    FONT_KEYS = tuple(map(str, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!?,.;:\'\"/|\_()[]{}<>@#$%+-*=^&'))

    fonts = {
        'm3x6': {
            'spacing': 2,
            'letters': {}
        }
    }

    colors = {
        'g': (0, 200, 125),
    }

    def init():
        for font_file in os.listdir(Fonts.FONT_PATH):
            name = font_file.split('.')[0]

            images = load_spritesheet(os.path.join(Fonts.FONT_PATH, font_file))

            for index, key in enumerate(Fonts.FONT_KEYS):
                Fonts.fonts[name]['letters'][key] = images[index]

    def create(font, text, size=1, color=(255, 255, 255)):
        surface_size = [0, 0]
        images = []
        current_color = None

        for i, letter in enumerate(str(text)):
            if str(text)[i - 1] == '~':
                if current_color:
                    continue
                
            if letter == '~':
                if not current_color:
                    current_color = Fonts.colors[str(text)[i + 1]]
                else:
                    current_color = None

                continue

            image = None
            if letter == ' ':
                image = pygame.Surface((Fonts.fonts[font]['spacing'] * 2, Fonts.fonts[font]['letters']['a'].get_height())).convert_alpha()
                image.set_colorkey((0, 0, 0))

            else:
                image = Fonts.fonts[font]['letters'][letter].copy()

            surface_size[0] += (image.get_width() + Fonts.fonts[font]['spacing'])
            if image.get_height() > surface_size[1]:
                surface_size[1] += image.get_height()

            image = pygame.transform.scale(image, (image.get_width() * size, image.get_height() * size)).convert_alpha()
            
            c = color if not current_color else current_color
            image = pygame.mask.from_surface(image).to_surface(setcolor=c, unsetcolor=(0, 0, 0)).convert_alpha()

            images.append(image)

        surface = pygame.Surface((surface_size[0] * size, surface_size[1] * size)).convert_alpha()
        surface.set_colorkey((0, 0, 0))

        x = 0
        for image, letter in zip(images, str(text)):
            surface.blit(image, (x, 0))
            x += image.get_width() + (Fonts.fonts[font]['spacing'] * size)

        return surface
