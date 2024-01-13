from scripts.sprite import Sprite

from scripts.utils import load_spritesheet, get_bezier_point

import pygame
import os

class Dashbar(Sprite):
    def __init__(self, player, position, index):
        surface = pygame.Surface((64, 12)).convert_alpha()
        surface.set_colorkey((0, 0, 0))

        super().__init__(position, surface, index)
        self.use_entity_surface = True

        self.player = player
        self.cooldown = 90

        self.frames = load_spritesheet(os.path.join('resources', 'images', 'ui', 'dashbar.png'))

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
