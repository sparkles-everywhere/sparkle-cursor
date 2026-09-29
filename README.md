# Cursor Comet

A mouse-following sparkle/comet overlay for Linux + X11.

## Description

Cursor Comet creates a beautiful particle trail that follows your mouse cursor. The overlay is completely mouse-transparent, so it won't interfere with your normal mouse clicks or other desktop effects.

## Features

- **Particle Trail**: Sparkles and stars follow your cursor movement
- **Customizable**: Easily adjust colors, particle count, size, and physics
- **Mouse-Transparent**: Click-through overlay that doesn't block interactions
- **X11 Support**: Designed for XFCE and other X11-based desktop environments
- **Composited Desktops**: Requires a compositor for transparency effects

## Requirements

- Linux with X11
- Composited desktop environment (e.g., XFCE with compton/picom)
- Python 3

## Dependencies

- `python3-gi`
- `python3-cairo`
- `gir1.2-gtk-3.0`
- `libxfixes3`

### Installation (Debian/Ubuntu)

```bash
sudo apt install python3-gi python3-cairo gir1.2-gtk-3.0 libxfixes3
```

## Usage

Make the script executable:
```
chmod +x msp.py
```
<br>
<b>REMEMBER TO MODIFY THE SERVICE FILE BEFORE YOU MOVE IT.</b><br>
Move the service file to your user systemd directory:

```
mv msp.service ~/.config/systemd/user/
```
<br>
Reload the systemd user daemon and start the service:

```
systemctl --user daemon-reload
systemctl --user enable --now msp.service
```
<br>
Stop the script:

```
systemctl --user stop msp.service
```
<br>
Restart the script if you modify the configuration:

```
systemctl --user restart msp.service
```


## Configuration

Edit the configuration section at the top of `msp.py` to customize the effect:

### Particle Settings

- `MAX_PARTICLES` (default: 100) - Maximum particles on screen
- `FPS` (default: 30) - Animation update rate
- `PARTICLES_PER_MOVE` (default: 3) - Particles spawned per movement
- `MIN_MOVE_DISTANCE` (default: 5.0) - Minimum cursor movement before spawning

### Particle Physics

- `MIN_LIFETIME` / `MAX_LIFETIME` (default: 0.7-1.5) - Particle lifespan in seconds
- `MIN_SIZE` / `MAX_SIZE` (default: 1.2-3.2) - Particle size range
- `DRIFT` (default: 22.0) - Sideways drift amount
- `VELOCITY_INHERIT` (default: 0.58) - How strongly particles inherit cursor velocity
- `GRAVITY` (default: 10.0) - Downward pull (negative values float upward)

### Visual Effects

- `GLOW` (default: True) - Enable/disable particle glow
- `STAR_CHANCE` (default: 0.05) - Probability of spawning a star sparkle
- `STAR_MIN_SIZE` / `STAR_MAX_SIZE` (default: 3.0-6.0) - Star size range

### Colors

Set `COLOR` to an RGB tuple (values 0.0-1.0):

```python
# White
COLOR = (1.0, 1.0, 1.0)

# Pink
COLOR = (1.0, 0.35, 0.75)

# Cyan
COLOR = (0.25, 0.9, 1.0)

# Purple
COLOR = (0.7, 0.35, 1.0)
```

Use `COLOR_VARIATION` (default: 0.15) to add slight color variation between particles.

## Troubleshooting

**"Your X11 compositor does not appear to support RGBA windows"**

Ensure you have a compositor running. For XFCE, install and run `compton` or `picom`:

```bash
sudo apt install compton
compton --config ~/.config/compton.conf
```

**"This program requires X11"**

Cursor Comet only supports X11. It will not work on Wayland.

**Overlay not visible**

- Check that your compositor is running
- Verify the script is running without errors
- Try adjusting the `COLOR` value to ensure contrast with your background
