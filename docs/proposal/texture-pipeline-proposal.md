# 🔧 Blend-AI MCP Extension Proposal — Texture Pipeline Tools

> **Propuesta:** Extender blend-ai MCP con tools custom para pipeline de texturizado procedural  
> **Contexto:** 30 scripts, ~3.800 líneas de Python, pipeline validado en 303 blends  
> **Autor:** Ignacio Badenes (Ignición) — Celestial Chaos MMORPG  
> **Repositorio base:** [blend-ai](https://github.com/your-org/blend-ai) (MCP server for Blender)

---

## 📋 Resumen del Pipeline

En 4 días de desarrollo iterativo construimos un pipeline completo para texturizar assets de un MMORPG (Last Chaos → Celestial Chaos) usando Blender 5.1 headless + Python + Pillow + numpy.

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│  Blender    │    │  Forge       │    │  Materializer  │    │  Batch       │
│  Scanner    │───→│  (PNG gen)   │───→│  (apply tex)   │───→│  Processor   │
│  .blend→JSON│    │  14 patterns │    │  105+ keywords │    │  3 paralelo  │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘
```

---

## 🛠️ Tools Propuestas para blend-ai MCP

### Tool 1: `forge_generate_texture`
**Función:** Genera una textura PNG procedural desde 14 patrones  
**Input:**
```json
{
  "pattern": "noise|marble|wood|voronoi|gradient|plasma|weave|runes|veins|stripe|cloud|sparks|fire|scales",
  "size": 128,
  "color_dark": [30, 30, 40],
  "color_light": [120, 120, 160],
  "seed": 42,
  "output_path": "/path/to/texture.png"
}
```
**Output:** PNG file + metadata (size, pattern, colors)  
**Uso en Blender:** `bpy.data.images.load(output_path)` → conecta a Principled BSDF

### Tool 2: `forge_batch_generate`
**Función:** Genera un lote de texturas desde una receta YAML/JSON  
**Input:** Array de definiciones de textura (pattern + colores + seed)  
**Output:** Múltiples PNGs

### Tool 3: `scan_blend_objects`
**Función:** Escanea un .blend y devuelve objetos, polígonos, materiales, UVs  
**Input:** Ruta al .blend  
**Output:** JSON estructurado con todos los objetos y sus propiedades

### Tool 4: `materialize_from_keywords`
**Función:** Aplica texturas a un .blend usando mapeo por nombre de objeto  
**Input:** 
```json
{
  "blend_path": "/path/to/model.blend",
  "texture_dir": "/path/to/textures/",
  "mode": "scena|mob|player",
  "roughness": true
}
```
**Output:** .blend modificado con texturas aplicadas in-place

### Tool 5: `materialize_mob_variant`
**Función:** Aplica textura considerando variante de color en el filename  
**Input:**
```json
{
  "blend_path": "/path/to/Fire_Red_Dragon.blend",
  "texture_dir": "/path/to/textures/"
}
```
**Output:** .blend con `dragon_scale_red.png` aplicada en lugar de `dragon_scale.png`

### Tool 6: `generate_roughness_map`
**Función:** Genera mapa de rugosidad en grises a partir de un patrón  
**Input:** Mismo que forge_generate_texture + `roughness_range: [30, 200]`  
**Output:** PNG en escala de grises + conectado a Roughness del BSDF

### Tool 7: `verify_textures`
**Función:** Verifica qué objetos de un .blend tienen texturas aplicadas  
**Input:** Ruta al .blend  
**Output:** Listado de objetos con estado (texturizados vs originales)

---

## 🔬 Pipeline de Referencia (Implementación Actual)

### 1. Core: forge_core.py (354 líneas)
14 patrones procedurales con numpy+PIL, exportables a PNG RGBA.

| Patrón | Parámetros clave | Uso |
|--------|-----------------|-----|
| `noise` | octaves, scale, color_dark/light | Piel, roca, metal |
| `marble` | veining, scale, colors | Mármol, hueso, hielo |
| `wood` | rings, grain | Madera, cuerno |
| `voronoi` | cells, edge_width | Losas, quitino, escamas |
| `weave` | thread_width, gap | Tela, vendas |
| `plasma` | complexity | Fuego, energía, magma |
| `scales` | cell_size | Dragón, reptil, serpiente |
| `runes` | count, glow | Magia, glifos |
| `gradient` | style, cycles | Tejados, cielo, energía |
| `veins` | density, branching | Sangre, venas, raíces |
| `cloud` | scale | Humo, espectros |
| `sparks` | count | Estrellas, gemas |
| `stripes` | count | Pelaje rayado |
| `fire` | vertical_bias | Llamas con alpha |

### 2. Materializer Dual (Color + Roughness)
```
Color Texture (RGB)    → Image Texture → Base Color
Roughness Map (Greyscale) → Image Texture → Roughness
Specular IOR           → 0.0 (siempre)
Interpolation          → 'Closest' (pixel art)
```

### 3. Convenciones Críticas
- `<textura>.png` = Color (RGB/RGBA). El nombre indica su contenido cromático.
- `<textura>_rough.png` = **Siempre escala de grises**. El sufijo `_rough` = tipo de mapa, no contenido. Aunque `<textura>` se llame `rainbow`, el `_rough` es gris.
- `Specular IOR = 0.0` en Blender 5.x reemplazó `Specular = 0.0`
- `interpolation = 'Closest'` para pixel art nítido
- Materiales compartidos: si dos objetos usan el mismo material data block, texturizar uno afecta al otro

### 4. Ejes de Propiedades del Material
| Propiedad | Eje | Rango | Comportamiento |
|-----------|-----|-------|----------------|
| Metallic | ⬆️ Ascendente | 0→1 | Subes para hacerlo metal |
| Roughness | ⬆️ Ascendente | 0→1 | Negro=liso, Blanco=rugoso |
| Alpha | ⬇️ Descendente | 1→0 | Base=opaco, bajas para transparencia |
| Specular IOR | ⬆️ Ascendente | 0→1 | Se deja a 0 siempre |

---

## 📊 Resultados del Pipeline (Producción)

| Métrica | Valor |
|---------|-------|
| Blends procesados | 303 |
| Texturas generadas | 422 PNGs (284 color + 39 roughness + 23 player + extras) |
| Patrones de textura | 14 |
| Keywords de mapeo | 105 (scena) + 42 species (mobs) + 9 classes (players) |
| Blender version | 5.1.2 (flatpak) |
| Tiempo de procesamiento | ~10 min para 139 blends (grupos de 3) |

---

## 🚀 Cómo Contribuir

1. **Fork** del repositorio [blend-ai](https://github.com/nousresearch/blend-ai)
2. Crear rama `feat/texture-pipeline-tools`
3. Añadir tools al servidor MCP usando patrón FastMCP:
```python
from fastmcp import FastMCP
mcp = FastMCP("blend-ai-texture")

@mcp.tool()
def forge_texture(pattern: str, colors: list, size: int = 128) -> str:
    """Generate procedural texture PNG"""
    ...
```
4. Cada tool sigue el principio: **input JSON → operación Blender → output JSON/PNG**
5. PR con descripción del pipeline y ejemplos de uso

---

## 📁 Archivos de Referencia

Todos los scripts están en el directorio `scena/textures/` del proyecto Celestial Chaos:
```
scena/textures/
├── forge_core.py              # 14 patrones procedurales (354 líneas)
├── blender_scanner.py         # Escáner de blends (71 líneas)
├── blender_materializer.py    # 105 keywords (290 líneas)
├── mob_materializer.py        # 42 species + roughness (337 líneas)
├── player_hard_reset.py       # Player cloth applier (111 líneas)
├── batch_*.py                 # 12 batches de generación
├── batch_*materializer.sh     # Procesadores batch
├── details.md                 # Documentación completa
└── details_complete.md        # Informe técnico
```

---

> **Contacto:** Ignacio Badenes — ignisky  
> **Proyecto:** Celestial Chaos (Last Chaos Remaster)  
> **Pipeline validado:** Julio 2026
