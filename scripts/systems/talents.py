from scripts.utils import generate_import_dict

class Talent(object):
    area = None
    rarity = None

    stackable = None
    prereq = None

    category = None
    description = None

    flags = []

    def __init__(self):
        self.stacks = 1 if self.stackable else None


# Offensive
class Precision(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 5

    category = 'offensive'
    description = 'Gain ~g+1 Power~'

class Marksman(Talent):
    area = 'generic'
    rarity = 'common'

    category = 'offensive'
    description = 'Your arrows deal 30%;more damage past;25m' # Note: 1 Pixel = 0.038370147 Meters

class RapidAssault(Talent):
    area = 'generic'
    rarity = 'common'

    category = 'offensive'
    description = 'Charged arrows;increase your ~gFocus~;by ~g10%~ for 5s'

class ExplosiveShot(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'offensive'
    description = 'Charged arrows; explode for 75% of; your ~gPower~'


# Defensive
class Vigor(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 5

    category = 'defensive'
    description = 'Gain ~g+1 Health~'

class Evasiveness(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 2

    category = 'defensive'
    description = 'Increase the duration;of invincibility when;damaged by 20%'

class Steadfast(Talent):
    area = 'generic'
    rarity = 'common'

    stackable = 3

    category = 'defensive'
    description = 'Gain ~g+1 Weight~'

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
    description = 'Gain ~g+1 Speed~ for;2s upon dashing'

class AerialAffinity(Talent):
    area = 'generic'
    rarity = 'common'

    category = 'mobility'
    description = 'Increase the;effectiveness of your;glide by 25%'

class Momentum(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'mobility'
    description = 'Dashing reduces its;cooldown by 10% for;3s, up to 50%'


# Utility
class Adaptivity(Talent):
    area = 'generic'
    rarity = 'rare'

    category = 'utility'
    description = '???'


TALENTS = {
    'R_RARITY': 0.1,

    'generic': {
        'common': {},
        'rare': {}
    }
}

for name, talent in generate_import_dict('Talent').items():
    TALENTS[talent.area][talent.rarity][name] = talent
