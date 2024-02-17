from scripts.fonts import Fonts
from scripts.sprite import Sprite

class Menu(object):
    def __init__(self, game):
        self.game = game

    def on_key_down(self, key):
        ...

    def on_key_up(self, key):
        ...

    def update(self):
        ...
    
    def render(self, surface):
        ...

class Container(object):
    def __init__(self, menu):
        self.menu = menu
        
    def rooted(self):
        ...
    
    def select(self):
        ...

    def back(self):
        ...

    def update(self):
        ...

    def render(self, surface):
        ...


class Textbox(Sprite):
    def __init__(self, position, index, font, text, size=1, color=(255, 255, 255)):
        image = Fonts.create(font, text, size, color)
        super().__init__(position, image, index)
    
    def update(self, game):
        ...

    def render(self, surface, offset):
        position = [self.rect.centerx + offset[0], self.rect.centery + offset[1]]
        surface.blit(self.image, self.image.get_rect(center=position))
