#!/usr/bin/env python3

"""
Cursor Comet
============

A mouse-following sparkle/comet overlay for Linux + X11.

Designed for:
    - XFCE
    - X11
    - composited desktops

The window is completely mouse-transparent, so it should not interfere
with your existing sparkle overlay or normal mouse clicks.

Dependencies:
    python3-gi
    python3-cairo
    gir1.2-gtk-3.0
    libxfixes3

Debian/Ubuntu:
    sudo apt install python3-gi python3-cairo gir1.2-gtk-3.0 libxfixes3

Run:
    python3 cursor_comet.py

Stop:
    Ctrl+C in the terminal
"""

import math
import random
import signal
import time

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")

from gi.repository import Gtk, Gdk, GdkX11, GLib


# ============================================================
# CONFIGURATION
# ============================================================

# How many particles can exist at once.
MAX_PARTICLES = 100

# How frequently the animation updates.
FPS = 30

# How many particles are spawned per movement.
PARTICLES_PER_MOVE = 3

# Minimum distance the cursor must move before spawning particles.
# Lower = denser trail.
MIN_MOVE_DISTANCE = 5.0

# How long particles live, in seconds.
MIN_LIFETIME = 0.7
MAX_LIFETIME = 1.5

# Particle size.
MIN_SIZE = 1.2
MAX_SIZE = 3.2

# How much particles drift sideways.
DRIFT = 22.0

# How strongly particles inherit the cursor's movement.
VELOCITY_INHERIT = 0.58

# Gravity. Negative values make particles float upward.
GRAVITY = 10.0

# Glow strength.
GLOW = True

# Occasionally create a larger star-shaped sparkle.
STAR_CHANCE = 0.05

# Size of those star sparkles.
STAR_MIN_SIZE = 3.0
STAR_MAX_SIZE = 6.0

# ------------------------------------------------------------
# COLOR
# ------------------------------------------------------------
# RGB values from 0.0 to 1.0.
#
# Examples:
#
#   white:
#       (1.0, 1.0, 1.0)
#
#   pink:
#       (1.0, 0.35, 0.75)
#
#   cyan:
#       (0.25, 0.9, 1.0)
#
#   purple:
#       (0.7, 0.35, 1.0)

COLOR = (1.0, 1.0, 1.0)

# Optional second color for slight variation.
COLOR_VARIATION = 0.15


# ============================================================
# PARTICLE
# ============================================================

class Particle:
    def __init__(self, x, y, vx, vy, size, lifetime, star=False):
        self.x = x
        self.y = y

        self.vx = vx
        self.vy = vy

        self.size = size
        self.lifetime = lifetime
        self.age = 0.0

        self.star = star

        # Slight per-particle color variation.
        variation = random.uniform(-COLOR_VARIATION, COLOR_VARIATION)

        self.r = max(0.0, min(1.0, COLOR[0] + variation))
        self.g = max(0.0, min(1.0, COLOR[1] + variation))
        self.b = max(0.0, min(1.0, COLOR[2] + variation))

        self.rotation = random.uniform(0.0, math.tau)
        self.rotation_speed = random.uniform(-3.0, 3.0)

    @property
    def alive(self):
        return self.age < self.lifetime

    def update(self, dt):
        self.age += dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Gentle gravity.
        self.vy += GRAVITY * dt

        # Air resistance.
        self.vx *= 0.985
        self.vy *= 0.985

        self.rotation += self.rotation_speed * dt

    def draw(self, cr):
        if not self.alive:
            return

        # Normalized age.
        t = self.age / self.lifetime

        # Smooth fade:
        # bright near birth, then fades away.
        alpha = (1.0 - t) ** 1.7

        # Make the particle slightly shrink as it dies.
        size = self.size * (1.0 - 0.35 * t)

        r = self.r
        g = self.g
        b = self.b

        if self.star:
            draw_star(cr, self.x, self.y, size, self.rotation,
                      r, g, b, alpha)
        else:
            draw_sparkle(cr, self.x, self.y, size,
                         r, g, b, alpha)


# ============================================================
# DRAWING
# ============================================================

def draw_sparkle(cr, x, y, size, r, g, b, alpha):
    """Draw a tiny glowing point."""

    if GLOW:
        # Outer glow.
        gradient = cairo.RadialGradient(
            x, y, 0,
            x, y, size * 3.5
        )

        gradient.add_color_stop_rgba(
            0.0,
            r, g, b,
            alpha * 0.45
        )

        gradient.add_color_stop_rgba(
            1.0,
            r, g, b,
            0.0
        )

        cr.set_source(gradient)
        cr.arc(x, y, size * 3.5, 0, math.tau)
        cr.fill()

    # Bright core.
    cr.set_source_rgba(r, g, b, alpha)

    cr.arc(
        x,
        y,
        size,
        0,
        math.tau
    )

    cr.fill()


def draw_star(cr, x, y, size, rotation, r, g, b, alpha):
    """Draw a little four-point star."""

    if GLOW:
        gradient = cairo.RadialGradient(
            x, y, 0,
            x, y, size * 4.0
        )

        gradient.add_color_stop_rgba(
            0.0,
            r, g, b,
            alpha * 0.55
        )

        gradient.add_color_stop_rgba(
            1.0,
            r, g, b,
            0.0
        )

        cr.set_source(gradient)
        cr.arc(x, y, size * 4.0, 0, math.tau)
        cr.fill()

    cr.save()

    cr.translate(x, y)
    cr.rotate(rotation)

    cr.set_source_rgba(1.0, 1.0, 1.0, alpha)

    # Vertical diamond.
    cr.move_to(0, -size * 2.0)
    cr.line_to(size * 0.45, 0)
    cr.line_to(0, size * 2.0)
    cr.line_to(-size * 0.45, 0)
    cr.close_path()
    cr.fill()

    # Horizontal diamond.
    cr.move_to(-size * 2.0, 0)
    cr.line_to(0, size * 0.45)
    cr.line_to(size * 2.0, 0)
    cr.line_to(0, -size * 0.45)
    cr.close_path()
    cr.fill()

    cr.restore()


# ============================================================
# CURSOR POSITION
# ============================================================

def get_cursor_position():
    """
    Ask X11 for the current pointer position.

    Returns:
        (x, y)
    """

    display = Gdk.Display.get_default()

    if not isinstance(display, GdkX11.X11Display):
        raise RuntimeError("This program requires X11.")

    screen = display.get_default_screen()
    root = screen.get_root_window()

    pointer = root.get_pointer()

    # Gdk 3 returns:
    #
    #   (screen, x, y, mask)
    #
    # depending on version.
    #
    # We only need x/y.
    if len(pointer) >= 3:
        return float(pointer[1]), float(pointer[2])

    raise RuntimeError("Could not determine pointer position.")


# ============================================================
# COMET OVERLAY
# ============================================================

class CometOverlay:
    def __init__(self):
        self.particles = []

        self.mouse_x = 0.0
        self.mouse_y = 0.0

        self.last_mouse_x = None
        self.last_mouse_y = None

        self.last_time = time.monotonic()

        self.window = Gtk.Window(
            type=Gtk.WindowType.TOPLEVEL
        )

        self.window.set_title("Cursor Comet")

        self.window.set_decorated(False)
        self.window.set_resizable(False)

        self.window.set_keep_above(True)

        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)

        self.window.set_type_hint(Gdk.WindowTypeHint.UTILITY)

        self.window.set_accept_focus(False)
        self.window.set_focus_on_map(False)

        self.window.set_app_paintable(True)

        # ----------------------------------------------------
        # Transparent visual
        # ----------------------------------------------------

        screen = self.window.get_screen()

        rgba_visual = screen.get_rgba_visual()

        if rgba_visual is not None:
            self.window.set_visual(rgba_visual)
        else:
            print(
                "WARNING: Your X11 compositor does not appear "
                "to support RGBA windows."
            )

        # ----------------------------------------------------
        # Drawing
        # ----------------------------------------------------

        self.window.connect(
            "draw",
            self.on_draw
        )

        self.window.connect(
            "destroy",
            Gtk.main_quit
        )

        self.window.connect(
            "map",
            self.on_map
        )

        # ----------------------------------------------------
        # Full virtual desktop
        # ----------------------------------------------------

        self.window.fullscreen()

        self.window.show_all()

        # Re-apply click-through after the window is mapped
        GLib.idle_add(self.on_map, self.window)

        # Start animation.
        GLib.timeout_add(
            int(1000 / FPS),
            self.tick
        )

    # --------------------------------------------------------
    # CLICK-THROUGH
    # --------------------------------------------------------

    def on_map(self, widget):
        """
        Apply click-through after window is mapped.
        """
        gdk_window = self.window.get_window()

        if gdk_window is not None:
            # Click-through - set after window is mapped
            empty_region = cairo.Region()

            gdk_window.input_shape_combine_region(
                empty_region,
                0,
                0
            )

    # --------------------------------------------------------
    # PARTICLES
    # --------------------------------------------------------

    def spawn_particles(self, x, y, dx, dy):
        movement_speed = math.sqrt(
            dx * dx + dy * dy
        )

        for _ in range(PARTICLES_PER_MOVE):

            if len(self.particles) >= MAX_PARTICLES:
                break

            # Spawn particles slightly behind the cursor.
            if movement_speed > 0:
                length = math.sqrt(dx * dx + dy * dy)

                back_x = -dx / length
                back_y = -dy / length
            else:
                back_x = 0
                back_y = 0

            offset = random.uniform(0.0, 5.0)

            px = x + back_x * offset
            py = y + back_y * offset

            # Random direction.
            angle = random.uniform(
                0,
                math.tau
            )

            speed = random.uniform(
                5.0,
                35.0
            )

            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Give particles a little of the cursor's velocity.
            vx += dx * VELOCITY_INHERIT
            vy += dy * VELOCITY_INHERIT

            size = random.uniform(
                MIN_SIZE,
                MAX_SIZE
            )

            lifetime = random.uniform(
                MIN_LIFETIME,
                MAX_LIFETIME
            )

            star = (
                random.random() < STAR_CHANCE
            )

            if star:
                size = random.uniform(
                    STAR_MIN_SIZE,
                    STAR_MAX_SIZE
                )

            self.particles.append(
                Particle(
                    px,
                    py,
                    vx,
                    vy,
                    size,
                    lifetime,
                    star
                )
            )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def tick(self):
        now = time.monotonic()

        dt = now - self.last_time
        self.last_time = now

        # Avoid huge jumps if the process was suspended.
        dt = min(dt, 0.05)

        try:
            x, y = get_cursor_position()
        except Exception as exc:
            print(
                f"Could not read mouse position: {exc}"
            )
            return True

        self.mouse_x = x
        self.mouse_y = y

        # ----------------------------------------------------
        # Mouse movement
        # ----------------------------------------------------

        if self.last_mouse_x is None:
            self.last_mouse_x = x
            self.last_mouse_y = y

        dx = x - self.last_mouse_x
        dy = y - self.last_mouse_y

        distance = math.sqrt(
            dx * dx + dy * dy
        )

        if distance >= MIN_MOVE_DISTANCE:
            self.spawn_particles(
                x,
                y,
                dx,
                dy
            )

        self.last_mouse_x = x
        self.last_mouse_y = y

        # ----------------------------------------------------
        # Update particles
        # ----------------------------------------------------

        for particle in self.particles:
            particle.update(dt)

        # Remove dead particles.
        self.particles = [
            p for p in self.particles
            if p.alive
        ]

        # Redraw.
        self.window.queue_draw()

        return True

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    def on_draw(self, widget, cr):
        # Completely clear the window.
        cr.set_operator(
            cairo.OPERATOR_SOURCE
        )

        cr.set_source_rgba(
            0,
            0,
            0,
            0
        )

        cr.paint()

        # Switch back to normal alpha compositing.
        cr.set_operator(
            cairo.OPERATOR_OVER
        )

        for particle in self.particles:
            particle.draw(cr)

        return False


# ============================================================
# MAIN
# ============================================================

def main():
    # Make Ctrl+C work cleanly.
    def shutdown(signum, frame):
        Gtk.main_quit()

    signal.signal(
        signal.SIGINT,
        shutdown
    )

    signal.signal(
        signal.SIGTERM,
        shutdown
    )

    # Verify we're running under X11.
    display = Gdk.Display.get_default()

    if display is None:
        print(
            "ERROR: Could not connect to a graphical display."
        )
        return 1

    if not isinstance(display, GdkX11.X11Display):
        print(
            "ERROR: This program requires X11."
        )
        print(
            "Detected display is not an X11 display."
        )
        return 1

    overlay = CometOverlay()

    print("Cursor Comet running.")
    print("The overlay is completely click-through.")
    print("Press Ctrl+C to exit.")

    Gtk.main()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
