from scripts.utils import generate_import_dict

from scripts import FRAME_RATE

class Talent(object):
    area = None
    rarity = None

    stackable = None
    prereq = None

    category = None
    description = None

    flags = []
    active = False

    def __init__(self, player):
        self.player = player
        self.stacks = 0 if self.stackable else None

        if self.stackable:
            self.stack()

    def stack(self):
        self.stacks += 1

    def call(self, game, info):
        ...

    def update(self, game):
        ...


# Offensive
class Precision(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 5

    category = 'offensive'
    description = 'Gain ~g+<1> Power~'
    
    def stack(self):
        super().stack()

        self.player.power += 1

class Marksman(Talent):
    area = 'generic'
    rarity = 'common'

    category = 'offensive'
    description = 'Your arrows deal 30%;more damage past;25m' # Note: 1 Pixel = 0.038370147 Meters

    flags = ['on_arrow']

    def __init__(self, player):
        self.pixels = round(25 / 0.038370147, -1)
        self.multiplier = .3

        super().__init__(player)

    def call(self, game, info):
        super().call(game, info)

        if info['distance_travelled'] >= self.pixels:
            info['damage_multiplier'] += self.multiplier

        return info

class RapidAssault(Talent):
    area = 'generic'
    rarity = 'common'

    category = 'offensive'
    description = 'Charged arrows give;~g+5 Focus~ for 3s'

    flags = ['on_fire']
    active = True

    def __init__(self, player):
        self.duration = None

        self.current_focus = 0
        self.focus = 5

        super().__init__(player)

    def call(self, game, info):
        super().call(game, info)
        
        if info['charge'] == 1 and self.duration == None:
            self.player.focus += self.focus
            self.current_focus = self.focus
            self.duration = FRAME_RATE * 3

        return info

    def update(self, game):
        super().update(game)

        if self.duration != None:
            self.duration -= 1 * game.delta_time

            if self.duration <= 0:
                self.duration = None
                self.player.focus -= self.current_focus
                self.current_focus = 0

class ExplosiveShot(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'offensive'
    description = '???'


# Defensive
class Vigor(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 5

    category = 'defensive'
    description = 'Gain ~g+<1> Health~'

    def stack(self):
        super().stack()

        self.player.max_health += 1
        self.player.health += 1

class Reprieve(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 2

    category = 'defensive'
    description = 'Increase the duration;of invincibility when;damaged by <20>%'

    flags = ['on_damaged']

    def __init__(self, player):
        self.multiplier = 0

        super().__init__(player)

    def stack(self):
        super().stack()

        self.multiplier += 0.2

    def call(self, game, info):
        super().call(game, info)

        info['iframe_multiplier'] += self.multiplier
        return info

class Exoskeleton(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'defensive'
    description = '???'


# Mobility
class Swiftfoot(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 3

    category = 'mobility'
    description = 'Dashing gives;~g+<1> Speed~ for 2s'

    flags = ['on_dash']
    active = True

    def __init__(self, player):
        self.duration = None

        self.current_speed = 0
        self.speed = 0

        super().__init__(player)

    def stack(self):
        super().stack()

        self.speed += 1

    def call(self, game, info):
        super().call(game, info)

        if self.duration != None:
            self.player.speed -= self.current_speed

        self.player.speed += self.speed
        self.current_speed = self.speed
        self.duration = FRAME_RATE * 2
        
        return info

    def update(self, game):
        super().update(game)

        if self.duration != None:
            self.duration -= 1 * game.delta_time

            if self.duration <= 0:
                self.duration = None
                self.player.speed -= self.current_speed
                self.current_speed = 0

class AerialAffinity(Talent):
    area = 'generic'
    rarity = 'common'

    category = 'mobility'
    description = 'Increase the;effectiveness of your;glide by 15%'

    def __init__(self, player):
        player.glide /= 1.15

        super().__init__(player)

class Momentum(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'mobility'
    description = '???'


# Utility
class Adaptivity(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'utility'
    description = '???'


TALENTS = {
    'R_RARITY': 0.0,

    'generic': {
        'common': {},
        'rare': {}
    }
}

for name, talent in generate_import_dict('Talent').items():
    TALENTS[talent.area][talent.rarity][name] = talent
