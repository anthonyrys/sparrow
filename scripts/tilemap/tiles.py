from scripts.sprite import Sprite

from scripts.utils import generate_import_dict

class Tile(Sprite):
    def __init__(self, position, image, index):
        super().__init__(position, image, index)

    def render(self, surface):
        surface.blit(self.image, self.rect)

class Barrier(Sprite):
    def __init__(self, position, image, index):
        super().__init__(position, image, index)

    def render(self, surface):
        surface.blit(self.image, self.rect)


TILES = generate_import_dict()
