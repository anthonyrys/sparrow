from scripts import SCREEN_DIMENSIONS
from scripts.mixer import Sfx
from scripts.sprite import Sprite
from scripts.fonts import Fonts

from scripts.utils import load_spritesheet, get_bezier_point, bezier_presets

import pygame
import os

class Card(Sprite):
    def __init__(self, position, index, face, talent, stacks):
        images = load_spritesheet(os.path.join('resources', 'images', 'ui', 'card', f'{talent.rarity}.png'))
        super().__init__(position, images[face], index)

        self.images = images

        self.face = face
        self.talent = talent
        self.talent_stacks = stacks

        self.load()

        self.to_time = [0, 0]
        self.to_type = None
        self.to_bezier = bezier_presets['ease_out']
        self.to_x = (0, 0)
        self.to_y = (0, 0)

        self.flipping = False
        self.flip_count = 0
        self.flip_time = [0, 0]
        self.flip_dir = 0

        self.selected = False
        self.deselected_y = SCREEN_DIMENSIONS[1] / 2 - self.rect.height / 2
        self.selected_y = SCREEN_DIMENSIONS[1] / 2 - self.rect.height / 1.75

        self.d_count = None

    def load(self):
        # Icon
        try:
            icon = pygame.image.load(os.path.join('resources', 'images', 'ui', 'card', f'icon-{self.talent.__name__.lower()}.png')).convert_alpha()
        except FileNotFoundError:
            icon = pygame.image.load(os.path.join('resources', 'images', 'ui', 'card', f'icon-default.png')).convert_alpha()

        icon = pygame.transform.scale(icon, (icon.get_width() * 4, icon.get_height() * 4))
        center = [self.images[1].get_width() / 2, 122]
        if self.talent.rarity == 'rare':
            center[1] += 21

        self.images[1].blit(icon, icon.get_rect(center=center))

        # Title
        string = ''.join(map(lambda x: x if x.islower() else " " + x, self.talent.__name__))
        if self.talent_stacks != None:
            string += f' {["I", "II", "III", "IV", "V"][self.talent_stacks]}'

        title = Fonts.create('m3x6', string, 1, (53, 52, 65))
        center = [self.images[1].get_width() / 2, 42]
        if self.talent.rarity == 'rare':
            center[1] += 22

        self.images[1].blit(title, title.get_rect(midtop=center))

        # Label
        string = self.talent.category[0].upper()
        if self.talent.stackable:
            string += f' | {self.talent.stackable}'

        label = Fonts.create('m3x6', string, 1, (113, 113, 113))
        center = [self.images[1].get_width() / 2, 183]
        if self.talent.rarity == 'rare':
            center[1] += 23

        self.images[1].blit(label, label.get_rect(midtop=center))    

        # Description
        descriptions = self.talent.description.split(';')
        center = [self.images[1].get_width() / 2, 205]
        if self.talent.rarity == 'rare':
            center[1] += 23

        for description in descriptions:
            surface = Fonts.create('m3x6', description, 1, (53, 52, 65))

            self.images[1].blit(surface, surface.get_rect(midtop=center)) 
            center[1] += surface.get_height() + 6

    def flip(self, dir=0, t=14):
        self.flip_dir = dir
        if dir == 0:
            Sfx.play('card_flip')
            self.flip_time = [-t, t]
        else:
            self.flip_time = [t, t]

        self.flipping = True

    def update(self, game):
        selected = game.card == self and game.card_active
        if not self.selected and selected:
            self.to_y = (self.position[1], self.selected_y)
            self.to_type = 'y'
            self.to_time = [0, 15]

        elif self.selected and not selected:
            self.to_y = (self.position[1], self.deselected_y)
            self.to_type = 'y'
            self.to_time = [0, 15]

        self.selected = selected

        if self.to_time[0] < self.to_time[1]:
            abs_prog = self.to_time[0] / self.to_time[1]

            if self.to_type == 'y':
                dist = self.to_y[1] - self.to_y[0]
                self.rect.y = self.to_y[0] + dist * get_bezier_point(abs_prog, *self.to_bezier)

            elif self.to_type == 'x':
                dist = self.to_x[1] - self.to_x[0]
                self.rect.x = self.to_x[0] + dist * get_bezier_point(abs_prog, *self.to_bezier)

            self.to_time[0] += 1 * game.raw_delta_time

            if self.to_time[0] > self.to_time[1]:
                self.to_time[0] = self.to_time[1]

                if self.to_type == 'y':
                    self.rect.y = self.to_y[1]
                elif self.to_type == 'x':
                    self.rect.x = self.to_x[1]

        if self.flipping:
            if self.flip_dir == 0:
                self.flip_time[0] += 1 * game.raw_delta_time
            else:
                self.flip_time[0] -= 1 * game.raw_delta_time

            if self.flip_time[0] < 0:
                if self.face != 0:
                    self.face = 0
                    self.image = self.images[0]

            elif self.flip_time[0] > 0:
                if self.face != 1: 
                    self.face = 1
                    self.image = self.images[1]
            
            if self.flip_dir == 0 and self.flip_time[0] > self.flip_time[1]:
                self.flipping = False
            elif self.flip_dir != 0 and self.flip_time[0] < -self.flip_time[1]:
                self.flipping = False

        if self.flip_count:
            self.flip_count -= 1 * game.raw_delta_time

            if self.flip_count <= 0:
                self.flip_count = None
                self.flip()

        if self.d_count:
            self.d_count -= 1 * game.raw_delta_time

            if self.d_count <= 0:
                game.ui.remove(self)

    def render(self, surface):
        image = self.image
        rect = self.rect

        if self.flipping:
            abs_prog = abs(self.flip_time[0]) / self.flip_time[1]
            width = self.original_image.get_width() * get_bezier_point(abs_prog, *bezier_presets['ease_out'])

            image = pygame.transform.scale(self.image, (width, self.image.get_height()))
            rect = image.get_rect(center=self.rect.center)

        surface.blit(image, rect)
