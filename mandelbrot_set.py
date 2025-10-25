import numpy as np

import moderngl
from moderngl_window.text.bitmapped import TextWriter2D
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

        instructions = [
            "Controls:",
            "  Mouse click sets Julia seed",
            "  WASD pans the view",
            "  Z / X zoom in or out",
            "  P / O adjust fractal power",
            "  K / L tweak iteration depth",
            "  M cycles fractal styles",
        ]
        self._instruction_writers = []
        for line in instructions:
            writer = TextWriter2D()
            writer.text = line
            self._instruction_writers.append(writer)
        self._instruction_time = 0.0
        self._instruction_hold = 3.0
        self._instruction_fade = 2.5
        self._instruction_alpha = 1.0
        self._instruction_text_size = 22.0
        self._instruction_line_spacing = int(self._instruction_text_size * 1.35)
        self._instruction_margin = (36, 36)  # (x, y) padding from window edges
        self._instruction_padding = 18
        if self._instruction_writers and getattr(self._instruction_writers[0], "_meta", None):
            meta = self._instruction_writers[0]._meta  # type: ignore[attr-defined]
            self._instruction_char_width = meta.char_aspect_wh * self._instruction_text_size
        else:
            self._instruction_char_width = self._instruction_text_size * 0.6
        self._instruction_max_chars = max(len(line) for line in instructions)

        text_vertex_shader = """
            #version 330

            in vec3 in_position;
            in uint in_char_id;

            uniform vec2 char_size;

            out uint vs_char_id;

            void main() {
                float xpos = gl_InstanceID * char_size.x;
                gl_Position = vec4(in_position + vec3(xpos, 0.0, 0.0), 1.0);
                vs_char_id = in_char_id;
            }
        """
        text_geometry_shader = """
            #version 330

            layout (points) in;
            layout (triangle_strip, max_vertices = 4) out;

            uniform mat4 m_proj;
            uniform vec2 text_pos;
            uniform vec2 char_size;

            in uint vs_char_id[1];
            out vec2 uv;
            flat out uint gs_char_id;

            void main() {
                vec3 pos = gl_in[0].gl_Position.xyz + vec3(text_pos, 0.0);

                vec3 right = vec3(1.0, 0.0, 0.0) * char_size.x / 2.0;
                vec3 up = vec3(0.0, 1.0, 0.0) * char_size.y / 2.0;

                uv = vec2(1.0, 1.0);
                gs_char_id = vs_char_id[0];
                gl_Position = m_proj * vec4(pos + (right + up), 1.0);
                EmitVertex();

                uv = vec2(0.0, 1.0);
                gs_char_id = vs_char_id[0];
                gl_Position = m_proj * vec4(pos + (-right + up), 1.0);
                EmitVertex();

                uv = vec2(1.0, 0.0);
                gs_char_id = vs_char_id[0];
                gl_Position = m_proj * vec4(pos + (right - up), 1.0);
                EmitVertex();

                uv = vec2(0.0, 0.0);
                gs_char_id = vs_char_id[0];
                gl_Position = m_proj * vec4(pos + (-right - up), 1.0);
                EmitVertex();

                EndPrimitive();
            }
        """
        text_fragment_shader = """
            #version 330

            uniform sampler2DArray font_texture;
            uniform vec4 text_color;

            in vec2 uv;
            flat in uint gs_char_id;

            out vec4 fragColor;

            void main() {
                vec4 base = texture(font_texture, vec3(uv, gs_char_id));
                fragColor = base * text_color;
            }
        """

        self._instruction_text_program = self.ctx.program(
            vertex_shader=text_vertex_shader,
            geometry_shader=text_geometry_shader,
            fragment_shader=text_fragment_shader,
        )
        self._instruction_text_program['text_color'].value = (1.0, 1.0, 1.0, 1.0)
        for writer in self._instruction_writers:
            writer._program = self._instruction_text_program  # type: ignore[attr-defined]
        # Simple quad shader for the instruction overlay background panel
        self._instruction_prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_pos;
                uniform vec2 viewport;
                void main() {
                    vec2 ndc = vec2(
                        (in_pos.x / viewport.x) * 2.0 - 1.0,
                        (in_pos.y / viewport.y) * 2.0 - 1.0
                    );
                    gl_Position = vec4(ndc, 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                uniform vec4 color;
                out vec4 fragColor;
                void main() {
                    fragColor = color;
                }
            """
        )
        self._instruction_quad = self.ctx.buffer(reserve=4 * 2 * 4)
        self._instruction_vao = self.ctx.simple_vertex_array(self._instruction_prog, self._instruction_quad, 'in_pos')

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

        self._update_instruction_overlay(frame_time)
        if self._instruction_alpha > 0.0:
            self._draw_instruction_overlay()

    def on_mouse_press_event(self, x, y, button):
        if button == self.wnd.mouse.left:
            width, height = self.wnd.size
            if width and height:
                self.new_JuliaC = (
                    x * 2 / width - 1,
                    y * 2 / height - 1,
                )

    def on_key_event(self, key, action, modifiers):
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

    def _update_instruction_overlay(self, frame_time):
        if self._instruction_alpha <= 0.0:
            return
        self._instruction_time += frame_time
        if self._instruction_time > self._instruction_hold:
            progress = (self._instruction_time - self._instruction_hold) / max(self._instruction_fade, 1e-6)
            self._instruction_alpha = max(0.0, 1.0 - progress)

    def _draw_instruction_overlay(self):
        width, height = self.wnd.buffer_size
        if not width or not height or not self._instruction_writers:
            return

        margin_x, margin_y = self._instruction_margin
        padding = self._instruction_padding

        base_text_size = self._instruction_text_size
        base_line_spacing = self._instruction_line_spacing
        base_char_width = self._instruction_char_width
        lines = len(self._instruction_writers)

        total_height = base_text_size + (lines - 1) * base_line_spacing
        total_width = self._instruction_max_chars * base_char_width

        available_width = max(width - 2 * margin_x, 50)
        available_height = max(height - 2 * margin_y, 50)

        denom_width = total_width + 2 * padding
        denom_height = total_height + 2 * padding
        scale_width = available_width / denom_width if denom_width > 0 else 1.0
        scale_height = available_height / denom_height if denom_height > 0 else 1.0
        scale = min(1.0, scale_width, scale_height)
        scale = max(scale, 0.4)

        text_size = base_text_size * scale
        char_width = base_char_width * scale
        line_spacing = max(1.0, base_line_spacing * scale)
        total_height = text_size + (lines - 1) * line_spacing
        total_width = self._instruction_max_chars * char_width

        top = height - margin_y
        bottom = top - total_height
        bottom = max(bottom, padding)
        left = margin_x
        right = left + total_width

        max_right_edge = width - margin_x
        overshoot = (right + padding) - max_right_edge
        if overshoot > 0:
            left = max(padding, left - overshoot)
            right = left + total_width

        quad = np.array([
            left - padding, bottom - padding,
            left - padding, top + padding,
            right + padding, bottom - padding,
            right + padding, top + padding,
        ], dtype='f4')
        self._instruction_quad.write(quad.tobytes())
        self._instruction_prog['viewport'].value = (float(width), float(height))
        self._instruction_prog['color'].value = (0.05, 0.05, 0.05, 0.7 * self._instruction_alpha)

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self._instruction_vao.render(moderngl.TRIANGLE_STRIP)

        self._instruction_text_program['text_color'].value = (1.0, 1.0, 1.0, self._instruction_alpha)

        char_center_x = left + char_width / 2.0
        for index, writer in enumerate(self._instruction_writers):
            y_top = top - index * line_spacing
            center_y = y_top - text_size / 2.0
            writer.draw((char_center_x, center_y), size=text_size)

        # Reset to default state so the fractal draw pass remains unaffected.
        self.ctx.blend_func = moderngl.ONE, moderngl.ZERO
        self.ctx.disable(moderngl.BLEND)


if __name__ == '__main__':
    Fractal.run()
