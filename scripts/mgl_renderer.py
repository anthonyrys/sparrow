from scripts import SCREEN_DIMENSIONS

import moderngl
import array
import os

class MglRenderer(object):
    def __init__(self, game, context):
        self.game = game

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

        self.create(context)
        self.main_array = context.vertex_array(
            self.programs['main'],
            [(self.main_buffer, '2f 2f', 'v_Position', 'v_TexCoords')]
        )

    def create(self, context):
        self.programs['main'] = context.program(
            vertex_shader=self.shaders['vert']['main'],
            fragment_shader=self.shaders['frag']['main']
        )
        
        self.programs['main']['dim_f'] = 0
        self.programs['main']['entity'] = 0
        self.programs['main']['ui'] = 1
    
    def update(self):
        self.programs['main']['dim_f'].value = self.game.dim

    def render(self):
        self.textures['entity'].write(self.game.entity_display.get_view('1'))
        self.textures['ui'].write(self.game.ui_display.get_view('1'))
    
        self.main_array.render(moderngl.TRIANGLE_STRIP)
