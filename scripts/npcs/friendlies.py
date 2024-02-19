from scripts.fonts import Fonts
from scripts.sprite import Sprite

from scripts.ui import Dialogue
from scripts.utils import generate_import_dict, scale

import pygame
import os

FRIENDLY_PATH = os.path.join('resources', 'images', 'friendlies')

class Friendly(Sprite):
    def __init__(self, position, image, index, interact='Talk'):
        super().__init__(position, image, index)

        self.target = False

        self.interact_type = interact
        self.interacting = False

        frame = scale(pygame.image.load(os.path.join('resources', 'images', 'ui', 'prompt.png')), 2)
        text = Fonts.create('m3x6', interact)

        prompt = pygame.Surface((frame.get_width() * 1.3 + text.get_width(), frame.get_height())).convert_alpha()
        prompt.set_colorkey((0, 0, 0))

        prompt.blit(frame, (0, 0))
        prompt.blit(text, text.get_rect(midleft=(frame.get_width() * 1.3, prompt.get_height() // 2 + 2)))

        self.prompt = prompt
        self.prompt_rect = prompt.get_rect()

        self.dialogue = Dialogue(self)

        self.direction = -1
        self.original_direction = self.direction

    def interact(self, game):
        self.interacting = True
        self.target = False

        self.dialogue.start(game)

    def outline(self, surface, size=3, color=(255, 255, 255)):
        image = pygame.Surface(self.image.get_size())
        image.set_colorkey((0, 0, 0))

        for point in self.mask.outline():
            image.set_at(point, color)

        for i in range(size):
            surface.blit(image, (self.rect.x - i, self.rect.y))
            surface.blit(image, (self.rect.x + i, self.rect.y))

            surface.blit(image, (self.rect.x, self.rect.y - i))
            surface.blit(image, (self.rect.x, self.rect.y + i))

    def update(self, game):
        self.key = pygame.key.name(game.player.keybinds['$interact'][0])
        self.image = pygame.transform.flip(self.original_image, True, False).convert_alpha() if self.direction > 0 else self.original_image
      
    def render(self, surface):
        if self.target:
            self.outline(surface)

            key = Fonts.create('m3x6', self.key)
            self.prompt_rect.center = (self.rect.centerx, self.rect.top - 20)

            surface.blit(self.prompt, self.prompt_rect)
            surface.blit(key, key.get_rect(midleft=(self.prompt_rect.left + 7, self.prompt_rect.centery + 1)))

        surface.blit(self.image, self.image.get_rect(center=self.rect.center))

class Dummy(Friendly):
    def __init__(self, position, index):
        image = pygame.image.load(os.path.join(FRIENDLY_PATH, 'dummy', 'dummy.png')).convert_alpha()
        image = scale(image, 2)

        super().__init__(position, image, index)

class MadDummy(Friendly):
    def __init__(self, position, index):
        image = pygame.image.load(os.path.join(FRIENDLY_PATH, 'mad-dummy', 'mad-dummy.png')).convert_alpha()
        image = scale(image, 2)

        super().__init__(position, image, index)

FRIENDLIES = generate_import_dict('Friendly')
