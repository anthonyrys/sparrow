from scripts.sprite import Sprite

class Sprites(list):
    def sort_list(self):
        self.sort(key = lambda sprite: sprite.index)

    def append(self, __object):
        if not isinstance(__object, Sprite):
            print(f'[SpriteList] Append Failed: {__object} not {Sprite.__name__}')
            return True

        super().append(__object)
        self.sort_list()

    def extend(self, __iterable):
        for __object in __iterable:
            if not isinstance(__object, Sprite):
                print(f'[SpriteList] Extend Failed: {__object} not {Sprite.__name__}')
                return True

        super().extend(__iterable)
        self.sort_list()

    def remove(self, __object):
        if not isinstance(__object, Sprite):
            print(f'[SpriteList] Remove Failed: {__object} not {Sprite.__name__}')
            return True

        super().remove(__object)
        self.sort_list()
