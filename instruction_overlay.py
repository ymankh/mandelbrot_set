from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import numpy as np
import moderngl
from moderngl_window.text.bitmapped import TextWriter2D


_TEXT_VERTEX_SHADER = """
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

_TEXT_GEOMETRY_SHADER = """
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

_TEXT_FRAGMENT_SHADER = """
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


class InstructionOverlay:
    """Reusable overlay that renders a fading instruction panel."""

    def __init__(
        self,
        ctx: moderngl.Context,
        instructions: Sequence[str],
        *,
        text_size: float = 22.0,
        hold_time: float = 3.0,
        fade_time: float = 2.5,
        margin: Tuple[int, int] = (36, 36),
        padding: int = 18,
    ) -> None:
        self.ctx = ctx
        self._instructions = list(instructions)
        self._text_size = text_size
        self._hold_time = hold_time
        self._fade_time = fade_time
        self._margin = margin
        self._padding = padding

        self._writers = [self._create_writer(line) for line in self._instructions]
        self._time = 0.0
        self._alpha = 1.0

        base_line_spacing = int(self._text_size * 1.35)
        self._base_line_spacing = max(1, base_line_spacing)
        self._base_char_width = self._resolve_char_width(self._writers, self._text_size)
        self._max_chars = max((len(line) for line in self._instructions), default=0)

        self._text_program = self.ctx.program(
            vertex_shader=_TEXT_VERTEX_SHADER,
            geometry_shader=_TEXT_GEOMETRY_SHADER,
            fragment_shader=_TEXT_FRAGMENT_SHADER,
        )
        self._text_program["text_color"].value = (1.0, 1.0, 1.0, 1.0)
        for writer in self._writers:
            writer._program = self._text_program  # type: ignore[attr-defined]

        self._panel_program = self.ctx.program(
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
            """,
        )
        self._panel_quad = self.ctx.buffer(reserve=4 * 2 * 4)
        self._panel_vao = self.ctx.simple_vertex_array(self._panel_program, self._panel_quad, "in_pos")

    @staticmethod
    def _create_writer(text: str) -> TextWriter2D:
        writer = TextWriter2D()
        writer.text = text
        return writer

    @staticmethod
    def _resolve_char_width(writers: Iterable[TextWriter2D], text_size: float) -> float:
        for writer in writers:
            meta = getattr(writer, "_meta", None)
            if meta and hasattr(meta, "char_aspect_wh"):
                return float(meta.char_aspect_wh) * text_size
        return text_size * 0.6

    def update(self, frame_time: float) -> None:
        if self._alpha <= 0.0:
            return
        self._time += frame_time
        if self._time > self._hold_time:
            denom = max(self._fade_time, 1e-6)
            progress = (self._time - self._hold_time) / denom
            self._alpha = max(0.0, 1.0 - progress)

    def reset(self) -> None:
        """Restart the overlay timers and fade."""
        self._time = 0.0
        self._alpha = 1.0

    def draw(self, wnd) -> None:
        if self._alpha <= 0.0 or not self._writers:
            return

        width, height = wnd.buffer_size
        if not width or not height:
            return

        margin_x, margin_y = self._margin
        padding = self._padding

        lines = len(self._writers)
        base_text_size = self._text_size
        base_line_spacing = self._base_line_spacing
        base_char_width = self._base_char_width

        total_height = base_text_size + (lines - 1) * base_line_spacing
        total_width = self._max_chars * base_char_width

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
        total_width = self._max_chars * char_width

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

        quad = np.array(
            [
                left - padding,
                bottom - padding,
                left - padding,
                top + padding,
                right + padding,
                bottom - padding,
                right + padding,
                top + padding,
            ],
            dtype="f4",
        )
        self._panel_quad.write(quad.tobytes())
        self._panel_program["viewport"].value = (float(width), float(height))
        self._panel_program["color"].value = (0.05, 0.05, 0.05, 0.7 * self._alpha)

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self._panel_vao.render(moderngl.TRIANGLE_STRIP)

        self._text_program["text_color"].value = (1.0, 1.0, 1.0, self._alpha)

        char_center_x = left + char_width / 2.0
        for index, writer in enumerate(self._writers):
            y_top = top - index * line_spacing
            center_y = y_top - text_size / 2.0
            writer.draw((char_center_x, center_y), size=text_size)

        self.ctx.blend_func = moderngl.ONE, moderngl.ZERO
        self.ctx.disable(moderngl.BLEND)
