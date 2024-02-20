from scripts import SCREEN_DIMENSIONS
from scripts.fonts import Fonts
from scripts.mixer import Sfx
from scripts.sprite import Sprite

from scripts.ui import Textbox
from scripts.utils import scale

import pygame
import json
import copy
import os

class Dialogue(Sprite):
    def __init__(self, friendly):
        image = pygame.image.load(os.path.join('resources', 'images', 'ui', 'dialogue', 'dialogue-background.png'))
        image = scale(image, 3)
        super().__init__((0, 0), image, friendly.index)

        self.rect = image.get_rect(center=(SCREEN_DIMENSIONS[0] // 2, SCREEN_DIMENSIONS[1] - 175))
        self.original_rect.topleft = self.rect.topleft

        self.friendly = friendly

        self.original_info = self.load()
        self.info = self.original_info.copy()

        self.current = None
        self.text = None
        self.images = None

        self.responses = {}
        self.responses_k = []
        self.responses_v = []

        self.pause = False
        self.waiting = False
        self.skipping = False

        self.y = -1
        self.s = 0
        self.i = 0
        self.tick = 0

        self.name = Fonts.create(self.info['font'], self.info['name'], 1.5, self.info['color'])

        self.next = scale(pygame.image.load(os.path.join('resources', 'images', 'ui', 'dialogue', 'dialogue-next.png')), 2)
        self.next_x, self.next_y = 0, 0
        self.next_alpha = 255

    def on_key_down(self, game, key):
        if key in game.player.keybinds['$interact']:
            if not self.pause and not self.waiting:
                self.skipping = True

            elif self.pause and self.waiting:
                if self.current['next'] is None and self.current['responses'] is None:
                    self.end(game)

                else:
                    if self.current['next']:
                        self.current = self.current['next']

                    elif self.current['responses']:
                        self.current = self.current['responses'][self.responses_k[self.s]]

                    if self.current['function']:
                        if self.current['function'][0] == 'flag':
                            game.player.npc_flags[self.current['function'][1]] = True

                    self.pause = False
                    self.waiting = False

                    self.text = ''
                    self.images = [0, {}]

                    self.i = 0

        elif key in game.player.keybinds['@dash']:
            self.end(game)

        elif key in game.player.keybinds['down']:
            self.y += 1
        elif key in game.player.keybinds['up']:
            self.y -= 1

    def on_key_up(self, game, key):
        if key in game.player.keybinds['$interact']:
            if self.skipping:
                self.skipping = False  
                
    def load(self):
        try:
            with open(os.path.join('resources', 'data', 'dialogue', self.friendly.area, f'{self.friendly.sprite_id.lower()}.json')) as t:
                data = json.load(t)    

        except FileNotFoundError:
            print(f'[LOAD_DIALOGUE] Dialogue "{self.friendly.sprite_id.lower()}" not found.')
            with open(os.path.join('resources', 'data', 'dialogue', f'default.json')) as t:
                data = json.load(t)   

        return data
    
    def start(self, game):
        self.info = copy.deepcopy(self.original_info)

        self.current = None
        for flag in self.info['trees'].keys():
            if flag in game.player.npc_flags.keys():
                self.current = self.info['trees'][flag]
                break

        if not self.current:
            self.current = self.info['trees']['default']

        self.text = ''
        self.images = [0, {}]

        self.responses = {}
        self.responses_k = []
        self.responses_v = []

        self.pause = False
        self.waiting = False
        self.skipping = False
        
        self.y = 0
        self.s = -1
        self.i = 0
        self.tick = 30

        self.next_x, self.next_y = 0, 0

        self.rect.y = SCREEN_DIMENSIONS[1]

        game.easing.create((self.rect, 'centery'), SCREEN_DIMENSIONS[1] - 175, 45, dt=1)
        game.ui.append(self)

    def end(self, game):
        self.friendly.interacting = False
        self.friendly.direction = self.friendly.original_direction

        game.camera.anchor_parent = game.player

        game.player.interact_npc = None
        game.player.cooldowns['interacted'] = 30

        game.ui.remove(self)
    
    def check(self, game, current):
        if 'prereq' not in current:
            return True
        
        prereq = current['prereq']

        if prereq[0] == 'flag':
            if prereq[1] not in game.player.npc_flags.keys():
                return False

        elif prereq[0] == 'min-level':
            if game.player.level < prereq[1]:
                return False
        
        elif prereq[0] == 'max-level':
            if game.player.level > prereq[1]:
                return False
        
        return True
    
    def update_text(self, game):
        self.tick -= (3 if self.skipping else 1) * game.raw_delta_time

        if self.tick > 0:
            return
        
        if self.pause:
            if not self.waiting:
                self.waiting = True

                self.next_alpha = 0
                self.next_x = -15
                
                game.easing.create((self, 'next_alpha'), 255, 30, dt=1)
                game.easing.create((self, 'next_x'), 0, 30, dt=1)

            if self.skipping and self.current['next']:
                self.on_key_down(game, game.player.keybinds['$interact'][0])
            
            return

        if self.i >= len(self.current['dialogue']):
            self.pause = True
            self.tick = self.info['delay']

            if self.current['responses']:
                y = 0
                empty = True

                for response in self.current['responses'].keys():
                    if not self.check(game, self.current['responses'][response]):
                        continue

                    textbox = Textbox((self.rect.right + 40, self.rect.top + 20 + y), 1, self.info['font'], response, 1)
                    self.responses[response] = textbox

                    y += textbox.image.get_height() * 2
                    empty = False

                if empty:
                    self.current['responses'] = None
                else:
                    self.responses_k = tuple(self.responses.keys())
                    self.responses_v = tuple(self.responses.values())

                    self.y = 0
                    self.s = -1
            
            elif self.current['next']:
                if not self.check(game, self.current['next']):
                    self.current['next'] = None

            return
        
        character = self.current['dialogue'][self.i]
        if character == ';':
            self.text = ''
            self.images[0] += 1

            self.i += 1

        else:
            self.tick = self.info['speed'] * (1 if character not in ('?', '!', '.', ',') else 3)

            self.text += self.current['dialogue'][self.i]
            self.images[1][self.images[0]] = Fonts.create(self.info['font'], self.text, color=self.info['color'])

            self.i += 1

            if self.skipping:
                Sfx.play(f'dialogue_{self.info["voice"]}-s', .2)
            else:
                Sfx.play(f'dialogue_{self.info["voice"]}', .25)

    def update_responses(self, game):
        if not self.current['responses'] or not self.pause:
            return
        
        k = self.y % len(self.responses)
        if self.s == k:
            return
        
        game.easing.create((self.responses_v[self.s].rect, 'x'), self.responses_v[self.s].original_rect.x, 10, 'ease_out', 1)
        self.s = k

        game.easing.create((self, 'next_y'), self.responses_v[self.s].rect.y + 2, 10, 'ease_out', 1)
        game.easing.create((self.responses_v[self.s].rect, 'x'), self.responses_v[self.s].original_rect.x + 10, 10, 'ease_out', 1)

    def update(self, game):
        if not self.friendly.interacting or not self.current:
            return
        
        self.update_text(game)
        self.update_responses(game)

    def render(self, surface):
        surface.blit(self.image, self.rect)
        surface.blit(self.name, self.name.get_rect(bottomleft=(self.rect.x + 30, self.rect.top + 4)))

        y = 0
        for textbox in self.images[1].values():
            surface.blit(textbox, (self.rect.x + 20, self.rect.top + 20 + y))
            y += textbox.get_height() * 1.5

        if self.waiting:
            self.next.set_alpha(self.next_alpha)

            if self.current['next']:
                surface.blit(self.next, self.next.get_rect(bottomright=(self.rect.right - 20 + self.next_x, self.rect.bottom - 20)))

            elif self.current['responses']:
                for response in self.responses_v:
                    response.image.set_alpha(self.next_alpha)
                    response.render(surface, (self.next_x, 0))

                surface.blit(self.next, self.next.get_rect(topright=(self.rect.right + 35 + self.next_x, self.next_y)))
