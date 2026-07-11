"""Blender addon handlers for object transform operations."""

import bpy
from .. import dispatcher

# Map origin type param to bpy.ops.object.origin_set type arg
_ORIGIN_TYPE_MAP = {
    "GEOMETRY": "ORIGIN_GEOMETRY",
    "CURSOR": "ORIGIN_CURSOR",
    "CENTER_OF_MASS": "ORIGIN_CENTER_OF_MASS",
    "CENTER_OF_VOLUME": "ORIGIN_CENTER_OF_VOLUME",
}


def handle_set_location(params: dict) -> dict:
    """Set the position of an object."""
    name = params.get("name")
    location = params.get("location")

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        obj.location = tuple(location)

        return {
            "name": obj.name,
            "location": list(obj.location),
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to set location for '{name}': {e}")


def handle_set_rotation(params: dict) -> dict:
    """Set the rotation of an object."""
    name = params.get("name")
    rotation = params.get("rotation")
    mode = params.get("mode", "EULER")

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        if mode == "QUATERNION":
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = tuple(rotation)
            return {
                "name": obj.name,
                "rotation_quaternion": list(obj.rotation_quaternion),
                "mode": "QUATERNION",
            }
        else:
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = tuple(rotation)
            return {
                "name": obj.name,
                "rotation_euler": list(obj.rotation_euler),
                "mode": "EULER",
            }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to set rotation for '{name}': {e}")


def handle_set_scale(params: dict) -> dict:
    """Set the scale of an object."""
    name = params.get("name")
    scale = params.get("scale")

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        obj.scale = tuple(scale)

        return {
            "name": obj.name,
            "scale": list(obj.scale),
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to set scale for '{name}': {e}")


def handle_apply_transforms(params: dict) -> dict:
    """Apply transforms on an object."""
    name = params.get("name")
    apply_location = params.get("location", True)
    apply_rotation = params.get("rotation", True)
    apply_scale = params.get("scale", True)

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        # Select and make active
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.transform_apply(
            location=apply_location,
            rotation=apply_rotation,
            scale=apply_scale,
        )

        return {
            "name": obj.name,
            "location": list(obj.location),
            "rotation_euler": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "applied": {
                "location": apply_location,
                "rotation": apply_rotation,
                "scale": apply_scale,
            },
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to apply transforms for '{name}': {e}")


def handle_set_origin(params: dict) -> dict:
    """Set the origin point of an object."""
    name = params.get("name")
    origin_type = params.get("type", "GEOMETRY")

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        bpy_type = _ORIGIN_TYPE_MAP.get(origin_type)
        if bpy_type is None:
            raise ValueError(f"Unknown origin type: {origin_type}")

        # Select and make active
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.origin_set(type=bpy_type)

        return {
            "name": obj.name,
            "origin_type": origin_type,
            "location": list(obj.location),
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to set origin for '{name}': {e}")


def handle_snap_to_grid(params: dict) -> dict:
    """Snap an object's location to the nearest grid point."""
    name = params.get("name")
    grid_size = params.get("grid_size", 1.0)

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        snapped = [round(v / grid_size) * grid_size for v in obj.location]
        obj.location = tuple(snapped)

        return {
            "name": obj.name,
            "location": list(obj.location),
            "grid_size": grid_size,
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to snap '{name}' to grid: {e}")


def handle_set_location_relative(params: dict) -> dict:
    """Move an object to a position relative to another object.

    Params:
        name: Object to move.
        target: Reference object name.
        offset: [dx, dy, dz] offset from target's location.
    """
    name = params.get("name")
    target_name = params.get("target")
    offset = tuple(params.get("offset", (0, 0, 0)))

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        target = bpy.data.objects.get(target_name)
        if target is None:
            raise ValueError(f"Target object '{target_name}' not found")

        target_loc = target.location
        obj.location = (target_loc.x + offset[0],
                        target_loc.y + offset[1],
                        target_loc.z + offset[2])

        return {
            "name": obj.name,
            "relative_to": target_name,
            "offset": list(offset),
            "location": list(obj.location),
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to set relative location for '{name}': {e}")


def handle_set_scale_origin(params: dict) -> dict:
    """Scale an object WITHOUT applying transforms (preserves location).

    Unlike set_scale + apply_transforms, this keeps the object's
    location and origin intact. Returns effective dimensions after scale.
    
    Params:
        name: Object name.
        scale: [sx, sy, sz] scale factors.
    """
    name = params.get("name")
    scale = tuple(params.get("scale", (1, 1, 1)))

    try:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise ValueError(f"Object '{name}' not found")

        # Store original dimensions for reference
        orig_dims = list(obj.dimensions)

        # Set scale (without applying transforms — location stays correct)
        obj.scale = scale

        # Calculate effective dimensions
        new_dims = [orig_dims[i] * scale[i] for i in range(3)]

        return {
            "name": obj.name,
            "scale": list(obj.scale),
            "location": list(obj.location),
            "dimensions_before": orig_dims,
            "dimensions_after": [round(d, 4) for d in obj.dimensions],
        }
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to scale '{name}' preserving origin: {e}")


def register():
    """Register transform handlers with the dispatcher."""
    dispatcher.register_handler("set_location", handle_set_location)
    dispatcher.register_handler("set_rotation", handle_set_rotation)
    dispatcher.register_handler("set_scale", handle_set_scale)
    dispatcher.register_handler("apply_transforms", handle_apply_transforms)
    dispatcher.register_handler("set_origin", handle_set_origin)
    dispatcher.register_handler("snap_to_grid", handle_snap_to_grid)
    dispatcher.register_handler("set_location_relative", handle_set_location_relative)
    dispatcher.register_handler("set_scale_origin", handle_set_scale_origin)
