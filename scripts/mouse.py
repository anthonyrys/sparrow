import pygame

class Mouse(object):
    def __init__(self):
        self.image = pygame.Surface((4, 4)).convert_alpha()
        self.image.fill((255, 0, 0))
        
        self.rect = self.image.get_frect()
        self.entity_rect = self.image.get_frect()

        self.crosshair_distance = 9
        self.original_crosshair_distance = self.crosshair_distance

        self.crosshair_length = 6
        self.original_crosshair_length = self.crosshair_length

        self.crosshair_color = (255, 255, 255)

    @property
    def mask(self):
        return pygame.mask.from_surface(self.image)
    
    @property
    def position(self):
        return list(self.rect.topleft)

    def update(self, game):
        self.rect.center = pygame.mouse.get_pos()

        self.entity_rect.x = self.rect.x - game.camera.offset[0]
        self.entity_rect.y = self.rect.y - game.camera.offset[1]

    def render(self, screen): 
        ...
