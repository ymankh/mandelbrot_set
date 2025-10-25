# Mandelbrot Set Generator

## Overview

This real-time viewer renders the Mandelbrot and related Julia fractals using ModernGL. A lightweight overlay explains the interactive controls, and smooth easing keeps panning, zooming, and palette exploration fluid. You can jump between preset fractal powers, drag the Julia seed directly in the viewport, or reset to the default framing in a single key press.

## Getting Started

The project is configured for the `uv` package manager (https://github.com/astral-sh/uv), which handles dependency resolution and virtual environments automatically.

1. Clone the repository and enter the directory:

   ```bash
   git clone https://github.com/ymankh/mandelbrot_set.git
   cd mandelbrot_set
   ```

2. Launch the viewer with uv (this will create/manage the venv on first run):

   ```bash
   uv run mandelbrot_set.py
   ```

   Alternatively, you can install dependencies manually:

   ```bash
   pip install -r requirements.txt
   python mandelbrot_set.py
   ```

## Controls

- **Mouse left click / drag**: Pick a Julia seed (updates continuously while held).
- **Z / X**: Smoothly zoom in or out.
- **R**: Glide back to the default view.
- **P / O**: Nudge the fractal power up or down.
- **Number keys 1–9**: Set a target power (transitions via easing).
- **K / L**: Increase or decrease the iteration depth.
- **M**: Cycle through alternate fractal modes.
- **A / W / S / D**: Pan the view (left, up, down, right).

Experiment with the controls to explore the classic Mandelbrot set, step through alternative power formulas, or drag the Julia seed to discover entirely new shapes. The easing-based transitions prevent jarring jumps and make it easier to keep your place while navigating deep zooms.

## Credits

This Mandelbrot set generator was created by [Yaman AlKhashashneh](https://github.com/ymankh).
