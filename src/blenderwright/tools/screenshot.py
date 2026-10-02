"""MCP tool for capturing Blender viewport screenshots."""

import base64

from mcp.server.fastmcp import Image

from blenderwright.connection import BlenderConnection
from blenderwright.server import mcp, get_connection
from blenderwright.validators import validate_numeric_range, validate_enum

# Allowed screenshot capture modes
ALLOWED_SCREENSHOT_MODES = {"fast", "full"}


@mcp.tool()
def get_viewport_screenshot(
    max_size: int = 1000,
    mode: str = "fast",
) -> Image:
    """Capture a screenshot of the current Blender 3D viewport.

    Args:
        max_size: Maximum size in pixels for the largest dimension (default: 1000).
        mode: Capture mode - 'fast' for instant viewport capture using OpenGL
            (default), 'full' for a complete render through the active render
            engine. 'fast' falls back to 'full' when Blender has no viewport
            (headless).

    Returns:
        The PNG image.
    """
    max_size = validate_numeric_range(max_size, min_val=64, max_val=4096, name="max_size")
    validate_enum(mode, ALLOWED_SCREENSHOT_MODES, name="mode")

    # Calculate dimensions maintaining roughly 16:9 aspect
    width = max_size
    height = int(max_size * 9 / 16)
    if height > max_size:
        height = max_size
        width = int(max_size * 16 / 9)

    conn = get_connection()

    params = {"width": width, "height": height}
    if mode == "fast":
        response = conn.send_command("fast_viewport_capture", params)
        # No usable viewport (headless, no OpenGL context): render through the camera instead.
        if response.get("status") == "error":
            mode = "full"
    if mode == "full":
        response = conn.send_command(
            "capture_viewport", params, timeout=BlenderConnection.RENDER_TIMEOUT
        )
    if response.get("status") == "error":
        raise RuntimeError(f"Screenshot failed: {response.get('result')}")

    # A real image block: base64 inside a JSON dict reaches the model as plain text.
    return Image(data=base64.b64decode(response["result"]["base64"]), format="png")
