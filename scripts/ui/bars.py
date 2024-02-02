from scripts.sprite import Sprite

from scripts.utils import load_spritesheet, get_bezier_point

import pygame
import os

class PlayerDashbar(Sprite):
    def __init__(self, player, position, index):
        surface = pygame.Surface((64, 12)).convert_alpha()
        surface.set_colorkey((0, 0, 0))

        super().__init__(position, surface, index)
        self.use_entity_surface = True

        self.player = player
        self.cooldown = 90

        self.frames = load_spritesheet(os.path.join('resources', 'images', 'ui', 'bars', 'dashbar.png'))

        self.offset = [0, -50]

    def update(self, game):
        self.rect.centerx = self.player.rect.centerx + self.offset[0]
        self.rect.centery = self.player.rect.centery + self.offset[1]

    def render(self, surface):
        if '@dash' not in self.player.cooldowns:
            return

        if self.player.dead:
            return

        abs_prog = self.player.cooldowns['@dash'] / self.cooldown

        self.image.fill((0, 0, 0))

        self.image.blit((self.frames[1]), self.frames[1].get_rect(center=self.image.get_rect().center))
        pygame.gfxdraw.box(self.image, (4, 4, self.rect.width - 12 - self.rect.width * abs_prog, 4), (205, 247, 226))
        
        self.image.blit((self.frames[0]), (0, 0))
        self.image.set_alpha(255 - 255 * get_bezier_point(1 - abs_prog, [0, 0], [0, 1], [0, 1], [1, 0], 0))

        surface.blit(self.image, self.rect)

class PlayerHealthbar(Sprite):
    def __init__(self, player, position, index):
        super().__init__(position, pygame.Surface((1, 1)), index)

        self.player = player

        self.image = pygame.image.load(os.path.join('resources', 'images', 'ui', 'bars', 'heart-p.png')).convert_alpha()
        self.images = {}
        self.outlines = {}

        self.states = {
            'default': ((255, 95, 95), (200, 60, 60)),
            'default_empty': ((50, 55, 65), (25, 30, 40)),

            'stored': ((205, 250, 225), (175, 200, 180)),
            'stored_empty':((85, 90, 100), (60, 70, 80))
        }

        for state in self.states:
            image = pygame.mask.from_surface(self.image).to_surface(setcolor=self.states[state][0], unsetcolor=(0, 0, 0, 0))
            self.images[state] = image

            outline = pygame.mask.from_surface(self.image).to_surface(setcolor=self.states[state][1], unsetcolor=(0, 0, 0, 0))
            self.outlines[state] = outline

    def outline(self, screen, state, position):
        screen.blit(self.outlines[state], (position[0] + 1, position[1]))
        screen.blit(self.outlines[state], (position[0] - 1, position[1]))
        screen.blit(self.outlines[state], (position[0], position[1] + 1))
        screen.blit(self.outlines[state], (position[0], position[1] - 1))

    def render(self, screen):
        # 1 for every 10 hearts the player has
        num_stored = max(0, (self.player.health - 1) // 10)
        num_stored_empty = (self.player.max_health - 1) // 10 - num_stored

        # 10 if at a 10 heart interval, else use remainder from stored
        num_default = 10 if self.player.health % 10 == 0 and self.player.health != 0 else self.player.health % 10
        num_default_empty = self.player.max_health % 10 - self.player.health % 10 if self.player.health // 10 == self.player.max_health // 10 else 10 - num_default

        # Specific case for 10 heart intervals
        if (self.player.health // 10 == self.player.max_health // 10 and num_stored_empty > 0):
            num_default_empty = 0

        x, y = 20, 20
        for _ in range(num_default):
            screen.blit(self.images['default'], (x, y))
            x += self.image.get_width() * 1.4

        for _ in range(num_default_empty):
            screen.blit(self.images['default_empty'], (x, y))
            x += self.image.get_width() * 1.4

        x, y = 20, y + self.image.get_height() * 1.6
        for _ in range(num_stored):
            screen.blit(self.images['stored'], (x, y))
            x += self.image.get_width() * 1.4

        for _ in range(num_stored_empty):
            screen.blit(self.images['stored_empty'], (x, y))
            x += self.image.get_width() * 1.4

class EnemyHealthbar(Sprite):
    def __init__(self, enemy, position, index):
        super().__init__(position, pygame.Surface((1, 1)), index)

        self.enemy = enemy

        self.images = {}
        self.outlines = {}
        self.states = {
            'default': ((255, 95, 95), (200, 60, 60)),
            'default_empty': ((50, 55, 65), (25, 30, 40))
        }

        self.image = pygame.image.load(os.path.join('resources', 'images', 'ui', 'bars', 'heart-e.png')).convert_alpha()

        for state in self.states:
            image = pygame.mask.from_surface(self.image).to_surface(setcolor=self.states[state][0], unsetcolor=(0, 0, 0, 0))
            self.images[state] = image

            outline = pygame.mask.from_surface(self.image).to_surface(setcolor=self.states[state][1], unsetcolor=(0, 0, 0, 0))
            self.outlines[state] = outline

    def outline(self, screen, state, position):
        screen.blit(self.outlines[state], (position[0] + 1, position[1]))
        screen.blit(self.outlines[state], (position[0] - 1, position[1]))
        screen.blit(self.outlines[state], (position[0], position[1] + 1))
        screen.blit(self.outlines[state], (position[0], position[1] - 1))

    def render(self, screen):
        if self.enemy.health == self.enemy.max_health:
            return

        w = (self.images['default'].get_width() + 5) * self.enemy.max_health - 5
        x = self.enemy.rect.centerx - (w / 2)
        y = self.enemy.rect.top - self.enemy.rect.height // 3

        c = x
        for _ in range(self.enemy.health):
            # self.outline(screen, 'default', (c, y))
            screen.blit(self.images['default'], (c, y))
            c += self.images['default'].get_width() + 5

        for _ in range(self.enemy.max_health - self.enemy.health):
            # self.outline(screen, 'default_empty', (c, y))
            screen.blit(self.images['default_empty'], (c, y))
            c += self.images['default'].get_width() + 5
