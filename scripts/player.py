from scripts.fonts import Fonts
from scripts.mixer import Sfx
from scripts.sprite import Sprite

from scripts.systems import BOWS
from scripts.ui import Dashbar, PlayerHealthbar
from scripts.utils import get_bezier_point, bezier_presets, get_distance, load_spritesheet, clamp
from scripts.visual_fx import PolygonParticle

import pygame
import random
import math
import os

class Player(Sprite):
    def __init__(self, position, index):
        super().__init__(position, pygame.Surface((32, 64)), index)

        self.previous_position = list(position)
        self.current_chunks = []

        self.keybinds = {
            # Press
            'up': [pygame.K_UP],
            'left': [pygame.K_LEFT],
            'down': [pygame.K_DOWN],
            'right': [pygame.K_RIGHT],

            # Keydown
            '@tleft': [pygame.K_LEFT],
            '@tright': [pygame.K_RIGHT],

            '@jump': [pygame.K_UP],
            '@dash': [pygame.K_z],

            # Keydown/Keyup
            '$interact': [pygame.K_x]
        }

        self.tinput = None
        self.inputs = {
            k: False for k in self.keybinds.keys()
        }

        self.velocity = pygame.Vector2()
        self.direction = 1
        self.move_speed = [.5, 6]
        self.move_friction = .35
        self.move_restriction = 0

        self.jumps = [1, 1]
        self.jump_power = -10
        self.jump_cooldown = 60

        self.gravity = [.5, 12]
        self.glide = self.gravity[0] * .8

        self.dashes = [1, 1]
        self.dash_cooldown = 90

        self.max_health = 5
        self.max_health_cap = 110
        self.health = self.max_health

        # Stats
        self.power = 1
        self.weight = 1
        self.speed = 0
        self.focus = 0
        
        self.iframes = 0

        self.dead = False
        self.dead_colors = ((35, 105, 80), (50, 130, 100), (65, 55, 50), (90, 80, 80), (255, 255, 255))

        self.in_combat = False
        self.combat_tags = []

        self.target_npc = None
        self.target_prop = None

        self.interact_npc = None

        self.bow = BOWS['WoodenBow'](self)

        self.collisions = []
        self.collide_points = {
            k: False for k in ['top', 'left', 'bottom', 'right']
        }

        self.animation_state = 'idle'
        self.animation_images = {}
        self.animation_frames = [{}, {}]
        self.animation_info = {
            'idle': [[120, 10, 10, 10, 10], True],
            'run': [[5, 5, 5, 4, 4], True],
            'jump': [[5, 5, 5], False],
            'fall': [[7, 7, 7], False],
            'landed': [[5, 5, 5], False],
            'dash': [[3, 3, 3, 3, 3], False]
        }

        for name in self.animation_info.keys():
            images = load_spritesheet(os.path.join('resources', 'images', 'player', f'{name}.png'), self.animation_info[name][0])

            self.animation_images[name] = images
            self.animation_frames[0][name] = 0
            self.animation_frames[1][name] = 0

        self.image_pulse_frames = [0, 0]
        self.image_pulse_color = (0, 0, 0)
        self.image_pulse_bezier = bezier_presets['linear']
        self.image_pulse_dt_time = 0

        self.pulse_image = None

        self.events = {}
        self.cooldowns = {}

        self.area_flags = {}
        self.npc_flags = {}

        self.ui_elements = {
            'healthbar': PlayerHealthbar(self, (25, 25), self.index),
            'dashbar': Dashbar(self, (0, 0), self.index)
        }

    def on_key_down(self, game, key):
        for action in [a for a in self.inputs.keys() if a[0] == '@' or a[0] == '$']:
            self.inputs[action] = False
            if not isinstance(self.keybinds[action], list):
                if key == self.keybinds[action]:
                    self.inputs[action] = True
                    break

            if key in self.keybinds[action]:
                self.inputs[action] = True
                break

        if self.inputs['@jump']:
            self.on_jump(game)
            self.inputs['@jump'] = False

        if self.inputs['@dash']:
            self.on_dash(game)
            self.inputs['@dash'] = False

        if self.inputs['@tleft']:
            self.tinput = 'left'
            self.inputs['@tleft'] = False

        if self.inputs['@tright']:
            self.tinput = 'right'
            self.inputs['@tright'] = False
            
        if self.inputs['$interact']:
            self.on_interact(game, 'down')

    def on_key_up(self, game, key):
        for action in [a for a in self.inputs.keys() if a[0] == '$']:
            if not isinstance(self.keybinds[action], list):
                if key == self.keybinds[action]:
                    self.inputs[action] = False
                    if action == '$interact':
                        self.on_interact(game, 'up')

                    break

            if key in self.keybinds[action]:
                self.inputs[action] = False
                if action == '$interact':
                    self.on_interact(game, 'up')
                
                break

    def on_interact(self, game, input):
        if self.health == 0:
            return

        # Npcs -> Props -> Bow
        if input == 'down':
            if self.interact_npc:
                ...


            elif self.target_npc:
                ...

            elif self.target_prop:
                ...


            else:
                if self.bow:
                    self.bow.state = 1

        elif input == 'up':
            if self.bow.state == 1:
                self.bow.state = 0
                self.bow.pre_charge = 0
                self.bow.charged = False

                self.move_restriction = 0

                game.camera.direction_offset = 0

                if self.bow.charge >= .5:
                    self.bow.fire(game)

    def on_jump(self, game):
        if self.jumps[0] <= 0 or 'jump' in self.cooldowns:
            return

        if not self.collide_points['bottom'] and self.jumps[0] == self.jumps[1] and 'coyote' not in self.events:
            return

        if 'damaged' in self.events or 'dashed' in self.events:
            return

        if self.health == 0:
            return

        Sfx.play('player_jump')
        Sfx.stop('player_land')

        self.cooldowns['jump'] = self.jump_cooldown
        self.jumps[0] -= 1

        self.velocity[1] = self.jump_power

        midbottom = self.get_position('midbottom')
        start_position = [midbottom[0], midbottom[1] - 5]
        end_position = [midbottom[0] + 45, midbottom[1] - 5]

        # Particles
        particle_r = PolygonParticle(
            self.index + 1, 10,
            [start_position, end_position],
            [
                [[-6, 0], [-1, -5], [1, -5], [6, 0], [1, 5], [-1, 5]],
                [[-9, 0], [-1, 0], [1, 0], [9, 0], [1, 0], [-1, 0]]
            ],
            color=(255, 255, 255)
        )

        end_position[0] = start_position[0] - 45

        particle_l = PolygonParticle(
            self.index + 1, 10,
            [start_position, end_position],
            [
                [[-6, 0], [-1, -5], [1, -5], [6, 0], [1, 5], [-1, 5]],
                [[-9, 0], [-1, 0], [1, 0], [9, 0], [1, 0], [-1, 0]]
            ],
            color=(255, 255, 255)
        )

        game.particles.extend([particle_r, particle_l])

    def on_dash(self, game):
        if self.dashes[0] <= 0 or '@dash' in self.cooldowns:
            return

        if not self.inputs['left'] and not self.inputs['right'] and not self.inputs['up']:
            return

        if self.bow.state == 1:
            return

        if 'damaged' in self.events:
            return

        if self.health == 0:
            return

        Sfx.play('player_dash')
        Sfx.stop('player_jump')
        Sfx.stop('player_land')

        self.events['movement_override'] = 15
        self.events['animation_reset_override'] = 15

        self.events['dashed'] = 15

        self.cooldowns['@dash'] = self.dash_cooldown
        self.dashes[0] -= 1

        if self.inputs['left'] and self.inputs['right']:
            if self.tinput == 'left':
                self.velocity[0] = -self.move_speed[1] * 2
            elif self.tinput == 'right':
                self.velocity[0] = self.move_speed[1] * 2
        elif self.inputs['left']:
            self.velocity[0] = -self.move_speed[1] * 2
        elif self.inputs['right']:
            self.velocity[0] = self.move_speed[1] * 2
        else:
            self.velocity[0] = 0

        if self.inputs['up']:
            self.velocity[1] = -self.move_speed[1]
        elif self.inputs['down']:
            self.velocity[1] = self.move_speed[1]
        else:
            self.velocity[1] = 0

        self.image_pulse_frames = [60, 60]
        self.image_pulse_color = (205, 247, 226)

        # Particles
        particles = []

        for _ in range(3):
            position = [*self.get_position('center')]
            position[0] += random.randint(-50, 50) - self.velocity[0] * 10
            position[1] += random.randint(-50, 50) - self.velocity[1] * 10 - self.rect.height // 3

            size = random.randint(2, 5)

            particle = PolygonParticle(
                self.index + 1, random.randint(40, 60),
                [self.get_position('center'), position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=(205, 250, 225), beziers=['ease_out', 'ease_in']
            )

            particles.append(particle)

        game.particles.extend(particles)

    def on_damaged(self, game, damage, knockback):
        if self.iframes > 0:
            return False

        self.iframes = 30

        self.health -= damage
        self.health = clamp(self.health, 0, self.max_health)

        self.image_pulse_frames = [60, 60]
        self.image_pulse_color = (255, 84, 84)

        # Dead
        if self.health == 0:
            self.bow.state = 0
            self.bow.pre_charge = 0
            self.bow.charged = False

            self.move_restriction = 0
            game.camera.direction_offset = 0

            game.delta_time_multipliers['player_dead'] = [1, 30]
            game.timers['player_dead_call'] = [30, 1, game.on_player_death, []]
            game.timers['player_dead_sfx'] = [30, 1, Sfx.play, ['player_death']]

            # Particles
            particles = []

            position = self.get_position('center')
            for color in self.dead_colors:
                for _ in range(random.randint(1, 2)):
                    new_position = [*position]
                    new_position[0] += random.randint(-250, 250)
                    new_position[1] += random.randint(-250, -150)

                    size = random.randint(5, 8)
                    particle = PolygonParticle(
                        self.index + 1, random.randint(90, 120),
                        [position, new_position],
                        [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                        color=color, beziers=['ease_out', 'ease_in'], gravity=random.uniform(1.25, 2)
                    )

                    particles.append([1, particle])

            x, y = 15, 5
            p_info = [[300, 0], [-300, 0], [0, 300], [0, -300]]
            points = [
                [[-x, 0], [-x // 10, -y], [x // 10, -y], [x, 0], [x // 10, y], [-x // 10, y]],
                [[-x * 1.5, 0], [-x // 10, 0], [x // 10, 0], [x * 1.5, 0], [x // 10, 0], [-x // 10, 0]]
            ]

            for i in p_info:
                new_position = [*position]
                new_position[0] += i[0]
                new_position[1] += i[1]

                rot = math.degrees(math.atan2(new_position[0] - position[0], -(new_position[1] - position[1]))) - 90
                particle = PolygonParticle(
                    self.index + 1, 105,
                    [position, new_position],
                    points,
                    color=(255, 255, 255), beziers=['ease_out', 'ease_out'], rotation=rot
                )

                particles.append([1, particle])

            game.particle_queue.extend(particles)

            return True

        self.events['damaged'] = 30

        self.velocity[0] = knockback * 2 / self.weight
        self.velocity[1] = self.jump_power // 2

        game.delta_time_multipliers['player_damaged'] = [1, 15]
        game.timers['player_damage_sfx'] = [15, 1, Sfx.play, ['player_hurt']]

        game.camera.set_camera_shake(30)

        # Particles
        particles = []

        position = self.get_position('center')
        for _ in range(random.randint(3, 5)):
            new_position = [*position]
            new_position[0] += random.randint(-75, 75) + self.velocity[0] * 30
            new_position[1] += random.randint(-50, 50) + self.velocity[1] * 10

            size = random.randint(3, 5)
            particle = PolygonParticle(
                self.index + 1, random.randint(25, 45),
                [position, new_position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=(255, 84, 84), beziers=['ease_out', 'ease_in'], gravity=random.uniform(1, 1.5)
            )

            particles.append([1, particle])

        game.particle_queue.extend(particles)

        return True

    def update_inputs(self):
        keys = pygame.key.get_pressed()

        for action in [a for a in self.inputs.keys() if a[0] != '@']:
            self.inputs[action] = False

            if not isinstance(self.keybinds[action], list):
                self.inputs[action] = keys[self.keybinds[action]]
                continue

            for v in self.keybinds[action]:
                if not keys[v]:
                    continue

                self.inputs[action] = keys[v]
                break

    def update_velocity(self, game):
        if 'movement_override' in self.events:
            return

        # X velocity
        if self.velocity[0] > self.move_speed[1] - self.move_restriction:
            if abs(self.velocity[0]) - self.move_speed[0] < self.move_friction:
                self.velocity[0] -= abs(self.velocity[0]) - self.move_speed[0]

            else:
                self.velocity[0] -= self.move_friction * game.delta_time

        elif self.velocity[0] < -self.move_speed[1] + self.move_restriction:
            if abs(self.velocity[0]) - self.move_speed[0] < self.move_friction:
                self.velocity[0] += abs(self.velocity[0]) - self.move_speed[0]

            else:
                self.velocity[0] += self.move_friction * game.delta_time

        if 'damaged' not in self.events:
            if self.inputs['right'] and not self.inputs['left']:
                self.velocity[0] += self.move_speed[0] * game.delta_time if self.velocity[0] < self.move_speed[1] - self.move_restriction else 0

            elif self.inputs['left'] and not self.inputs['right']:
                self.velocity[0] -= self.move_speed[0] * game.delta_time if self.velocity[0] > -self.move_speed[1] + self.move_restriction else 0

            if self.inputs['right'] and self.inputs['left']:
                if self.tinput == 'left':
                    self.velocity[0] += self.move_speed[0] * game.delta_time if self.velocity[0] < self.move_speed[1] - self.move_restriction else 0
                elif self.tinput == 'right':
                    self.velocity[0] -= self.move_speed[0] * game.delta_time if self.velocity[0] > -self.move_speed[1] + self.move_restriction else 0

            if not self.inputs['right'] and not self.inputs['left']:
                if self.velocity[0] > 0:
                    self.velocity[0] -= self.move_speed[0] * .5 * game.delta_time

                elif self.velocity[0] < 0:
                    self.velocity[0] += self.move_speed[0] * .5 * game.delta_time

        if abs(self.velocity[0]) < self.move_speed[0] * game.delta_time:
            self.velocity[0] = 0

        if 'damaged' not in self.events:
            if self.velocity[0] > 0:
                if self.bow.state == 1 and self.inputs['right'] and self.tinput == 'left':
                    self.direction = -1
                elif self.bow.state == 1 and self.inputs['left']:
                    self.direction = -1
 
                else:
                    self.direction = 1

            elif self.velocity[0] < 0:
                if self.bow.state == 1 and self.inputs['left'] and self.tinput == 'right':
                    self.direction = 1
                elif self.bow.state == 1 and self.inputs['right']:
                    self.direction = 1

                else:
                    self.direction = -1

        # Y velocity
        if not 'coyote' in self.events or self.collide_points['bottom']:
            gravity = (self.gravity[0] if not self.inputs['up'] else self.glide) * game.delta_time if self.velocity[1] < self.gravity[1] else 0
            self.velocity[1] += gravity

    def update_collision_x(self, tiles):
        self.collide_points['right'] = False
        self.collide_points['left'] = False

        for tile in tiles:
            if not self.rect.colliderect(tile.rect):
                if tile in self.collisions:
                    self.collisions.remove(tile)

                continue

            if self.velocity[0] > 0:
                self.rect.right = tile.rect.left
                self.collide_points['right'] = True

                if tile not in self.collisions:
                    self.collisions.append(tile)

                self.velocity[0] = 0

            if self.velocity[0] < 0:
                self.rect.left = tile.rect.right
                self.collide_points['left'] = True

                if tile not in self.collisions:
                    self.collisions.append(tile)

                self.velocity[0] = 0

    def update_collision_y(self, tiles, game):
        self.collide_points['top'] = False

        # https://www.giantbomb.com/coyote-time/3015-9701/
        if self.collide_points['bottom']:
            self.events['coyote'] = 6

        self.collide_points['bottom'] = False

        for tile in tiles:
            if not self.rect.colliderect(tile.rect):
                if tile in self.collisions:
                    self.collisions.remove(tile)

                continue

            if self.velocity[1] < 0:
                self.rect.top = tile.rect.bottom
                self.collide_points['top'] = True

                if tile not in self.collisions:
                    self.collisions.append(tile)

                self.velocity[1] = 0

            else:
                if self.velocity[1] >= self.gravity[0] * 20:
                    Sfx.play('player_land')
                    self.events['landed'] = 15

                    midbottom = self.get_position('midbottom')
                    start_position = [midbottom[0], midbottom[1] - 5]
                    end_position = [midbottom[0] + 45, tile.rect.top - 5]

                    particle_r = PolygonParticle(
                        self.index + 1, 15,
                        [start_position, end_position],
                        [
                            [[-4, 0], [-1, -3], [1, -3], [4, 0], [1, 3], [-1, 3]],
                            [[-7, 0], [-1, 0], [1, 0], [7, 0], [1, 0], [-1, 0]]
                        ],
                        color=(155, 155, 155)
                    )

                    end_position[0] = start_position[0] - 45

                    particle_l = PolygonParticle(
                        self.index + 1, 15,
                        [start_position, end_position],
                        [
                            [[-4, 0], [-1, -3], [1, -3], [4, 0], [1, 3], [-1, 3]],
                            [[-7, 0], [-1, 0], [1, 0], [7, 0], [1, 0], [-1, 0]]
                        ],
                        color=(155, 155, 155)
                    )

                    game.particles.extend([particle_r, particle_l])

                self.rect.bottom = tile.rect.top
                self.collide_points['bottom'] = True

                if tile not in self.collisions:
                    self.collisions.append(tile)

                    self.velocity[1] = 0

    def update_states(self, game):
        # Animations
        if 'dashed' in self.events:
            self.animation_state = 'dash'

        elif not self.collide_points['bottom']:
            if self.velocity[1] < 0:
                self.animation_state = 'jump'

            else:
                self.animation_state = 'fall'

        elif 'landed' in self.events:
            self.animation_state = 'landed'

        elif self.velocity[0] > 0 or self.velocity[0] < 0:
            self.animation_state = 'run'

        else:
            self.animation_state = 'idle'

    def update_image(self, game):
        et = 1
        if self.animation_state == 'run':
            et = 1 if abs(self.velocity[0] / self.move_speed[1]) > 1 else abs(self.velocity[0] / self.move_speed[1])

        if len(self.animation_images[self.animation_state]) <= self.animation_frames[0][self.animation_state]:
            if self.animation_info[self.animation_state][1]:
                if self.animation_state == 'idle':
                    v = random.randint(self.animation_info['idle'][0][0] // 4, self.animation_info['idle'][0][0] // 2)
                    self.animation_frames[0][self.animation_state] = v
                    self.animation_frames[1][self.animation_state] = v

                else:
                    self.animation_frames[0][self.animation_state] = 0
                    self.animation_frames[1][self.animation_state] = 0

            else:
                self.animation_frames[0][self.animation_state] = len(self.animation_images[self.animation_state]) - 1
                self.animation_frames[1][self.animation_state] = len(self.animation_images[self.animation_state]) - 1

        image = self.animation_images[self.animation_state][self.animation_frames[0][self.animation_state]]

        if len(self.animation_images[self.animation_state]) > self.animation_frames[0][self.animation_state]:
            self.animation_frames[1][self.animation_state] += (1 * et) * game.delta_time
            self.animation_frames[0][self.animation_state] = round(self.animation_frames[1][self.animation_state])

        if 'animation_reset_override' not in self.events:
            for frame in self.animation_frames[0]:
                if self.animation_state == frame:
                    continue

                if frame == 'run':
                    self.animation_frames[0][frame] = 13
                    self.animation_frames[1][frame] = 13
                    continue

                if frame == 'idle':
                    v = random.randint(self.animation_info['idle'][0][0] // 5, self.animation_info['idle'][0][0] // 2)
                    self.animation_frames[0][frame] = v
                    self.animation_frames[1][frame] = v
                    continue

                if self.animation_frames[0][frame] == 0:
                    continue

                self.animation_frames[0][frame] = 0
                self.animation_frames[1][frame] = 0

        self.image = pygame.transform.flip(image, True, False).convert_alpha() if self.direction < 0 else image

    def update_targets(self, game):
        ...

    def update(self, game):
        if self.dead:
            return

        self.update_inputs()
        self.update_velocity(game)

        # Update current chunks
        self.current_chunks = []

        k = game.tilemap.chunk_keys
        for i in range(len(game.tilemap.chunk_rects)):
            if get_distance(self.rect.center, game.tilemap.chunk_rects[k[i]].center) <= game.tilemap.tile_size[0] * game.tilemap.chunk_dimensions[0] // 1.5:
                self.current_chunks.append(k[i])

        tiles = []
        for c in self.current_chunks:
            tiles.extend([t for t in game.tilemap.chunks[c] if get_distance(self.position, t.position) <= self.rect.height * 2])

        self.previous_position = self.position

        self.rect.x += self.velocity[0] * game.delta_time
        self.update_collision_x(tiles)

        self.rect.y += self.velocity[1] * game.delta_time
        self.update_collision_y(tiles, game)

        self.update_states(game)
        self.update_image(game)
        
        self.update_targets(game)

        self.max_health = clamp(self.max_health, 1, self.max_health_cap)
        self.health = clamp(self.health, 0, self.max_health)

        if self.collide_points['bottom']:
            self.jumps[0] = self.jumps[1]
            self.dashes[0] = self.dashes[1]

        self.bow.update(game)
        
        if self.iframes > 0:
            self.iframes -= 1 * game.delta_time

        cooldown_dels = []
        for cooldown in self.cooldowns.keys():
            self.cooldowns[cooldown] -= 1 * game.delta_time

            if self.cooldowns[cooldown] <= 0:
                cooldown_dels.append(cooldown)

        for v in cooldown_dels:
            del self.cooldowns[v]

        event_dels = []
        for event in self.events.keys():
            self.events[event] -= 1 * game.delta_time

            if self.events[event] <= 0:
                event_dels.append(event)

        for v in event_dels:
            del self.events[v]

        if self.image_pulse_frames[0] > 0:
            self.pulse_image = self.mask.to_surface(
                setcolor=self.image_pulse_color,
                unsetcolor=(0, 0, 0, 0)
            )

            self.pulse_image.set_alpha(255 * get_bezier_point((self.image_pulse_frames[0] / self.image_pulse_frames[1]), *self.image_pulse_bezier))
            if self.image_pulse_dt_time == 0:
                self.image_pulse_frames[0] -= 1 * game.delta_time
            else:
                self.image_pulse_frames[0] -= 1 * game.raw_delta_time

    def render(self, surface):
        if self.dead:
            return
        
        surface.blit(self.image, self.image.get_rect(center=self.rect.center))

        if self.image_pulse_frames[0] > 0:
            surface.blit(self.pulse_image, self.pulse_image.get_rect(center=self.rect.center))

        self.bow.render(surface)
