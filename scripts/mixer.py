import pygame
import os

class Sfx:
    SOUNDS = {}
    SETTINGS = {}

    STATIC_VOLUMES = {
        'arrow_collide-e': 0.6,
        'arrow_collide-t': 0.6,

        'card_flip': 0.3,
        
        'player_hurt': 0.7,
        'player_land': 0.7,
        'player_death': 0.7

    }

    def init():
        for path in os.listdir(os.path.join('resources', 'sound_fx')):
            for file in os.listdir(os.path.join('resources', 'sound_fx', path)):
                f = os.path.join('resources', 'sound_fx', path, file)

                if os.path.isfile(f):
                    name = f'{path}_{file.split(".")[0]}'
                    sound = pygame.mixer.Sound(f)

                    if name in Sfx.STATIC_VOLUMES:
                        sound.set_volume(Sfx.STATIC_VOLUMES[name])

                    Sfx.SOUNDS[name] = sound

                elif os.path.isdir(f):
                    for _file in os.listdir(f):
                        _f = os.path.join('resources', 'sound_fx', path, file, _file)

                        name = f'{path}_{file}_{_file.split(".")[0]}'
                        sound = pygame.mixer.Sound(_f)

                        if name in Sfx.STATIC_VOLUMES:
                            sound.set_volume(Sfx.STATIC_VOLUMES[name])

                        Sfx.SOUNDS[name] = sound

    def play(sound, volume=1):
        if sound not in Sfx.SOUNDS:
            print(f'[SFX_MANAGER] Sound "{sound}" not found.')
            return False

        if sound in Sfx.STATIC_VOLUMES:
            volume *= Sfx.STATIC_VOLUMES[sound]

        Sfx.SOUNDS[sound].set_volume(volume)
        Sfx.SOUNDS[sound].play()

        return True

    def stop(sound):
        if sound not in Sfx.SOUNDS:
            print(f'[SFX_MANAGER] Sound "{sound}" not found.')
            return False

        Sfx.SOUNDS[sound].stop()

        return True
