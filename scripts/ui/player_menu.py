from scripts import SCREEN_DIMENSIONS
from scripts.fonts import Fonts
from scripts.mixer import Sfx

from scripts.ui import Menu, Container, Textbox
from scripts.utils import scale

import pygame
import os
import re

MENU_PATH = os.path.join('resources', 'images', 'ui', 'menus')

class NavContainer(Container):
    def __init__(self, menu):
        super().__init__(menu)

        self.nav = {
            'talents': Textbox((0, 0), 0, 'm3x6', 'Talents', 1.5),
            'stats': Textbox((0, 0), 0, 'm3x6', 'Stats', 1.5)
        }
        
        self.nav_n = len(self.nav)
        self.nav_k = tuple(self.nav.keys())
        self.nav_v = tuple(self.nav.values())
        self.i = -1
        
        i = -(self.nav_n // 2)
        for v in self.nav_v:
            x = 80
            y = SCREEN_DIMENSIONS[1] // 2 + i * (v.rect.height * 1.5)

            v.rect.topleft = (x, y)
            v.original_rect.topleft = (x, y)

            i += 1
            
        self.pointer = scale(pygame.image.load(os.path.join(MENU_PATH, 'nav-pointer.png')), 3)
        self.pointer_x = 50
        self.pointer_y = self.nav_v[self.i].rect.y

    def select(self):
        if self.nav_k[self.i][0] == '_':
            return
        
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

        self.menu.game.easing.create((self, 'pointer_y'), self.nav_v[self.i].rect.y - 2, 10, 'ease_out', 1)
        self.menu.game.easing.create((self.nav_v[self.i].rect, 'x'), self.nav_v[self.i].original_rect.x + 15, 10, 'ease_out', 1)

    def render(self, surface):
        position = [self.pointer_x + self.menu.global_x, self.pointer_y + self.menu.global_y]
        surface.blit(self.pointer, position)

        for k in self.nav.values():
            k.render(surface, (self.menu.global_x, self.menu.global_y))


class TalentsContainer(Container):
    class Main(object):
        def __init__(self, container):
            self.container = container

            self.background = scale(pygame.image.load(os.path.join(MENU_PATH, 'player', 'talent', 'talent-back.png')), 3)
            self.background_rect = self.background.get_rect(midright=(400, SCREEN_DIMENSIONS[1] // 2))
            self.background_x, self.background_y = self.background_rect.topleft

            self.seperator = scale(pygame.image.load(os.path.join(MENU_PATH, 'player', 'talent', 'talent-seperator.png')), 3)
            self.seperator_rect = self.seperator.get_rect(center=(self.background_rect.centerx, self.background_y + 80))

            self.arrow = scale(pygame.image.load(os.path.join(MENU_PATH, 'player', 'talent','talent-arrow.png')), 2)
            self.arrow_flipped = pygame.transform.flip(self.arrow, True, False).convert_alpha()
            self.arrow_rect = self.arrow.get_rect(center=(0, self.background_y + 59))

            self.pointer = scale(pygame.image.load(os.path.join(MENU_PATH, 'player', 'talent','talent-pointer.png')), 2)
            self.pointer_rect = self.pointer.get_rect(midright=(0, 0))

            self.header = Textbox((0, 0), 1, 'm3x6', 'Talents', 1.5)
            self.header.rect.topleft = (self.background_x + 10, self.background_y - 30)
            self.header.original_rect.topleft = self.header.rect.topleft

            self.placeholder = Textbox((0, 0), 1, 'm3x6', 'Yet to be discovered..', 1, (125, 125, 125))
            self.placeholder.rect.center = (self.background_rect.centerx, self.background_y + 60)
            self.placeholder.original_rect.center = self.placeholder.rect.center

        def update(self, x, y):
            talent = self.container.talents_v[self.container.talents_k[x]][y][0]
            if y == -1:
                self.container.menu.game.easing.create((self.pointer_rect, 'right'), talent.rect.left - 15, 5, dt=1)
                self.container.menu.game.easing.create((self.pointer_rect, 'centery'), talent.rect.centery - 2, 5, dt=1)
            else:
                self.container.menu.game.easing.create((self.pointer_rect, 'right'), talent.rect.left - 15, 10, dt=1)
                self.container.menu.game.easing.create((self.pointer_rect, 'centery'), talent.rect.centery - 2, 10, dt=1)
        
        def render(self, surface):
            global_x, global_y = self.container.menu.global_x, self.container.menu.global_y
            
            position = (self.background_x + global_x, self.background_y + global_y)
            surface.blit(self.background, position)

            self.header.render(surface, (global_x, global_y))

            if self.container.category_n == 0:
                self.placeholder.render(surface, (global_x, global_y))
                return

            self.container.categories[self.container.talents_k[self.container.x]].render(surface, (global_x, global_y))
            if self.container.category_n > 1:
                self.arrow_rect.left = self.container.categories[self.container.talents_k[self.container.x]].rect.right + 15
                surface.blit(self.arrow, (self.arrow_rect.x + global_x, self.arrow_rect.y + global_y))

                self.arrow_rect.right = self.container.categories[self.container.talents_k[self.container.x]].rect.left - 15
                surface.blit(self.arrow_flipped, (self.arrow_rect.x + global_x, self.arrow_rect.y + global_y))

            position = (self.seperator_rect.x + global_x, self.seperator_rect.y + global_y)
            surface.blit(self.seperator, position)

            for box, _ in self.container.talents[self.container.talents_k[self.container.x]].values():
                box.render(surface, (global_x, global_y))

            surface.blit(self.pointer, (self.pointer_rect.x + global_x, self.pointer_rect.y + global_y))

    class Display(object):
        def __init__(self, container):
            self.container = container

            self.background = scale(pygame.image.load(os.path.join(MENU_PATH, 'default-square.png')), 2)

        def render(self, surface):
            if self.container.category_n == 0:
                return
    
            global_x, global_y = self.container.menu.global_x, self.container.menu.global_y

            name = self.container.talents_v[self.container.talents_k[self.container.x]][self.container.y][1]
            cache = self.container.talent_cache[self.container.talents_k[self.container.x]][name]

            surface.blit(cache[1], (self.container.main.background_rect.right + 50 + global_x, self.container.main.background_y + global_y))

    def __init__(self, menu):
        super().__init__(menu)

        self.main = self.Main(self)
        self.display = self.Display(self)

        self.talent_cache = {}

        self.categories = {}
        for k in ('offensive', 'defensive', 'mobility', 'utility'):
            textbox = Textbox((0, 0), 1, 'm3x6', k.capitalize(), 1.5)
            textbox.rect.center = (self.main.background_rect.centerx, self.main.background_y + 60)
            textbox.original_rect.center = textbox.rect.center

            self.categories[k] = textbox

        self.talents = {}

        self.talents_k = []
        self.talents_v = {}

        self.talents_n = {}
        self.category_n = 0

        self.x, self.y = 0, 0

    def add(self, cache):
        if cache['talent'].category not in self.talent_cache:
            self.talent_cache[cache['talent'].category] = {}
            self.talents[cache['talent'].category] = {}

        color = (255, 135, 135) if cache['talent'].rarity == 'rare' else (255, 255, 255)

        # Create display image
        cache['icon'] = pygame.mask.from_surface(cache['icon']).to_surface(setcolor=(color), unsetcolor=((0, 0, 0, 0))).convert_alpha()
        cache['label'] = pygame.mask.from_surface(cache['label']).to_surface(setcolor=(color), unsetcolor=((0, 0, 0, 0))).convert_alpha()
        for i in range(len(cache['description'])):
            description = re.sub(r'<(\d+)>', lambda m: str(int(m.group(1)) * cache['stacks']), cache['description'][i])
            cache['description'][i] = Fonts.create('m3x6', description, 1, (255, 255, 255))

        background = self.display.background.copy()
        origin = [*background.get_rect().midtop]
        origin[1] += 15

        background.blit(cache['icon'], (origin[0] - cache['icon'].get_width() // 2, origin[1]))
        origin[1] += cache['icon'].get_height() * 1.1

        background.blit(cache['label'], (origin[0] - cache['label'].get_width() // 2, origin[1])) 
        origin[1] += cache['label'].get_height() * 2

        for image in cache['description']:
            background.blit(image, (origin[0] - image.get_width() // 2, origin[1]))
            origin[1] += image.get_height() * 1.2
            
        self.talent_cache[cache['talent'].category][cache['talent'].__name__] = (cache, background)

        # Update talent list
        textbox = Textbox((0, 0), 1, 'm3x6', cache['name'], color=color)
        textbox.rect.centerx = self.main.background_rect.centerx
        textbox.original_rect.centerx = textbox.rect.centerx

        self.talents[cache['talent'].category][cache['talent'].__name__] = (textbox, cache['talent'].__name__)

        k = [s for s in self.categories.keys() if s in self.talents.keys()]
        self.talents_k = tuple(k)
        self.talents_v = {
            i: tuple(self.talents[i].values()) for i in self.talents_k
        }
        self.category_n = len(self.talents)

        for category in self.talents:
            self.talents_n[category] = len(self.talents[category])

            y = 120
            for box, _ in self.talents[category].values():
                box.rect.centery = self.main.background_y + y
                y += box.rect.height * 1.5
            
    def rooted(self):
        self.y = -1

    def back(self):
        self.menu.root = 0
        self.menu.current = 'nav'

        Sfx.play('menu_back')
    
    def update(self):
        if self.category_n == 0:
            return
        
        x = self.menu.x % self.category_n
        if self.x != x:
            self.x = x

            self.menu.y = 0
            self.y = -1

        y = self.menu.y % self.talents_n[self.talents_k[self.x]]
        if self.y != y:
            self.main.update(self.x, y)
            self.y = y

    def render(self, surface):
        self.main.render(surface)
        self.display.render(surface)

class StatsContainer(Container):
    class Primary(object):
        def __init__(self, container):
            self.container = container

            self.background = scale(pygame.image.load(os.path.join(MENU_PATH, 'player', 'stats', 'stats-back.png')), 3)
            self.background_rect = self.background.get_rect(bottomright=(400, SCREEN_DIMENSIONS[1] // 1.9))
            self.background_x, self.background_y = self.background_rect.topleft

            self.level_k = Textbox((self.background_x + 30, self.background_y + 30), 1, 'm3x6', 'Level: ', 1.5)
            self.level_v = None
            self.exp = None
            self.max = False

            self.stats_k = []
            self.stats_v = []

            x, y = self.background_x + 30, self.background_y + self.background_rect.height // 1.75
            for i, s in enumerate(self.container.stats):
                textbox = Textbox((x, y), 1, 'm3x6', f'{s}:')
                x += self.background_rect.width // 2
                self.stats_k.append(textbox)

                if (i + 1) % 2 == 0:
                    x = self.background_x + 30
                    y += textbox.image.get_height() * (1.5 if i != 1 else 2.25)

        def render(self, surface):
            global_x, global_y = self.container.menu.global_x, self.container.menu.global_y
            
            position = (self.background_x + global_x, self.background_y + global_y)
            surface.blit(self.background, position) 

            self.level_k.render(surface, (global_x, global_y))
            self.level_v.render(surface, (global_x, global_y))
            
            self.exp.render(surface, (global_x, global_y))

            for k in self.stats_k:
                k.render(surface, (global_x, global_y))
            
            for va, vb in self.stats_v:
                va.render(surface, (global_x, global_y))
                if vb != None:
                    vb.render(surface, (global_x, global_y))

    class Secondary(object):
        def __init__(self, container):
            self.container = container

        def render(self, surface):
            ...

    def __init__(self, menu):
        super().__init__(menu)

        self.stats = {
            k: (0, 0) for k in ('Health', 'Power', 'Speed', 'Focus', 'Knockback', 'Weight')
        }

        self.primary = self.Primary(self)
        self.secondary = self.Secondary(self)

        self.header = Textbox((0, 0), 1, 'm3x6', 'Stats', 1.5)
        self.header.rect.topleft = (self.primary.background_x + 10, self.primary.background_y - 30)
        self.header.original_rect.topleft = self.header.rect.topleft
    
    def rooted(self):
        player = self.menu.game.player
        
        if player.level >= player.max_level and not self.primary.max:
            self.primary.max = True
            self.primary.level_k = Textbox((self.primary.background_x + 30, self.primary.background_y + 30), 1, 'm3x6', 'Level: ', 1.5, (205, 250, 225))

        elif player.level < player.max_level and self.primary.max:
            self.primary.max = False
            self.primary.level_k = Textbox((self.primary.background_x + 30, self.primary.background_y + 30), 1, 'm3x6', 'Level: ', 1.5)

        # Update level
        level_k = self.primary.level_k

        color = (255, 255, 255)
        if self.primary.max:
            color = (205, 250, 225)
            
        self.primary.level_v = Textbox((level_k.rect.right + 5, 0), 1, 'm3x6', player.level, 1.5, color)
        self.primary.level_v.rect.centery = level_k.rect.centery

        exp = f'{player.experience} / {player.expreq}' if player.level < player.max_level else 'MAX'
        col = (175, 175, 175) if player.level < player.max_level else color
        self.primary.exp = Textbox((level_k.rect.left, level_k.rect.bottom + 5), 1, 'm3x6', exp, 1, col)

        # Update stats
        self.stats['Health'] = (5, player.health - 5)
        self.stats['Power'] = (0, player.power)

        self.stats['Speed'] = (0, player.speed)
        self.stats['Focus'] = (0, player.focus)

        self.stats['Knockback'] = (0, player.knockback)
        self.stats['Weight'] = (0, player.weight)

        k = self.primary.stats_k
        self.primary.stats_v = []
        for i, v in enumerate(self.stats):
            textbox_a = Textbox((k[i].rect.right + 5, k[i].rect.top), 1, 'm3x6', self.stats[v][0])

            textbox_b = None
            if self.stats[v][1] != 0:
                textbox_b = Textbox((k[i].rect.right + textbox_a.rect.width * 2.25, k[i].rect.top), 1, 'm3x6', f'~g+{self.stats[v][1]}~',)

            self.primary.stats_v.append((textbox_a, textbox_b))

    def back(self):
        self.menu.root = 0
        self.menu.current = 'nav'

        Sfx.play('menu_back')    

    def render(self, surface):
        self.header.render(surface, (self.menu.global_x, self.menu.global_y))

        self.primary.render(surface)
        self.secondary.render(surface)


class PlayerMenu(Menu):
    def __init__(self, game):
        super().__init__(game)

        self.active = False

        self.x, self.y = 0, 0
        self.root, self._root = 0, 0
        self.current = 'nav'

        self.global_x = -SCREEN_DIMENSIONS[0] // 2
        self.global_y = 0

        self.containers = [
            # Root 0
            {'nav': NavContainer(self)},

            # Root 1
            {'talents': TalentsContainer(self),
             'stats': StatsContainer(self)}
        ]

    def on_key_down(self, key):
        if self.game.in_menu and not self.active:
            return
        
        if self.game.in_cards:
            return
        
        if self.game.player.interact_npc:
            return
        
        if key in self.game.player.keybinds['@player_menu']:
            self.active = not self.active
            self.game.in_menu = self.active

            if self.active:
                self.game.easing.create((self.game, 'dim'), .75, 20, 'linear', 1)
                self.game.easing.create((self, 'global_x'), 0, 30, 'ease_out', 1)

                self.x, self.y = 0, 0
                self.root = 0
                self.current = 'nav'

                self.containers[self.root][self.current].rooted()

            else:
                self.game.easing.create((self.game, 'dim'), 0, 20, 'linear', 1)
                self.game.easing.create((self, 'global_x'), -SCREEN_DIMENSIONS[0] // 2, 10, 'ease_out', 1)

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
