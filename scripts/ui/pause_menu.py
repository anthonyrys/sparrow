from scripts import SCREEN_DIMENSIONS
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
            {'nav': NavContainer(self)}
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
                self.game.easing.create((self, 'global_y'), -SCREEN_DIMENSIONS[1] // 2, 10, 'ease_out', 1)

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

    def update(self):
        if self._root != self.root:
            self._root = self.root
            self.containers[self.root][self.current].rooted()
        
            self.global_x = -SCREEN_DIMENSIONS[0] // 2
            self.game.easing.create((self, 'global_x'), 0, 30, 'ease_out', 1)

            self.x, self.y = 0, 0

        self.containers[self.root][self.current].update()

    def render(self, surface):
        if not self.active:
            return
        
        self.containers[self.root][self.current].render(surface)
