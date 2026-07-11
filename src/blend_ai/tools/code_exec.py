"""MCP tool for executing Python code in Blender's sandboxed environment."""

from typing import Any

from blend_ai.server import mcp, get_connection


@mcp.tool()
def execute_blender_code(
    code: str,
    max_exec_time: float = 30.0,
) -> dict[str, Any]:
    """Execute Python code inside Blender's sandboxed environment.

    The code runs in a restricted sandbox that blocks dangerous imports
    (os, subprocess, socket, etc.) and dangerous builtins (exec, eval, open).
    Safe Blender modules are pre-loaded: bpy, bmesh, math, Vector, Matrix,
    Euler, Quaternion, Color.

    Args:
        code: Python code to execute.
        max_exec_time: Maximum execution time in seconds (default: 30.0).

    Returns:
        Dict with 'output' (captured stdout), 'success' boolean,
        and 'exec_time_ms'.
    """
    if not code or not code.strip():
        raise ValueError("No code provided")

    conn = get_connection()
    response = conn.send_command("execute_code", {
        "code": code, "max_exec_time": max_exec_time
    })
    if response.get("status") == "error":
        raise RuntimeError(f"Blender error: {response.get('result')}")
    return response.get("result")


@mcp.tool()
def reload_modules() -> dict[str, Any]:
    """Force-reload all addon modules without restarting Blender.

    Use after editing handler Python files on disk to pick up changes
    without disabling/re-enabling the addon.

    Returns:
        Dict with reload confirmation and module count.
    """
    conn = get_connection()
    response = conn.send_command("reload_modules", {})
    if response.get("status") == "error":
        raise RuntimeError(f"Blender error: {response.get('result')}")
    return response.get("result")


@mcp.tool()
def lattice_deform(
    name: str,
    resolution: list[int] | tuple[int, ...] = (4, 4, 4),
) -> dict[str, Any]:
    """Add a lattice modifier for non-destructive organic deformation.

    Creates a lattice cage around the object. Edit the lattice points
    (in Blender's edit mode on the lattice) to deform the mesh smoothly.
    Perfect for shaping heads, torsos, and organic forms.

    Args:
        name: Name of the mesh object to deform.
        resolution: [U, V, W] lattice divisions (default: [4,4,4])

    Returns:
        Dict with object, lattice name, and success status.
    """
    if not name:
        raise ValueError("name is required")

    conn = get_connection()
    response = conn.send_command("lattice_deform", {
        "name": name, "resolution": list(resolution)
    })
    if response.get("status") == "error":
        raise RuntimeError(f"Blender error: {response.get('result')}")
    return response.get("result")
