from scripts import GLOBAL_STAT_CURVE
from scripts.mixer import Sfx
from scripts.sprite import Sprite

from scripts.utils import generate_import_dict, load_spritesheet, get_bezier_point, bezier_presets, get_distance, clamp
from scripts.visual_fx import PolygonParticle

import pygame
import pygame.gfxdraw
import random
import math
import os

class Bow(object):
    def __init__(self, player, images):
        self.player = player
        self.images = {True: [], False: []}
        for image in images:
            self.images[False].append(image)
            self.images[True].append(pygame.transform.flip(image, True, False).convert_alpha())

        self.use_move_restriction = 0
        
        # Stats
        self.power = 0
        self.knockback = 0

        self.state = 0
        self.pre_charge = 0
        self.pre_charge_max = 0
        self.charged = False
        self.charge = 0

        self.special = None

        self.velocity_intensity = 0
        self.velocity_height = 0
        self.velocity_intensity_add = 0
        self.velocity_height_add = 0

        self.velocity_time = 0
        self.velocity_speed = 0

        self.prediction_line = []

        image = pygame.image.load(os.path.join('resources', 'images', 'bows', 'arrow.png')).convert_alpha()
        self.arrow_image = (image, pygame.transform.flip(image, True, False).convert_alpha())

    def y(self, x):
        a = self.velocity_intensity + self.velocity_intensity_add * self.charge
        b = self.velocity_height + self.velocity_height_add * self.charge

        return -0.1 * x **a + x * b
    
    def effect(self, game, entity):
        ...

    def fire(self, game):
        info = {'charge': self.charge}
        self.player.call_talents(game, 'on_fire', info)

        center = self.player.get_position('center')

        arrow = Arrow(self, (center[0] + 10 * self.player.direction, center[1]), self.player.index, self.special, self.effect)
        game.projectiles.append(arrow)

        # Particles
        start_position = [center[0] + 10 * self.player.direction, center[1]]

        end_pos_rel = pygame.Vector2((50 + 10 * abs(self.player.velocity[0]) + 10 * 2 * self.charge) * self.player.direction, 0)
        end_position = [center[0] + end_pos_rel[0], center[1] + end_pos_rel[1]]

        x = 12 * self.charge
        y = 6 + 3 * self.charge

        points = [
            [[-x, 0], [-x // 10, -y], [x // 10, -y], [x, 0], [x // 10, y], [-x // 10, y]],
            [[-x * 1.5, 0], [-x // 10, 0], [x // 10, 0], [x * 1.5, 0], [x // 10, 0], [-x // 10, 0]]
        ]

        dur = 30 // (1.5 * max(.667, self.charge))
        rot = 45 - 20 * self.charge

        particles = []

        particle_m = PolygonParticle(
            self.player.index + 1, dur,
            [start_position, end_position],
            points,
            color=(255, 255, 255), beziers=['ease_out', 'ease_out']
        )

        p = end_pos_rel.rotate(rot)
        end_position = [center[0] + p[0], center[1] + p[1]]

        particle_t = PolygonParticle(
            self.player.index + 1, dur,
            [start_position, end_position],
            points,
            color=(255, 255, 255), beziers=['ease_out', 'ease_out'], rotation=rot
        )

        p = end_pos_rel.rotate(-rot)
        end_position = [center[0] + p[0], center[1] + p[1]]

        particle_b = PolygonParticle(
            self.player.index + 1, dur,
            [start_position, end_position],
            points,
            color=(255, 255, 255), beziers=['ease_out', 'ease_out'], rotation=-rot
        )

        for _ in range(round(2 + 2 * self.charge)):
            position = [*center]
            position[0] += (random.randint(25, 50) + random.randint(30, 40) * self.charge) * self.player.direction
            position[1] += random.randint(-50, 50) * self.charge

            size = random.randint(1, 2) * self.charge
            particle = PolygonParticle(
                self.player.index + 1, dur + random.randint(20, 25) * self.charge,
                [center, position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=(255, 255, 255), beziers=['ease_out', 'ease_in']
            )

            particles.append(particle)

        particles.extend((particle_m, particle_t, particle_b))
        game.particles.extend(particles)

        Sfx.play('player_bow')
    
    def update(self, game):
        self.prediction_line = []

        if self.state == 1:
            # Focus curve graph: https://www.desmos.com/calculator/4rohuhaqnd
            focus = round(self.player.focus / (self.player.focus + GLOBAL_STAT_CURVE), 2)

            self.pre_charge = clamp(self.pre_charge + (1 + 1 * focus) * game.delta_time, 0, self.pre_charge_max)
            abs_prog = self.pre_charge / self.pre_charge_max

            game.camera.direction_offset = 75 * -self.player.direction * get_bezier_point(abs_prog, *bezier_presets['ease_out'])

            if abs_prog >= 1 and not self.charged:
                self.charged = True
                self.player.image_pulse_frames = [30, 30]
                self.player.image_pulse_color = (255, 255, 255)

            self.player.move_restriction = clamp((self.use_move_restriction - self.use_move_restriction * focus) * abs_prog, 0.0, self.use_move_restriction)

            self.charge = get_bezier_point(abs_prog, *bezier_presets['ease_out'])

            n = False
            for x in range(self.velocity_time // 25, self.velocity_time + 1, self.velocity_time // 25):
                point = (-x if self.player.direction == 1 else x, self.y(x))

                position = self.player.get_position('center')
                position[0] = round(position[0] - point[0])
                position[1] = round(position[1] - point[1])

                collide = False
                for tile in game.tilemap.renderable_tiles:
                    if tile.rect.collidepoint(position):
                        collide = True
                        break

                for enemy in game.enemies[1]:
                    if enemy.rect.collidepoint(position):
                        collide = True
                        break

                if collide:
                    break

                if n:
                    self.prediction_line.append((position, x / self.velocity_time))
                    n = False
                else:
                    n = True

    def render(self, surface):
        for info in self.prediction_line:
            a = 255 * info[1]
            pygame.gfxdraw.filled_circle(surface, *info[0], 1, (255, 255, 255, 255 - round(a)))

        if self.state == 1:
            image = self.images[self.player.direction != 1][3 - round(self.charge * 3)]

            position = self.player.get_position('center')
            position[0] += 10 * self.player.direction
            position[1] += self.player.mask.centroid()[1] // 3 - 10

            surface.blit(image, image.get_rect(center=position))

            position[0] += (8 * self.player.direction) - (8 * (self.charge) * self.player.direction)
            if self.player.direction > 0:
                surface.blit(self.arrow_image[0], self.arrow_image[0].get_rect(center=position))
            else:
                surface.blit(self.arrow_image[1], self.arrow_image[1].get_rect(center=position))

class Arrow(Sprite):
    def __init__(self, bow, position, index, special, effect):
        super().__init__(position, bow.arrow_image[0], index)

        self.bow = bow
        self.charge = bow.charge

        self.special = special
        self.effect = effect

        self.velocity_intensity = bow.velocity_intensity
        self.velocity_height = bow.velocity_height
        self.velocity_intensity_add = bow.velocity_intensity_add
        self.velocity_height_add = bow.velocity_height_add

        self.start_position = position
        self.previous_position = position

        self.velocity_direction = bow.player.direction
        self.velocity_time = bow.velocity_time
        self.velocity_speed = bow.velocity_speed
        self.velocity_x = 0
        
        self.current_chunk = None

        self.afterimage_ticks = [0, 1]
        self.afterimage_sub = 25
        self.afterimages = []

    def y(self, x):
        a = self.velocity_intensity + self.velocity_intensity_add * self.charge
        b = self.velocity_height + self.velocity_height_add * self.charge

        return -0.1 * x **a + x * b

    def collision(self, game, entity):
        particles = []
        velocity = pygame.math.Vector2(self.position) - pygame.math.Vector2(self.previous_position)

        distance_travelled = get_distance(self.position, self.start_position)

        info = {'distance_travelled': distance_travelled, 'damage_multiplier': 1}
        info = self.bow.player.call_talents(game, 'on_arrow', info)
    
        if entity.sprite_type == 'Enemy':
            power = math.floor(((self.bow.power * self.charge) + self.bow.player.power) * info['damage_multiplier'])
            knockback = math.floor(self.bow.knockback * self.charge) + self.bow.player.knockback

            entity.on_damaged(game, power, knockback)

            # Particles
            for _ in range(3):
                position = [*self.get_position('center')]
                position[0] += random.randint(-30, 30) - velocity[0] * (10 * self.charge)
                position[1] += random.randint(-30, 30) - velocity[1] * (10 * self.charge)

                size = round(random.randint(3, 6) * self.charge)

                particle = PolygonParticle(
                    self.index + 1, round(random.randint(40, 55) * self.charge),
                    [self.get_position('center'), position],
                    [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                    color=(255, 84, 84), beziers=['ease_out', 'ease_out']
                )

                particles.append(particle)

            start_position = [*self.get_position('center')]
            end_pos_rel = [velocity[0] * 10, velocity[1] * 10]
            end_position = [start_position[0] + end_pos_rel[0], start_position[1] + end_pos_rel[1]]

            x = 15 * self.charge
            y = 7 + 3 * self.charge

            points = [
                [[-x, 0], [-x // 10, -y], [x // 10, -y], [x, 0], [x // 10, y], [-x // 10, y]],
                [[-x * 1.5, 0], [-x // 10, 0], [x // 10, 0], [x * 1.5, 0], [x // 10, 0], [-x // 10, 0]]
            ]

            dur = 30 // max(self.charge, .95)
            rot = math.degrees(math.atan2(end_position[0] - start_position[0], -(end_position[1] - start_position[1]))) - 90
            particle = PolygonParticle(
                self.index + 1, dur,
                [start_position, end_position],
                points,
                color=(255, 255, 255), beziers=['ease_out', 'ease_out'], rotation=rot
            )

            particles.append(particle)

        volume = clamp(1 - (get_distance(game.player.position, self.position) / 1750), .1, 1)
        if entity.sprite_type == 'Enemy':
            Sfx.play(f'arrow_collide-e', volume)
        elif entity.sprite_type == 'Tile' or entity.sprite_type == 'Barrier':
            Sfx.play(f'arrow_collide-t', volume)

        self.effect(game, entity)

        # Particles
        position = self.get_position('center')
        for _ in range(2):
            new_position = [*position]
            new_position[0] += round(random.randint(-35, 35) * self.charge)
            new_position[1] += round(random.randint(-35, 35) * self.charge)

            size = random.randint(1, 3)

            particle = PolygonParticle(
                self.index + 1, random.randint(25, 35),
                [position, new_position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=(255, 255, 255), beziers=['ease_out', 'ease_in']
            )

            particles.append(particle)

        game.particles.extend(particles)

        for _ in range(round(random.randint(2, 3) * self.charge)):
            new_position = [*position]
            new_position[0] += round(random.randint(-50, 50) * self.charge) + velocity[0] * 10 * self.charge
            new_position[1] += round(random.randint(-50, 50) * self.charge) + velocity[1] * 10 * self.charge

            size = random.randint(2, 4)

            color = self.image.get_at((random.randint(0, self.image.get_width() - 1), random.randint(0, self.image.get_height() - 1)))
            if color[3] == 0:
                color = self.image.get_at((self.image.get_width() // 2, self.image.get_height() // 2))

            particle = PolygonParticle(
                self.index + 1, random.randint(30, 40),
                [position, new_position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=color, beziers=['ease_out', 'ease_in']
            )

            particles.append(particle)

        game.particles.extend(particles)

    def update(self, game):
        super().update(game)

        k = game.tilemap.chunk_keys
        for i in range(len(game.tilemap.chunk_rects)):
            if game.tilemap.chunk_rects[k[i]].colliderect(self.rect):
                self.current_chunk = k[i]
                break

        if self.velocity_x < self.bow.velocity_time:
            self.previous_position = self.position
            self.rect.x = self.start_position[0] + self.velocity_x * self.velocity_direction
            self.rect.y = self.start_position[1] - self.y(self.velocity_x)

            self.velocity_x += self.velocity_speed * max(self.charge, .25) * game.delta_time

        else:
            game.projectiles.remove(self)

        # Afterimages
        if self.charge >= .85 and self.afterimage_ticks[1] != 0:
            self.afterimage_ticks[0] += 1 * game.delta_time
            if self.afterimage_ticks[0] >= self.afterimage_ticks[1]:
                self.afterimage_ticks[0] = 0
                self.afterimages.append([self.image.copy(), self.image.get_alpha(), self.position])

        if not game.delta_time <= 0.01:
            angle = (180 / math.pi) * math.atan2(*(self.position[0] - self.previous_position[0], self.position[1] - self.previous_position[1])) - 90
            self.image = pygame.transform.rotate(self.original_image, angle).convert_alpha()

        for tile in game.tilemap.chunks[self.current_chunk]:
            if tile.rect.colliderect(self.rect):
                game.projectiles.remove(self)
                self.collision(game, tile)

                break

        for enemy in game.enemies[1]:
            if enemy.rect.colliderect(self.rect):
                game.projectiles.remove(self)
                self.collision(game, enemy)

                break

        dels = []
        for i in range(len(self.afterimages)):
            self.afterimages[i][1] -= self.afterimage_sub
            if self.afterimages[i][1] <= 0:
                dels.append(i)
            else:
                self.afterimages[i][0].set_alpha(self.afterimages[i][1])

        for i in dels:
            self.afterimages.pop(i)

    def render(self, surface):
        for i in range(len(self.afterimages)):
            surface.blit(self.afterimages[i][0], self.afterimages[i][2])

        surface.blit(self.image, self.image.get_rect(center=self.rect.center))

class WoodenBow(Bow):
    def __init__(self, player):
        super().__init__(player, load_spritesheet(os.path.join('resources', 'images', 'bows', 'wooden.png')))

        self.use_move_restriction = 3

        self.power = 2
        self.knockback = 1

        self.charge = 0

        self.pre_charge_max = 45

        self.velocity_intensity = 1.375
        self.velocity_height = 0.475
        self.velocity_intensity_add = -0.225
        self.velocity_height_add = -0.200

        self.velocity_time = 900
        self.velocity_speed = 20

BOWS = generate_import_dict('Bow', 'Arrow')
