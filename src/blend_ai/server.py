"""MCP Server entry point for blend-ai."""

from mcp.server.fastmcp import FastMCP
from blend_ai.connection import BlenderConnection

# Create the MCP server
_mcp: FastMCP | None = None
_connection: BlenderConnection | None = None


def get_connection() -> BlenderConnection:
    """Get or create the global Blender connection."""
    global _connection
    if _connection is None:
        _connection = BlenderConnection()
    return _connection


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    global _mcp
    if _mcp is not None:
        return _mcp
    
    mcp = FastMCP(
        "blend-ai",
        instructions="The most intuitive and efficient MCP Server for Blender",
    )
    
    # CRITICAL: Set module's mcp before importing tool modules
    # Tool modules do 'from blend_ai.server import mcp' and need it to exist
    import sys
    this_mod = sys.modules[__name__]
    this_mod.mcp = mcp
    
    # Import ALL tool modules to register their decorators
    import blend_ai.tools.scene
    import blend_ai.tools.objects
    import blend_ai.tools.transforms
    import blend_ai.tools.modeling
    import blend_ai.tools.materials
    import blend_ai.tools.lighting
    import blend_ai.tools.camera
    import blend_ai.tools.animation
    import blend_ai.tools.rendering
    import blend_ai.tools.curves
    import blend_ai.tools.sculpting
    import blend_ai.tools.uv
    import blend_ai.tools.physics
    import blend_ai.tools.geometry_nodes
    import blend_ai.tools.armature
    import blend_ai.tools.collections
    import blend_ai.tools.file_ops
    import blend_ai.tools.viewport
    import blend_ai.tools.code_exec
    import blend_ai.tools.screenshot
    import blend_ai.tools.booltool
    import blend_ai.tools.mesh_editing
    import blend_ai.tools.mesh_quality
    import blend_ai.tools.gpencil
    
    # Import resources and prompts
    import blend_ai.resources.scene_info  # noqa: F401
    import blend_ai.prompts.workflows  # noqa: F401
    
    _mcp = mcp
    return mcp


mcp = create_server()


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
