from scripts.sprite import Sprite

from scripts.ui import EnemyHealthbar
from scripts.utils import generate_import_dict, bezier_presets, get_bezier_point, scale
from scripts.visual_fx import PolygonParticle

import pygame
import random
import os

ENEMY_PATH = os.path.join('resources', 'images', 'enemies')

class Enemy(Sprite):
    def __init__(self, position, image, index):
        super().__init__(position, image, index)

        self.enemy_type = None
        self.spawn = position

        self.despawn_timer = 300
        self.despawn = self.despawn_timer

        self.velocity = pygame.Vector2()
        self.direction = 0
        self.move_speed = [0, 0]
        self.move_friction = 0
        self.move_restriction = 0

        self.jumps = [0, 0]
        self.jump_power = 0
        self.jump_cooldown = 0

        self.gravity = [0, 0]

        self.level = 0

        # Stats
        self.max_health = 0
        self.health = 0
        self.power = 0

        self.knockback = 0
        self.weight = 0

        self.attack_cooldown = 0
        self.attack_cooldown_limit = 60

        self.collisions = []
        self.collide_points = {
            k: False for k in ['top', 'left', 'bottom', 'right']
        }

        self.image_pulse_frames = [0, 0]
        self.image_pulse_color = (0, 0, 0)
        self.image_pulse_bezier = bezier_presets['linear']
        self.image_pulse_dt_time = 0

        self.pulse_image = None

        self.events = {}
        self.cooldowns = {}

        self.healthbar = EnemyHealthbar(self, (0, 0), 0)

    def on_damaged(self, game, damage, knockback):
        self.health -= damage

        self.image_pulse_frames = [60, 60]
        self.image_pulse_color = (255, 84, 84)

        if self.weight != -1:
            self.velocity[0] = knockback * 2 / (self.weight + 1)

        if self.health <= 0:
            self.on_death(game)

        return True

    def on_death(self, game):
        game.enemies[1].remove(self)
        game.player.on_experience(self.level)
        
        # Particles
        particles = []

        position = self.get_position('center')
        for _ in range(random.randint(4, 6)):
            new_position = [*position]
            new_position[0] += random.randint(-125, 125)
            new_position[1] += random.randint(-100, -75)

            size = random.randint(3, 5)
            color = self.image.get_at((random.randint(0, self.image.get_width() - 1), random.randint(0, self.image.get_height() - 1)))
            if color[3] == 0:
                color = self.image.get_at((self.image.get_width() // 2, self.image.get_height() // 2))

            particle = PolygonParticle(
                self.index + 1, random.randint(70, 100),
                [position, new_position],
                [[[-size, size], [-size, -size], [size, -size], [size, size]], [[0, 0], [0, 0], [0, 0], [0, 0]]],
                color=color, beziers=['ease_out', 'ease_in'], gravity=random.uniform(1.5, 2.5)
            )

            particles.append(particle)

        game.particles.extend(particles)

    def attack(self, game):
        game.player.on_damaged(game, self.power, self.knockback * -1 if game.player.rect.x < self.rect.x else 1)

    def update(self, game):
        if self.attack_cooldown <= 0 and self.rect.colliderect(game.player.rect) and not game.player.dead:
            self.attack_cooldown = self.attack_cooldown_limit
            self.attack(game)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1 * game.delta_time

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
        
        if self not in game.player.combat_tags and not game.entity_rect.colliderect(self.rect):
            self.despawn -= 1 * game.delta_time
        elif self.despawn != self.despawn_timer:
            self.despawn = self.despawn_timer

        if self.despawn <= 0:
            game.enemies[1].remove(self)

    def render(self, surface):
        surface.blit(self.image, self.image.get_rect(center=self.rect.center))
        self.healthbar.render(surface)

        if self.image_pulse_frames[0] > 0 and self.pulse_image:
            surface.blit(self.pulse_image, self.pulse_image.get_rect(center=self.rect.center))

class Target(Enemy):
    def __init__(self, position, index):
        image = pygame.image.load(os.path.join(ENEMY_PATH, 'target-s', 'target-s.png')).convert_alpha()
        image = scale(image, 2)

        super().__init__(position, image, index)

        self.enemy_type = 'stationary'

        self.level = 1
        
        self.max_health = 3
        self.health = self.max_health
        self.power = 1

        self.knockback = 3
        self.weight = -1

ENEMIES = generate_import_dict('Enemy')
