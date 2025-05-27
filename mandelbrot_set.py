import numpy as np

import moderngl
from ported._example import Example


def lerp(a, b):
    return a + (b-a) * 0.05


class Fractal(Example):
    title = "Mandelbrot"
    gl_version = (3, 3)
    resource_dir = 'shaders'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prog = self.load_program(vertex_shader='vertex_shader.glsl',
                                      fragment_shader='fragment_shader.glsl')

        self.center = self.prog['Center']
        self.scale = self.prog['Scale']
        self.ratio = self.prog['Ratio']
        self.iter = self.prog['Iter']
        self.power = self.prog['Power']
        self.type = self.prog['Type']
        self.JuliaC = self.prog['JuliaC']
        self.texture = self.load_texture_2d('pal.png')
        self.center.value = (0.5, 0.0)
        self.JuliaC.value = (-0.8, 0.156)
        self.new_JuliaC = self.JuliaC.value
        self.type.value = 0
        self.iter.value = 100
        self.scale.value = 1.25
        self.power.value = 1.0
        self.ratio.value = self.aspect_ratio
        self.zoom = 1
        self.new_center = self.center.value
        self.new_power = 2.0

        vertices = np.array([-1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0])

        self.vbo = self.ctx.buffer(vertices.astype('f4'))
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')

        self.going_right = False
        self.going_left = False
        self.going_up = False
        self.going_down = False
        self.is_zooming = False
        self.is_shrinking = False
        self.power_increase = False
        self.power_decrees = False
        self.iter_increase = False
        self.iter_decrease = False

    def on_render(self, time, frame_time):
        self.ctx.clear(1.0, 1.0, 1.0)
        self.texture.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # movement
        value = self.new_center
        scale = self.scale.value * frame_time
        if self.going_right:
            value = (value[0] - scale, value[1])
        if self.going_left:
            value = (value[0] + scale, value[1])
        if self.going_up:
            value = (value[0], value[1] - scale)
        if self.going_down:
            value = (value[0], value[1] + scale)
        self.new_center = value
        x, y = self.center.value
        new_x, new_y = self.new_center
        self.center.value = (lerp(x, new_x),
                             lerp(y, new_y))

        # zooming
        if self.is_zooming or self.is_shrinking:
            if self.is_zooming:
                self.zoom = lerp(self.zoom, 0.99)
            if self.is_shrinking:
                self.zoom = lerp(self.zoom, 1/0.99)
        else:
            self.zoom = lerp(self.zoom, 1)

        # power
        if self.power_increase or self.power_decrees:
            if self.power_increase:
                self.new_power += frame_time
            if self.power_decrees:
                self.new_power -= frame_time
        self.power.value = lerp(self.power.value, self.new_power)

        self.scale.value *= self.zoom

        x, y = self.JuliaC.value
        new_x, new_y = self.new_JuliaC
        self.JuliaC.value = (lerp(x, new_x),
                             lerp(y, new_y))

        # lope iterations (accuracy)
        if self.iter_increase:
            self.iter.value += 1
        if self.iter_decrease:
            self.iter.value -= 1

    def mouse_press_event(self, x, y, button):
        if button == 1:
            self.new_JuliaC = (
                x * 2 / self.window_size[0] - 1, y * 2 / self.window_size[1] - 1)

    def key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        scale = self.scale.value
        # Key presses
        if action == keys.ACTION_PRESS:
            if key == keys.D:
                self.going_right = True
            if key == keys.A:
                self.going_left = True
            if key == keys.W:
                self.going_up = True
            if key == keys.S:
                self.going_down = True
            if key == keys.Z:
                self.is_zooming = True
            if key == keys.X:
                self.is_shrinking = True
            if key == keys.P:
                self.power_increase = True
            if key == keys.O:
                self.power_decrees = True
            if key == keys.K:
                self.iter_increase = True
            if key == keys.L:
                self.iter_decrease = True
            if key == keys.M:
                self.type.value = (self.type.value + 1) % 8

         # Key release
        if action == keys.ACTION_RELEASE:
            if key == keys.D:
                self.going_right = False
            if key == keys.A:
                self.going_left = False
            if key == keys.W:
                self.going_up = False
            if key == keys.S:
                self.going_down = False
            if key == keys.Z:
                self.is_zooming = False
            if key == keys.X:
                self.is_shrinking = False
            if key == keys.P:
                self.power_increase = False
            if key == keys.O:
                self.power_decrees = False
            if key == keys.K:
                self.iter_increase = False
            if key == keys.L:
                self.iter_decrease = False


if __name__ == '__main__':
    Fractal.run()
