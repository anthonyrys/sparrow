from scripts.sprite import Sprite

from scripts.utils import get_bezier_point, bezier_presets

import pygame
import pygame.gfxdraw

class PolygonParticle(Sprite):
    def __init__(self, index, time, positions, points,
                 beziers=['linear', 'linear'], rotation=0, color=(255, 255, 255),
                 anchor=None, delta_type=0, gravity=0):

        super().__init__(positions[0], pygame.Surface((1, 1)), index)

        self.current_time, self.end_time = 0, time
        self.delta_type = delta_type

        self.anchor = anchor
        self.use_entity_surface = True

        self.start_position = [positions[0][0], positions[0][1]]
        self.end_position =  [positions[1][0], positions[1][1]]
        self.current_position = [positions[0][0], positions[0][1]]

        self.start_points = [[p[0], p[1]] for p in points[0]]
        self.end_points = [[p[0], p[1]] for p in points[1]]
        self.current_points = [[p[0], p[1]] for p in points[0]]

        self.position_bezier = bezier_presets[beziers[0]]
        self.point_bezier = bezier_presets[beziers[1]]

        self.rotation = rotation
        self.color = color

        self.gravity = 0
        self.per_gravity = gravity

        self.xs = [0, 0]
        self.ys = [0, 0]

    def update(self, game):
        if self.delta_type == 0:
            self.current_time += 1 * game.delta_time
            self.gravity += self.per_gravity * game.delta_time
        else:
            self.current_time += 1 * game.raw_delta_time
            self.gravity += self.per_gravity * game.raw_delta_time

        if self.current_time > self.end_time:
            if self in game.particles:
                game.particles.remove(self)

            return

        abs_prog = self.current_time / self.end_time

        self.current_position[0] = self.start_position[0] + ((self.end_position[0] - self.start_position[0]) * get_bezier_point(abs_prog, *self.position_bezier))
        self.current_position[1] = self.start_position[1] + ((self.end_position[1] - self.start_position[1]) * get_bezier_point(abs_prog, *self.position_bezier))
        self.current_position[1] += self.gravity

        if self.anchor:
            position = self.anchor[0].get_position(self.anchor[1])
            self.current_position[0] += position[0]
            self.current_position[1] += position[1]

        for i in range(len(self.current_points)):
            self.current_points[i][0] = self.start_points[i][0] + ((self.end_points[i][0] - self.start_points[i][0]) * get_bezier_point(abs_prog, *self.point_bezier))
            self.current_points[i][1] = self.start_points[i][1] + ((self.end_points[i][1] - self.start_points[i][1]) * get_bezier_point(abs_prog, *self.point_bezier))

        self.rect.topleft = self.current_position

    def render(self, surface):
        if self.rotation != 0:
            points = []
            for p in self.current_points:
                point = pygame.Vector2(p).rotate(self.rotation)
                points.append((self.current_position[0] + point[0], self.current_position[1] + point[1]))

            pygame.gfxdraw.filled_polygon(surface, points, self.color)

        else:
            points = [[self.current_position[0] + p[0], self.current_position[1] + p[1]] for p in self.current_points]
            pygame.gfxdraw.filled_polygon(surface, points, self.color)
