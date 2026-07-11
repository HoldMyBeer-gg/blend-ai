# blend-ai Texture Pipeline Extension

> **Author:** Ignacio Badenes (@ignisky)  
> **Project:** Celestial Chaos (Last Chaos Remaster)  
> **Based on:** blend-ai v1.2.1 — The most intuitive MCP Server for Blender

## Overview

This extension adds procedural texture generation and materialization to blend-ai, 
enabling AI-driven texturing of entire game asset pipelines directly from the MCP agent.

## Architecture

```
User Prompt → Hermes Agent → MCP Tools → blend-ai → Blender 5.1 Headless
                                           ↓
                                    forge_core.py (14 patterns)
                                           ↓
                                    PNG Textures (64×64 / 128×128)
                                           ↓
                                    Materializer (auto-maps by object/species name)
                                           ↓
                                    Textured .blend files (in-place)
```

## Key Principles

1. **Pixel Art First:** `interpolation = 'Closest'` for crisp pixel art
2. **Specular IOR = 0:** Never reflective — keeps the hand-crafted look
3. **Dual Pipeline:** Color (RGB) + Roughness (greyscale) maps
4. **Color Variants:** `Fire_Red_Dragon` gets red scales, not green
5. **Non-Destructive:** Only textures cloth objects, preserves skin/metal/hair

## Material Properties — Critical Axes

| Property  | Axis   | Range | Behavior |
|-----------|--------|-------|----------|
| Metallic  | Ascending  | 0→1   | Increase for metal |
| Roughness | Ascending  | 0→1   | 0=smooth, 1=rough |
| Alpha     | Descending | 1→0   | Base=opaque, decrease for transparency |
| Specular  | Ascending  | 0→1   | Always 0 in this pipeline |

## Pipeline Stats

- **303 blends** textured (164 scenes + 139 mobs)
- **422+ PNGs** generated (284 color + 39 roughness + 23 player cloth + variants)
- **14 procedural patterns** (noise, marble, wood, voronoi, gradient, plasma, 
   weave, runes, veins, stripes, cloud, sparks, fire, scales)
- **105+ keywords** auto-mapping by object name
- **42 species + 9 player classes** mapped
- **0 critical errors** across the entire pipeline

## Naming Convention

- `<texture>.png` = Color (RGB/RGBA). Name indicates chromatic content.
- `<texture>_rough.png` = **Always greyscale.** The `_rough` suffix means 
  "roughness map type", NOT chromatic content.
- Always clean up `_old` backup files after replacing textures.
