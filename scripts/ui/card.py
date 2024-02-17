from scripts import SCREEN_DIMENSIONS
from scripts.mixer import Sfx
from scripts.sprite import Sprite
from scripts.fonts import Fonts

from scripts.systems import TALENTS
from scripts.utils import load_spritesheet, bezier_presets, get_bezier_point, scale
from scripts.visual_fx import PolygonParticle

import pygame
import random
import os
import re

class Card(Sprite):
    def __init__(self, position, index, face, talent, stacks):
        images = load_spritesheet(os.path.join('resources', 'images', 'ui', 'card', f'{talent.rarity}.png'))
        super().__init__(position, images[face], index)

        self.images = images

        self.face = face
        self.talent = talent
        self.talent_stacks = stacks

        self.cache = self.load()

        self.flipping = False
        self.flip_count = 0
        self.flip_time = [0, 0]
        self.flip_dir = 0

        self.image_pulse_frames = [0, 0]
        self.image_pulse_color = (0, 0, 0)
        self.image_pulse_bezier = bezier_presets['ease_in']
        self.image_pulse_dt_time = 0

        self.selected = False
        self.deselected_y = SCREEN_DIMENSIONS[1] / 2 - self.rect.height / 2
        self.selected_y = SCREEN_DIMENSIONS[1] / 2 - self.rect.height / 1.75

        self.d_count = None

    def load(self):
        cache = {} 
        cache['talent'] = self.talent

        # Icon
        try:
            icon = pygame.image.load(os.path.join('resources', 'images', 'ui', 'card', self.talent.area, f'icon-{self.talent.__name__.lower()}.png')).convert_alpha()
        except FileNotFoundError:
            icon = pygame.image.load(os.path.join('resources', 'images', 'ui', 'card', f'icon-default.png')).convert_alpha()

        icon = scale(icon, 4)
        center = [self.images[1].get_width() / 2, 122]
        if self.talent.rarity == 'rare':
            center[1] += 21

        self.images[1].blit(icon, icon.get_rect(center=center))
        cache['icon'] = icon

        # Title
        string = ''.join(map(lambda x: x if x.islower() else ' ' + x, self.talent.__name__)).lstrip()

        cache['stacks'] = None
        if self.talent_stacks != None:
            string += f' {["I", "II", "III", "IV", "V"][self.talent_stacks]}'
            cache['stacks'] = self.talent_stacks + 1

        title = Fonts.create('m3x6', string, 1, (53, 52, 65))
        center = [self.images[1].get_width() / 2, 42]
        if self.talent.rarity == 'rare':
            center[1] += 22

        self.images[1].blit(title, title.get_rect(midtop=center))

        cache['name'] = string

        # Label
        string = self.talent.category[0].upper()
        if self.talent.stackable:
            string += f' | {self.talent.stackable}'

        label = Fonts.create('m3x6', string, 1, (113, 113, 113))
        center = [self.images[1].get_width() / 2, 183]
        if self.talent.rarity == 'rare':
            center[1] += 23

        self.images[1].blit(label, label.get_rect(midtop=center))    
        cache['label'] = label

        # Description
        descriptions = self.talent.description.split(';')
        center = [self.images[1].get_width() / 2, 205]
        if self.talent.rarity == 'rare':
            center[1] += 23

        cache['description'] = []
        for description in descriptions:
            cache['description'].append(description)
            surface = Fonts.create('m3x6', re.sub(r'<|>', '', description), 1, (53, 52, 65))

            self.images[1].blit(surface, surface.get_rect(midtop=center)) 
            center[1] += surface.get_height() + 6

        return cache

    def burst(self, game):
        # Particles
        particles = []
        
        center = self.get_position('center')
        h = self.image.get_height()
        for i in range(random.randint(5, 8)):
            start = [*center]
            start[1] += random.randint(-h // 3, h // 3)

            position = [*start]
            position[0] += random.randint(100, 200) if i % 2 != 0 else random.randint(-200, -100)
            position[1] += random.randint(-75, -25)

            size = random.randint(3, 6)

            particle = PolygonParticle(
                self.index + 1, random.randint(45, 75),
                [start, position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=(200, 185, 120), beziers=['ease_out', 'ease_in'], delta_type=1, gravity=-1
            )

            particle.use_entity_surface = False
            particles.append(particle)

        game.particles.extend(particles)

    def flip(self, dir=0, t=14, l=0):
        self.flip_dir = dir
        if dir == 0:
            Sfx.play('card_flip')
            self.flip_time = [-t, t]
        else:
            Sfx.play('card_flip', 1.0 - 0.125 * l)
            self.flip_time = [t, t]

        self.flipping = True

    def update(self, game):
        selected = game.card_manager.card == self and game.card_manager.active
        if not self.selected and selected:
            game.easing.create((self.rect, 'y'), self.selected_y, 15, 'ease_out', 1)

        elif self.selected and not selected:
            game.easing.create((self.rect, 'y'), self.deselected_y, 15, 'ease_out', 1)

        self.selected = selected

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

                    if self.flip_dir == 0:
                        if self.talent.rarity == 'rare':
                            self.burst(game)

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

        if self.image_pulse_frames[0] > 0:
            if self.image_pulse_dt_time == 0:
                self.image_pulse_frames[0] -= 1 * game.delta_time
            else:
                self.image_pulse_frames[0] -= 1 * game.raw_delta_time
                
    def render(self, surface):
        image = self.image
        rect = self.rect

        if self.flipping:
            abs_prog = abs(self.flip_time[0]) / self.flip_time[1]
            width = self.original_image.get_width() * get_bezier_point(abs_prog, *bezier_presets['ease_out'])

            image = pygame.transform.scale(self.image, (width, self.image.get_height()))
            rect = image.get_rect(center=self.rect.center)

        surface.blit(image, rect)

        if self.image_pulse_frames[0] > 0:
            pulse_image = pygame.mask.from_surface(image).to_surface(setcolor=self.image_pulse_color, unsetcolor=(0, 0, 0, 0))
            pulse_image.set_alpha(255 * get_bezier_point((self.image_pulse_frames[0] / self.image_pulse_frames[1]), *self.image_pulse_bezier))

            surface.blit(pulse_image, pulse_image.get_rect(center=self.rect.center))

class CardManager(object):
    def __init__(self, game):
        self.game = game

        self.active = False
        self.flags = {'specific': None}

        self.cards = []
        self.card = None
        self.card_i = 0

    def on_key_down(self, key):
        if not self.game.in_cards or not self.active:
            return
        
        if key in self.game.player.keybinds['$interact']:
            self.active = False
            for card in self.cards:
                card.flip(1, 14, len(self.cards))

            color = (240, 240, 180) if self.card.talent.rarity == 'rare' else (255, 255, 255)
            self.card.image_pulse_color = color
            self.card.image_pulse_frames = [15, 15]

            self.game.timers['card_select'] = [15, 1, self.select, []]

        else:
            if key in self.game.player.keybinds['left']:
                self.card_i -= 1
                if self.card_i < 0:
                    self.card_i = len(self.cards) - 1

            elif key in self.game.player.keybinds['right']:
                self.card_i += 1
                if self.card_i >= len(self.cards):
                    self.card_i = 0

            self.card = self.cards[self.card_i]

    def on_key_up(self, key):
        ...

    def generate(self):
        c_pool = list(TALENTS['generic']['common'].values())
        r_pool = list(TALENTS['generic']['rare'].values())
        s_pool = {}

        for talent in self.game.player.talents:
            s_pool[talent.__class__] = talent.stacks

            if not talent.stackable:
                if talent.rarity == 'rare':
                    r_pool.remove(talent.__class__)
                else:
                    c_pool.remove(talent.__class__)
            else:
                if talent.stacks >= talent.stackable:
                    if talent.rarity == 'rare':
                        r_pool.remove(talent.__class__)
                    else:
                        c_pool.remove(talent.__class__)  

        if self.flags['specific'] and self.flags['specific'] not in s_pool:
            if self.flags['specific'].stackable:
                s_pool[self.flags['specific']] = 0
            
        if len(c_pool) < 3:
            return -1
    
        choices = []
        has_rare = False

        r_count = len(r_pool)
        for _ in range(3):
            if random.uniform(0, 1.0) <= TALENTS['R_RARITY'] and r_count > 0:
                pool = r_pool
                r_count -= 1

                has_rare = True

            else:
                pool = c_pool

            talent = random.choice(pool)
            while talent in choices or talent == self.flags['specific']:
                talent = random.choice(pool)
            
            if talent not in s_pool and talent.stackable:
                s_pool[talent] = 0

            choices.append(talent)

        if self.flags['specific']:
            choices.append(self.flags['specific'])

        cards = tuple(Card((0, -500), 1, 0, c, s_pool.get(c, None)) for c in choices)

        self.game.delta_time_multipliers['card_spawn'] = [0, False, [1, [0, 75], 'ease_in']]

        self.game.easing.create((self.game, 'dim'), .95, 75, 'ease_out', 1, 50)

        p = 50
        x = (SCREEN_DIMENSIONS[0] / 2) - (sum(c.image.get_width() for c in cards) + (len(cards) - 1) * p) / 2

        i = 0
        for card in cards:
            card.rect.x = x
            
            self.game.easing.create((card.rect, 'y'), (SCREEN_DIMENSIONS[1] / 2) - card.rect.height / 2, 80, 'ease_out', 1, 100)
            card.flip_count = 100 + i * 25

            i += 1
            x += card.image.get_width() + p

        self.game.in_cards = True
        self.cards = tuple(cards)

        self.card_i = len(self.cards) // 2
        self.card = self.cards[self.card_i]

        self.game.timers['card_add'] = [100, 1, self.game.ui.extend, ([cards])]
        self.game.timers['card_start'] = [200 + i * 25, 1, setattr, [self, 'active', True]]

        return has_rare
    
    def select(self):
        for card in self.cards:
            y = -500 if self.card != card else SCREEN_DIMENSIONS[1] + 50
            self.game.easing.create((card.rect, 'y'), y, 60, 'ease_in', 1)
            card.d_count = 60

        self.game.in_cards = False

        if self.card.talent == self.flags['specific']:
            self.flags['specific'] = None

        if self.card.talent.stackable:
            found = False
            for talent in self.game.player.talents:
                if self.card.talent == talent.__class__:
                    talent.stack()
                    found = True
                    break

            if not found:
                talent = self.card.talent(self.game.player)
                self.game.player.talents.append(talent)

        else:
            talent = self.card.talent(self.game.player)
            self.game.player.talents.append(talent)

        self.game.menus['player'].containers[1]['talents'].add(self.card.cache)

        del self.game.delta_time_multipliers['card_spawn']
        self.game.delta_time_multipliers['card_select'] = [1, False, [0, [0, 75], 'ease_in']]

        self.game.easing.create((self.game, 'dim'), 0, 50, 'ease_in', 1)
