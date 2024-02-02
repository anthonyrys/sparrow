from scripts import FRAME_RATE, SCREEN_DIMENSIONS
from scripts.camera import Camera
from scripts.fonts import Fonts
from scripts.mixer import Sfx
from scripts.mouse import Mouse
from scripts.player import Player
from scripts.sprites import Sprites
from scripts.tilemap import TilemapRenderer

from scripts.npcs import ENEMIES
from scripts.ui import CardManager
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

        self.card_manager = CardManager(self)

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

                self.card_manager.on_key_down(event.key)

                if self.delta_time != 0:
                    self.player.on_key_down(self, event.key)

            if event.type == pygame.KEYUP:
                self.card_manager.on_key_up(event.key)

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

        if self.__debug_player_stats:
            for i, name in enumerate(['max_health', 'power', 'speed', 'focus']):
                text = Fonts.create('m3x6', f'{name}: ~g{getattr(self.player, name)}~')

                self.ui_display.blit(text, (20, 100 + (20 * i)))

        for ui in self.ui:
            if hasattr(ui, 'use_entity_surface'):
                ui.render(self.entity_surface)
            else:
                ui.render(self.ui_display)

        for particle in self.particles:
            if particle.use_entity_surface:
                if self.delta_time != 0 and particle.rect.colliderect(self.entity_rect):
                    particle.render(self.entity_surface)
                    
            elif not particle.use_entity_surface:
                particle.render(self.ui_display)

        self.ui_display.blit(self.fps_surface, self.fps_surface.get_rect(topright=(SCREEN_DIMENSIONS[0] - 5, 5)))

        if self.delta_time != 0:
            self.entity_display.blit(self.entity_surface, self.camera.offset)

        self.programs['main']['dim_f'].value = self.dim
        self.textures['entity'].write(self.entity_display.get_view('1'))
        self.textures['ui'].write(self.ui_display.get_view('1'))

        self.main_array.render(moderngl.TRIANGLE_STRIP)
