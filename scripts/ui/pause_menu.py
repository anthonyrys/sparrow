from scripts import SCREEN_DIMENSIONS
from scripts.fonts import Fonts
from scripts.mixer import Sfx

from scripts.ui import Menu, Container, Textbox
from scripts.utils import scale

import pygame
import os

MENU_PATH = os.path.join('resources', 'images', 'ui', 'menus')

class NavContainer(Container):
    def __init__(self, menu):
        super().__init__(menu)

        self.nav = {
            'continue': Textbox((0, 0), 0, 'm3x6', 'Continue', 1.5),
            'settings': Textbox((0, 0), 0, 'm3x6', 'Settings', 1.5),
            'exit': Textbox((0, 0), 0, 'm3x6', 'Exit', 1.5)
        }

        self.nav_n = len(self.nav)
        self.nav_k = tuple(self.nav.keys())
        self.nav_v = tuple(self.nav.values())
        self.i = -1
        
        i = -(self.nav_n // 2)
        for v in self.nav_v:
            x = -v.rect.width // 2
            y = SCREEN_DIMENSIONS[1] // 2 + i * (v.rect.height * 1.5)

            v.rect.topleft = (x, y)
            v.original_rect.topleft = (x, y)

            i += 1
            
        self.pointer = scale(pygame.image.load(os.path.join(MENU_PATH, 'nav-pointer.png')), 3)
        self.pointer_x = 0
        self.pointer_y = 0

    def select(self):
        if self.nav_k[self.i] == 'exit':
            self.menu.game.quit = True
            return
        
        if self.nav_k[self.i] == 'continue':
            self.menu.on_key_down(pygame.K_ESCAPE)

        else:
            self.menu.root = 1
            self.menu.current = self.nav_k[self.i]

        Sfx.stop('menu_back')
        Sfx.play('menu_forward')

    def update(self):
        k = self.menu.y % self.nav_n
        if self.i == k:
            return
        
        self.menu.game.easing.create((self.nav_v[self.i].rect, 'x'), self.nav_v[self.i].original_rect.x, 10, 'ease_out', 1)
        self.i = k

        self.menu.game.easing.create((self, 'pointer_x'), self.nav_v[self.i].rect.left - 30, 10, 'ease_out', 1)
        self.menu.game.easing.create((self, 'pointer_y'), self.nav_v[self.i].rect.y - 2, 10, 'ease_out', 1)
        self.menu.game.easing.create((self.nav_v[self.i].rect, 'x'), self.nav_v[self.i].original_rect.x + 15, 10, 'ease_out', 1)

    def render(self, surface):
        position = [self.pointer_x + self.menu.global_x, self.pointer_y + self.menu.global_y]
        surface.blit(self.pointer, position)

        for k in self.nav.values():
            k.render(surface, (self.menu.global_x, self.menu.global_y))


class SettingsContainer(Container):
    def __init__(self, menu):
        super().__init__(menu)

        self.pointer = scale(pygame.image.load(os.path.join(MENU_PATH, 'pause', 'settings','settings-pointer.png')), 2)
        self.pointer_x = 0
        self.pointer_y = 0

        self.settings = {
            'volume': Textbox((0, 0), 0, 'm3x6', 'Volume:', 1.5),
            'fps': Textbox((0, 0), 0, 'm3x6', 'Frame Limit:', 1.5)
        }

        self.settings_n = len(self.settings)
        self.settings_k = tuple(self.settings.keys())
        self.settings_v = tuple(self.settings.values())

        self.settings_o = {
            'volume': tuple(v for v in range(0, 105, 5)),
            'fps': (30, 60, 120, 'uncapped')
        }

        self.settings_s = {
            'volume': (self.settings_o['volume'][20], 20),
            'fps': (self.settings_o['fps'][3], 3)
        }

        self.settings_d = {
            'volume': (Sfx, 'GLOBAL_VOLUME'),
            'fps': (self.menu.game, 'fps_cap')
        }

        self.i = -1  
    
        i = -(self.settings_n // 2)
        for v in self.settings_v:
            x = -v.rect.width // 2
            y = SCREEN_DIMENSIONS[1] // 2 + i * (v.rect.height * 1.5)

            v.rect.topleft = (x, y)
            v.original_rect.topleft = (x, y)

            i += 1

    def on_key_down(self, key):
        if key not in self.menu.game.player.keybinds['left'] and key not in self.menu.game.player.keybinds['right']:
            return
        
        setting = self.settings_k[self.i]
        v = self.settings_s[setting][1]
        if key in self.menu.game.player.keybinds['left']:
            v -= 1
        elif key in self.menu.game.player.keybinds['right']:
            v += 1

        v %= len(self.settings_o[setting])
        self.settings_s[setting] = (self.settings_o[setting][v], v)
        
        value = self.settings_o[setting][v]
        if setting == 'fps' and value == 'uncapped':
            value = 0
        elif setting == 'volume':
            value /= 100

        setattr(self.settings_d[setting][0], self.settings_d[setting][1], value)

    def back(self):
        self.menu.root = 0
        self.menu.current = 'nav'

        Sfx.play('menu_back')  
    
    def update(self):
        k = self.menu.y % self.settings_n
        if self.i != k:
            self.menu.game.easing.create((self.settings_v[self.i].rect, 'x'), self.settings_v[self.i].original_rect.x, 10, 'ease_out', 1)
            self.i = k

            self.menu.game.easing.create((self, 'pointer_x'), self.settings_v[self.i].rect.left - 15, 10, 'ease_out', 1)
            self.menu.game.easing.create((self, 'pointer_y'), self.settings_v[self.i].rect.y + 2, 10, 'ease_out', 1)
            self.menu.game.easing.create((self.settings_v[self.i].rect, 'x'), self.settings_v[self.i].original_rect.x + 10, 10, 'ease_out', 1)

    def render(self, surface):
        position = (self.pointer_x + self.menu.global_x, self.pointer_y + self.menu.global_y)
        surface.blit(self.pointer, position)

        for i, k in self.settings.items():
            k.render(surface, (self.menu.global_x, self.menu.global_y))
            
            decorator = '%' if i == 'volume' else ''
            color = (255, 255, 255) if i == self.settings_k[self.i] else (150, 150, 150)

            image = Fonts.create('m3x6', f'{self.settings_s[i][0]}{decorator}', color=color)
            pos = (k.rect.right + 10 + self.menu.global_x, k.rect.centery + self.menu.global_y)

            surface.blit(image, image.get_rect(midleft=pos))


class PauseMenu(Menu):
    def __init__(self, game):
        super().__init__(game)

        self.active = False

        self.x, self.y = 0, 0
        self.root, self._root = 0, 0
        self.current = 'nav'

        self.global_x = SCREEN_DIMENSIONS[0] // 2
        self.global_y = -SCREEN_DIMENSIONS[1] // 2

        self.containers = [
            # Root 0
            {'nav': NavContainer(self)},
            {'settings': SettingsContainer(self)}
        ]

    def on_key_down(self, key):
        if self.game.in_menu and not self.active:
            return
        
        if self.game.in_cards:
            return
        
        if self.game.player.interact_npc:
            return
        
        if key == pygame.K_ESCAPE:
            self.active = not self.active
            self.game.in_menu = self.active

            if self.active:
                self.game.easing.create((self.game, 'dim'), .75, 10, 'linear', 1)
                self.game.easing.create((self, 'global_y'), 0, 30, 'ease_out', 1)

                self.x, self.y = 0, 0
                self.root = 0
                self.current = 'nav'

                self.containers[self.root][self.current].rooted()

            else:
                self.game.easing.create((self.game, 'dim'), 0, 10, 'linear', 1)
                self.game.easing.create((self, 'global_y'), -SCREEN_DIMENSIONS[0] // 2, 30, 'ease_out', 1)

        if not self.active:
            return
        
        if key in self.game.player.keybinds['up']:
            self.y -= 1
        elif key in self.game.player.keybinds['down']:
            self.y += 1

        if key in self.game.player.keybinds['left']:
            self.x -= 1
        elif key in self.game.player.keybinds['right']:
            self.x += 1

        if key in self.game.player.keybinds['$interact']:
            self.containers[self.root][self.current].select()

        if key in self.game.player.keybinds['@dash']:
            self.containers[self.root][self.current].back()

        self.containers[self.root][self.current].on_key_down(key)

    def update(self):
        if self._root != self.root:
            self._root = self.root
            self.containers[self.root][self.current].rooted()
        
            self.global_y = -SCREEN_DIMENSIONS[0] // 2
            self.game.easing.create((self, 'global_y'), 0, 30, 'ease_out', 1)

            self.x, self.y = 0, 0

        self.containers[self.root][self.current].update()

    def render(self, surface):
        if not self.active:
            return
        
        self.containers[self.root][self.current].render(surface)
