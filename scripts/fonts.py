from scripts.utils import load_spritesheet

import pygame
import os

class Fonts:
    FONT_PATH = os.path.join('resources', 'images', 'fonts')

    FONT_KEYS = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.', ':', ',', ';', '\'', '\"', '(', '!', '?', ')', '+', '-', '*', '/', '='
    ]

    fonts = {
        'default': {
            'info': {
                'key_spacing': [10, 32],
                'key_padding': 5,

                'key_specials': {
                    'g': 11,
                    'p': 11,
                    'q': 11,
                    'y': 11,

                    ':': -4
                }
            },

            'letters': {}
        }
    }

    def init():
        for font_file in os.listdir(Fonts.FONT_PATH):
            name = font_file.split('.')[0]

            images = load_spritesheet(os.path.join(Fonts.FONT_PATH, font_file))

            for index, key in enumerate(Fonts.FONT_KEYS):
                Fonts.fonts[name]['letters'][key] = images[index]

    def create(font, text, size=.5, color=(255, 255, 255)):
        text = str(text).lower()

        surface_size = [0, 0]
        images = []

        for letter in text:
            image = None
            if letter == ' ':
                image = pygame.Surface((Fonts.fonts[font]['info']['key_spacing'][0], Fonts.fonts[font]['info']['key_spacing'][1])).convert_alpha()
                image.set_colorkey((0, 0, 0))

            else:
                image = Fonts.fonts[font]['letters'][letter].copy()

            surface_size[0] += image.get_width() + Fonts.fonts[font]['info']['key_padding']
            if image.get_height() > surface_size[1]:
                surface_size[1] += image.get_height() * 2

            image = pygame.transform.scale(image, (image.get_width() * size, image.get_height() * size)).convert_alpha()
            image = pygame.mask.from_surface(image).to_surface(
                setcolor=color,
                unsetcolor=(0, 0, 0)
            ).convert_alpha()

            images.append(image)

        surface = pygame.Surface((surface_size[0] * size, surface_size[1] * size)).convert_alpha()
        surface.set_colorkey((0, 0, 0))

        x = 0
        for image, letter in zip(images, text):
            if letter in Fonts.fonts[font]['info']['key_specials'].keys():
                surface.blit(image, (x, (Fonts.fonts[font]['info']['key_specials'][letter] * size)))
                x += image.get_width() + (Fonts.fonts[font]['info']['key_padding'] * size)
                continue

            surface.blit(image, (x, 0))
            x += image.get_width() + (Fonts.fonts[font]['info']['key_padding'] * size)

        return surface
