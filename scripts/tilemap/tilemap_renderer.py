from scripts.sprites import Sprites

from scripts.npcs import FRIENDLIES
from scripts.tilemap import TILES
from scripts.utils import load_spritesheet

import pygame
import json
import os

TILEMAP_FOLDER_PATH = os.path.join('resources', 'tilemaps')

class TilemapRenderer(object):
    def __init__(self, game):
        self.game = game

        self.chunk_dimensions = (15, 15)
        self.chunk_keys = None
        self.chunk_rects = {}
        self.chunks = {}

        # Rendered prior to the player
        self.decor_a = Sprites()
        self.friendlies = Sprites()

        # Rendered after the player
        self.tiles = Sprites()
        self.renderable_tiles = []
        self.decor_b = Sprites()

        self.flags = None
        self.enemies = None

        self.tile_size = (0, 0)
        self.tilemap_size = (0, 0)

    def update(self):
        self.renderable_tiles = []
        for tile in self.tiles:
            if tile.rect.colliderect(self.game.entity_rect):
                self.renderable_tiles.append(tile)

        for friendly in self.friendlies:
            friendly.update(self.game)

    def render_a(self):
        for friendly in self.friendlies:
            friendly.render(self.game.entity_surface)

    def render_b(self):
        for tile in self.renderable_tiles:
            if tile.sprite_id == 'Barrier':
                continue

            tile.render(self.game.entity_surface)

    def load(self, name):
        path = os.path.join(TILEMAP_FOLDER_PATH, name)

        with open(os.path.join(path, 'tilemap.json')) as t:
            data = json.load(t)

        dimensions = [
            data['config']['tile']['dimensions'][0] * data['config']['tilemap']['dimensions'][0],
            data['config']['tile']['dimensions'][1] * data['config']['tilemap']['dimensions'][1]
        ]

        self.tile_size = data['config']['tile']['dimensions']
        self.tilemap_size = dimensions

        surface = pygame.Surface(dimensions).convert_alpha()
        surface.set_colorkey((0, 0, 0))

        friendlies = []
        tiles = []

        flags = {}
        enemies = {}

        images = {}
        for image in data['config']['images']:
            images[image] = {}
            images[image]['imgs'] = load_spritesheet(os.path.join(path, data['config']['images'][image]['path']), scale=2)
            images[image]['tiles'] = data['config']['images'][image]['tiles']

        self.chunk_rects = {}
        self.chunks = {}

        # Create chunks
        x, y = 0, 0
        while y < dimensions[1]:
            while x < dimensions[0]:
                rect = pygame.Rect(x, y, data['config']['tile']['dimensions'][0] * self.chunk_dimensions[0], data['config']['tile']['dimensions'][1] * self.chunk_dimensions[1])
                self.chunk_rects[(x, y)] = rect
                self.chunks[(x, y)] = []

                x += rect.width

            y += rect.height
            x = 0

        self.chunk_keys = tuple(self.chunk_rects.keys())

        # Create tiles
        for tile_data in data['tiles']:
            if tile_data['tileset'] == 'flags':
                if tile_data['tile'] not in flags:
                    flags[tile_data['tile']] = []

                flags[tile_data['tile']].append(tile_data['position'])

            elif tile_data['tileset'] == 'enemies':
                if tile_data['tile'] not in enemies:
                    enemies[tile_data['tile']] = []

                enemies[tile_data['tile']].append(tile_data['position'])
        
            elif tile_data['tileset'] == 'friendlies':
                friendly = FRIENDLIES[tile_data['tile']](
                    tile_data['position'],
                    tile_data['strata']
                )

                friendlies.append(friendly)

            elif tile_data['tile'] in TILES.keys():
                img = images[tile_data['tileset']]['imgs'][tile_data['index']].copy()
                img = pygame.transform.rotate(img, -tile_data['orientation'])
                img = pygame.transform.flip(img, tile_data['flipped'], False)

                tile = TILES[tile_data['tile']](
                    tile_data['position'],
                    img,
                    tile_data['strata']
                )

                for point in self.chunk_rects:
                    if self.chunk_rects[point].colliderect(tile.rect):
                        self.chunks[point].append(tile)
                        break

                tiles.append(tile)

            else:
                print(f'[LOAD_TILEMAP] Cannot resolve tile type: {tile_data["tile"]}')

        self.game.entity_surface = surface

        self.friendlies.clear()
        self.friendlies.extend(friendlies)

        self.tiles.clear()
        self.tiles.extend(tiles)

        self.flags = flags
        self.enemies = enemies
