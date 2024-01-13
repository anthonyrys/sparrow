from scripts import SCREEN_DIMENSIONS

from scripts.utils import bezier_presets, get_bezier_point, clamp

import pygame
import random

class Camera(object):
    def __init__(self, focus=None):
        self.focus_parent = focus
        self.focus_alert = True
        self.focus = None

        self.offset = pygame.Vector2()
        self.to_offset = pygame.Vector2()

        self.direction_offset = 0

        self.box_dimensions = (SCREEN_DIMENSIONS[0] * .15, SCREEN_DIMENSIONS[1] * .25)
        self.box = pygame.Rect(0, 0, *self.box_dimensions)
        self.original_box = pygame.Rect(0, 0, *self.box_dimensions)

        self.camera_tween_frames = [0, 0]
        self.camera_tween_position = [0, 0]
        self.camera_tween_bezier = bezier_presets['ease_out']

        self.camera_shake_frames = [0, 0]
        self.camera_shake_intensity = 0

    def set_camera_tween(self, frames, bezier='ease_out'):
        self.camera_tween_frames = [0, frames]
        self.camera_tween_position = self.offset
        self.camera_tween_bezier = bezier_presets[bezier]

    def set_camera_shake(self, frames, intensity=10):
        self.camera_shake_frames = [frames, frames]
        self.camera_shake_intensity = intensity

    def update(self, game):
        if self.focus != self.focus_parent.rect:
            self.focus = self.focus_parent.rect
            self.focus_alert = True

        if self.focus:
            if self.focus.left < self.box.left:
                self.box.left = self.focus.left

            elif self.focus.right > self.box.right:
                self.box.right = self.focus.right

            if self.focus.bottom > self.box.bottom:
                self.box.bottom = self.focus.bottom

            elif self.focus.top < self.box.top:
                self.box.top = self.focus.top

        shake = [0, 0]
        if self.camera_shake_frames[0] > 0 and game.delta_time != 0:
            abs_prog = self.camera_shake_frames[0] / self.camera_shake_frames[1]
            intensity = round((self.camera_shake_intensity) * get_bezier_point(abs_prog, *bezier_presets['linear']))

            shake[0] = random.randint(-intensity, intensity)
            shake[1] = random.randint(-intensity, intensity)

            self.camera_shake_frames[0] -= 1 * game.delta_time

        self.to_offset[0] = -self.box.centerx + (SCREEN_DIMENSIONS[0] * .5)
        self.to_offset[1] = -self.box.centery + (SCREEN_DIMENSIONS[1] * .5)

        self.to_offset[0] += self.direction_offset

        if self.camera_tween_frames[0] < self.camera_tween_frames[1]:
            abs_prog = self.camera_tween_frames[0] / self.camera_tween_frames[1]

            tweened_offset = [
                self.camera_tween_position[0] + ((self.to_offset[0] - self.camera_tween_position[0]) * get_bezier_point(abs_prog, *self.camera_tween_bezier)),
                self.camera_tween_position[1] + ((self.to_offset[0] - self.camera_tween_position[1]) * get_bezier_point(abs_prog, *self.camera_tween_bezier))
            ]

            self.camera_tween_frames[0] += 1 * game.raw_delta_time

            self.offset = tweened_offset
            self.offset[0] += shake[0]
            self.offset[1] += shake[1]

        else:
            self.offset += (self.to_offset - self.offset) * .08 * game.raw_delta_time
            self.offset[0] += shake[0]
            self.offset[1] += shake[1]

        return self.offset
