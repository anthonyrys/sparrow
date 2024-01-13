import pygame

class Sprite(pygame.sprite.Sprite):
    def __init__(self, position, image, index):
        pygame.sprite.Sprite.__init__(self)
        self.sprite_type = self.__class__.__mro__[-4].__name__
        self.sprite_id = self.__class__.__name__

        self.index = index

        self.image = image
        self.original_image = image

        self.rect = self.image.get_frect()
        self.original_rect = self.image.get_frect()

        self.rect.topleft = position
        self.original_rect.topleft = position

    @property
    def mask(self):
        return pygame.mask.from_surface(self.image)

    @property
    def position(self):
        return self.get_position()

    @property
    def dimensions(self):
        return list(self.rect.size)

    def get_position(self, point='topleft'):
        return list(getattr(self.rect, point))

    def collidepixel(self, other):
        collision = None
        if not isinstance(other, pygame.sprite.Group):
            group = pygame.sprite.Group(other)
            collision = pygame.sprite.spritecollide(self, group, False, pygame.sprite.collide_mask)
            group.remove(other)

        else:
            collision = pygame.sprite.spritecollide(self, other, False, pygame.sprite.collide_mask)

        return collision

    def update(self, game):
        ...

    def render(self, surface):
        ...
