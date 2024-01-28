from scripts import FRAME_RATE, SCREEN_DIMENSIONS
from scripts.camera import Camera
from scripts.fonts import Fonts
from scripts.mixer import Sfx
from scripts.mouse import Mouse
from scripts.player import Player
from scripts.sprites import Sprites
from scripts.tilemap import TilemapRenderer

from scripts.npcs import ENEMIES
from scripts.systems import TALENTS
from scripts.ui import Card
from scripts.utils import clamp, get_distance, bezier_presets, get_bezier_point

import moderngl
import pygame
import pygame.gfxdraw
import random
import array
import time
import os

class Game(object):
    def __init__(self, clock, context):
        # Moderngl
        self.context = context

        self.main_buffer = context.buffer(
            data=array.array('f', [
                -1.0, 1.0, 0.0, 0.0,
                1.0, 1.0, 1.0, 0.0,
                -1.0, -1.0, 0.0, 1.0,
                1.0, -1.0, 1.0, 1.0
            ])
        )

        self.shaders = {'vert': {}, 'frag': {}}
        self.textures = {'entity': None, 'ui': None}
        self.programs = {}

        path = os.path.join('resources', 'shaders')
        for shader in os.listdir(path):
            with open(os.path.join(path, shader), 'r') as s:
                self.shaders[shader.split('.')[1]][shader.split('.')[0]] = s.read()

        for texture in self.textures:
            tex = context.texture(SCREEN_DIMENSIONS, 4)
            tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            tex.swizzle = 'BGRA'

            self.textures[texture] = tex

        self.textures['entity'].use(0)
        self.textures['ui'].use(1)

        self.create_programs(context)
        self.main_array = context.vertex_array(
            self.programs['main'],
            [(self.main_buffer, '2f 2f', 'v_Position', 'v_TexCoords')]
        )


        # Pygame
        self.clock = clock
        self.fps_clock = [10, 10]
        self.fps_surface = None

        self.frames = 0

        self.timers = []

        self.entity_surface = pygame.Surface(SCREEN_DIMENSIONS).convert_alpha()
        self.entity_surface.set_colorkey((0, 0, 0))
        self.entity_rect = pygame.Rect(0, 0, *SCREEN_DIMENSIONS)

        self.entity_display = pygame.Surface(SCREEN_DIMENSIONS)

        self.dim = 0
        self.to_dim = [0, 0]
        self.dim_time = [0, 0]
        self.dim_bezier = bezier_presets['ease_out']

        self.ui_display = pygame.Surface(SCREEN_DIMENSIONS).convert_alpha()
        self.ui_display.set_colorkey((0, 0, 0))

        self.delta_time, self.raw_delta_time, self.last_time = time.time(), time.time(), time.time()
        self.delta_time_multipliers = {}

        self.timers = {}

        self.mouse = Mouse()

        self.player = Player((0, 0), 0)
        self.camera = Camera(self.player)

        self.card_specials = {'specific': None}

        self.in_cards = False
        self.cards = []

        self.card_active = False
        self.card_i = 0
        self.card = None

        self.enemies = [{}, Sprites()]
        self.enemy_spawns = {}
        self.enemy_ticks = [0, 180]

        self.friendlies = Sprites()

        self.projectiles = Sprites()

        self.particles = Sprites()
        self.particle_queue = []

        self.ui = Sprites()
        self.ui.extend(self.player.ui_elements.values())

        self.area = 'sandbox'
        self.tilemap = TilemapRenderer(self)

        self.enemy_spawns = None
        self.friendly_spawns = None

        self.load_tilemap(self.area)

        self.__debug_player_stats = False

    def on_player_respawn(self):
        self.player.dead = False

        self.player.health = self.player.max_health
        self.player.velocity = pygame.Vector2()

        self.player.image_pulse_frames[0] = 0
        self.player.rect.topleft = self.tilemap.flags['Player_spawn'][0]

    def on_player_death(self):
        self.player.dead = True

        self.camera.set_camera_shake(120)
        self.timers['player_respawn'] = [180, 0, self.on_player_respawn, []]

    def on_card_spawn(self):
        c_pool = list(TALENTS['generic']['common'].values())
        r_pool = list(TALENTS['generic']['rare'].values())
        s_pool = {}

        for talent in self.player.talents:
            s_pool[talent.__class__] = talent.stacks

            if not talent.stackable:
                if talent.rarity == 'rare':
                    r_pool.remove(talent.__class__)
                else:
                    c_pool.remove(talent.__class__)
            else:
                if talent.stacks >= talent.stackable:
                    if talent.rarity == 'rare':
                        r_pool.remove(talent.__class__)
                    else:
                        c_pool.remove(talent.__class__)  

        if self.card_specials['specific'] and self.card_specials['specific'] not in s_pool:
            if self.card_specials['specific'].stackable:
                s_pool[self.card_specials['specific']] = 0
            
        if len(c_pool) < 3:
            return -1
    
        choices = []
        has_rare = False

        r_count = len(r_pool)
        for _ in range(3):
            if random.uniform(0, 1.0) <= TALENTS['R_RARITY'] and r_count > 0:
                pool = r_pool
                r_count -= 1

                has_rare = True

            else:
                pool = c_pool

            talent = random.choice(pool)
            while talent in choices or talent == self.card_specials['specific']:
                talent = random.choice(pool)
            
            if talent not in s_pool and talent.stackable:
                s_pool[talent] = 0

            choices.append(talent)

        if self.card_specials['specific']:
            choices.append(self.card_specials['specific'])

        cards = tuple(Card((0, -500), 1, 0, c, s_pool.get(c, None)) for c in choices)

        self.delta_time_multipliers['card_spawn'] = [0, False, [1, [0, 75], 'ease_in']]

        self.dim_time = [0, 0]
        self.to_dim = [0, 0]

        self.timers['card_spawn_t'] = [50, 1, setattr, (self, 'dim_time', [0, 75])]
        self.timers['card_spawn_db'] = [50, 1, setattr, (self, 'dim_bezier', bezier_presets['ease_out'])]
        self.timers['card_spawn_td'] = [50, 1, setattr, (self, 'to_dim', [self.dim, .95])]

        p = 50
        x = (SCREEN_DIMENSIONS[0] / 2) - (sum(c.image.get_width() for c in cards) + (len(cards) - 1) * p) / 2

        i = 0
        for card in cards:
            card.rect.x = x

            card.to_time = [0, 80]
            card.to_type = 'y'
            card.to_y = (card.rect.y, (SCREEN_DIMENSIONS[1] / 2) - card.rect.height / 2)
            
            card.flip_count = 100 + i * 25

            i += 1
            x += card.image.get_width() + p

        self.in_cards = True
        self.cards = tuple(cards)

        self.card_i = len(self.cards) // 2
        self.card = self.cards[self.card_i]

        self.timers['card_add'] = [100, 1, self.ui.extend, ([cards])]
        self.timers['card_start'] = [200 + i * 25, 1, setattr, [self, 'card_active', True]]

        return has_rare
    
    def on_card_select(self):
        for card in self.cards:
            card.to_time = [0, 60]
            card.to_type = 'y'
            card.to_bezier = bezier_presets['ease_in']
            card.to_y = (card.rect.y, -500)

            if self.card == card:
                card.to_y = (card.rect.y, SCREEN_DIMENSIONS[1] + 50)

            card.d_count = 60

        self.in_cards = False

        if self.card.talent == self.card_specials['specific']:
            self.card_specials['specific'] = None

        if self.card.talent.stackable:
            found = False
            for talent in self.player.talents:
                if self.card.talent == talent.__class__:
                    talent.stack()
                    found = True
                    break

            if not found:
                talent = self.card.talent(self.player)
                self.player.talents.append(talent)

        else:
            talent = self.card.talent(self.player)
            self.player.talents.append(talent)

        del self.delta_time_multipliers['card_spawn']
        self.delta_time_multipliers['card_select'] = [1, False, [0, [0, 75], 'ease_in']]

        self.dim_time = [0, 50]
        self.dim_bezier = bezier_presets['ease_in']

        self.to_dim = [self.dim, 0]

    def load_tilemap(self, tilemap):
        self.tilemap.load(tilemap)

        if 'Player_spawn' in self.tilemap.flags and self.player.position == [0.0, 0.0]:
            self.player.rect.topleft = self.tilemap.flags['Player_spawn'][0]

        self.enemy_spawns = {
            k: (v, (1, 500)) for k, v in self.tilemap.enemies.items()
        }

    def create_programs(self, context):
        self.programs['main'] = context.program(
            vertex_shader=self.shaders['vert']['main'],
            fragment_shader=self.shaders['frag']['main']
        )
        
        self.programs['main']['dim_f'] = 0
        self.programs['main']['entity'] = 0
        self.programs['main']['ui'] = 1

    def update_enemyspawns(self):
        self.enemy_ticks[0] += 1 * self.delta_time
        if self.enemy_ticks[0] >= self.enemy_ticks[1]:
            # Enemy count
            self.enemies[0] = {}
            for enemy in self.enemies[1]:
                if enemy.sprite_id not in self.enemies[0]:
                    self.enemies[0][enemy.sprite_id] = {}

                if tuple(enemy.spawn) not in self.enemies[0][enemy.sprite_id]:
                    self.enemies[0][enemy.sprite_id][tuple(enemy.spawn)] = 0

                self.enemies[0][enemy.sprite_id][tuple(enemy.spawn)] += 1

            # Enemy spawns
            for enemy in self.enemy_spawns:
                spawns = [p for p in self.enemy_spawns[enemy][0]]
                spawns.sort(key=lambda p: get_distance(self.player.position, p))

                for i in range(len(spawns)):
                    if enemy in self.enemies[0] and tuple(spawns[i]) in self.enemies[0][enemy]:
                        if self.enemies[0][enemy][tuple(spawns[i])] >= self.enemy_spawns[enemy][1][0]:
                            continue
                    
                    if get_distance(self.player.position, spawns[i]) > self.enemy_spawns[enemy][1][1]:
                        continue

                    spawn_enemy = ENEMIES[enemy](spawns[i], 1)
                    self.enemies[1].append(spawn_enemy)

                    break

            self.enemy_ticks[0] = 0

    def update(self):
        quit = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit = True

                if event.key == pygame.K_1:
                    self.__debug_player_stats = not self.__debug_player_stats

                if self.in_cards and self.card_active:
                    if event.key in self.player.keybinds['$interact']:
                        self.card_active = False
                        for card in self.cards:
                            card.flip(1)

                        self.timers['card_select'] = [10, 1, self.on_card_select, []]

                    else:
                        if event.key in self.player.keybinds['left']:
                            self.card_i -= 1
                            if self.card_i < 0:
                                self.card_i = len(self.cards) - 1

                        elif event.key in self.player.keybinds['right']:
                            self.card_i += 1
                            if self.card_i >= len(self.cards):
                                self.card_i = 0

                        self.card = self.cards[self.card_i]

                if self.delta_time != 0:
                    self.player.on_key_down(self, event.key)

            if event.type == pygame.KEYUP:
                if self.delta_time != 0:
                    self.player.on_key_up(self, event.key)

        self.delta_time = max(0, min((time.time() - self.last_time) * FRAME_RATE, 6))
        self.raw_delta_time = self.delta_time
        self.last_time = time.time()

        multiplier = 1
        dels = []
        for delta_multiplier in self.delta_time_multipliers.keys():
            if len(self.delta_time_multipliers[delta_multiplier]) >= 3:
                if self.delta_time_multipliers[delta_multiplier][2][1][0] < self.delta_time_multipliers[delta_multiplier][2][1][1]:
                    abs_prog = self.delta_time_multipliers[delta_multiplier][2][1][0] / self.delta_time_multipliers[delta_multiplier][2][1][1]
                    point = get_bezier_point(abs_prog, *bezier_presets[self.delta_time_multipliers[delta_multiplier][2][2]])

                    dist = self.delta_time_multipliers[delta_multiplier][2][0] - self.delta_time_multipliers[delta_multiplier][0]
                    self.delta_time_multipliers[delta_multiplier][0] = self.delta_time_multipliers[delta_multiplier][0] + dist * point
                    self.delta_time_multipliers[delta_multiplier][2][1][0] += 1 * self.raw_delta_time

                elif self.delta_time_multipliers[delta_multiplier][2][1][0] > self.delta_time_multipliers[delta_multiplier][2][1][1]:
                    self.delta_time_multipliers[delta_multiplier][2][1][0] = self.delta_time_multipliers[delta_multiplier][2][1][1]
                    self.delta_time_multipliers[delta_multiplier][0] = self.delta_time_multipliers[delta_multiplier][2][0]

                    if self.delta_time_multipliers[delta_multiplier][0] == 0:
                        dels.append(delta_multiplier)

            if not self.delta_time_multipliers[delta_multiplier][1]:
                multiplier -= self.delta_time_multipliers[delta_multiplier][0]
                continue

            multiplier -= self.delta_time_multipliers[delta_multiplier][0]
            self.delta_time_multipliers[delta_multiplier][1] -= 1 * self.raw_delta_time
            if self.delta_time_multipliers[delta_multiplier][1] <= 0:
                dels.append(delta_multiplier)

        for delta_dels in dels:
            del self.delta_time_multipliers[delta_dels]

        self.delta_time *= clamp(multiplier, 0, 1)

        del_timers = []
        for timer in self.timers:
            if self.timers[timer][0] <= 0:
                del_timers.append(timer)
                continue

            if self.timers[timer][1] == 0:
                self.timers[timer][0] -= 1 * self.delta_time
            else:
                self.timers[timer][0] -= 1 * self.raw_delta_time

        for timer in del_timers:
            self.timers[timer][2](*self.timers[timer][3])
            del self.timers[timer]

        del_queues = []
        for i in range(len(self.particle_queue)):
            if self.particle_queue[i][0] <= 0:
                del_queues.append(self.particle_queue[i])
                self.particles.append(self.particle_queue[i][1])
                continue

            self.particle_queue[i][0] -= 1 * self.delta_time

        for del_queue in del_queues:
            self.particle_queue.remove(del_queue)

        if self.delta_time != 0:
            self.tilemap.update()

            self.update_enemyspawns()

            for enemy in self.enemies[1]:
                enemy.update(self)

            for projectile in self.projectiles:
                projectile.update(self)

        for particle in self.particles:
            if particle.use_entity_surface and self.delta_time != 0:
                particle.update(self)

            elif not particle.use_entity_surface:
                particle.update(self)

        if self.delta_time != 0:
            self.player.update(self)

        for ui in self.ui:
            ui.update(self)

        self.mouse.update(self)
        self.camera.update(self)

        self.entity_rect.x, self.entity_rect.y = -self.camera.offset[0], -self.camera.offset[1]

        if self.dim_time[0] < self.dim_time[1]:
            abs_prog = self.dim_time[0] / self.dim_time[1]

            dist = self.to_dim[1] - self.to_dim[0]
            self.dim = self.to_dim[0] + dist * get_bezier_point(abs_prog, *self.dim_bezier)
            self.dim_time[0] += 1 * self.raw_delta_time

        self.frames += 1 * self.raw_delta_time
        self.fps_clock[0] += 1 * self.raw_delta_time
        if self.fps_clock[0] >= self.fps_clock[1]:
            self.fps_clock[0] = 0
            self.fps_surface = Fonts.create('m3x6', round(self.clock.get_fps()), 1.5)

        return quit

    def render(self):
        if self.delta_time != 0:
            self.entity_surface.fill((0, 0, 0), self.entity_rect)
            self.entity_display.fill((0, 0, 0))

        self.ui_display.fill((0, 0, 0))

        if self.delta_time != 0:
            self.tilemap.render_a()

            for projectile in [p for p in self.projectiles if p.rect.colliderect(self.entity_rect)]:
                projectile.render(self.entity_surface)

            for enemy in self.enemies[1]:
                enemy.render(self.entity_surface)

            self.player.render(self.entity_surface)

            self.tilemap.render_b()

        for particle in self.particles:
            if particle.use_entity_surface:
                if self.delta_time != 0 and particle.rect.colliderect(self.entity_rect):
                    particle.render(self.entity_surface)
                    
            elif not particle.use_entity_surface:
                particle.render(self.ui_display)

        if self.__debug_player_stats:
            for i, name in enumerate(['max_health', 'power', 'speed', 'focus']):
                text = Fonts.create('m3x6', f'{name}: ~g{getattr(self.player, name)}~')

                self.ui_display.blit(text, (20, 100 + (20 * i)))

        for ui in self.ui:
            if hasattr(ui, 'use_entity_surface'):
                ui.render(self.entity_surface)
            else:
                ui.render(self.ui_display)

        self.ui_display.blit(self.fps_surface, self.fps_surface.get_rect(topright=(SCREEN_DIMENSIONS[0] - 5, 5)))

        if self.delta_time != 0:
            self.entity_display.blit(self.entity_surface, self.camera.offset)

        self.programs['main']['dim_f'].value = self.dim
        self.textures['entity'].write(self.entity_display.get_view('1'))
        self.textures['ui'].write(self.ui_display.get_view('1'))

        self.main_array.render(moderngl.TRIANGLE_STRIP)
