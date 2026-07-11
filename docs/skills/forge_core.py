#!/usr/bin/env python3
"""Texture PNG Forge Core — 14 patrones procedurales con numpy + Pillow."""
import numpy as np
from PIL import Image, ImageFilter
import math, random, os, sys

def _rng(seed):
    return np.random.RandomState(seed)

def _normalize(a):
    lo, hi = a.min(), a.max()
    if hi <= lo: return np.zeros_like(a)
    return (a - lo) / (hi - lo)

def pattern_gradient(size=512, channels=4, seed=42, style='diagonal', colors=None, cycles=2.0):
    if colors is None:
        colors = [(0.0, (255,0,0)), (0.25, (20,5,5)), (0.5, (255,220,0)), (0.75, (15,5,10)), (1.0, (255,0,0))]
    y, x = np.mgrid[0:size, 0:size]
    if style == 'diagonal': t = (x + y) / (size * 2) * cycles
    elif style == 'horizontal': t = x / size * cycles
    elif style == 'vertical': t = y / size * cycles
    elif style == 'radial': t = np.sqrt((x-size/2)**2 + (y-size/2)**2) / (size * 0.5) * cycles
    else: t = (x + y) / (size * 2) * cycles
    t = t % 1.0
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for i in range(len(colors)-1):
        p1, c1 = colors[i]; p2, c2 = colors[i+1]
        mask = (t >= p1) & (t <= p2)
        if not np.any(mask): continue
        local = np.clip((t[mask] - p1) / (p2 - p1), 0, 1)
        for ch in range(3):
            result[mask, ch] = (c1[ch] + (c2[ch] - c1[ch]) * local).astype(np.uint8)
    if channels == 4:
        alpha = np.full((size, size, 1), 255, dtype=np.uint8)
        return np.concatenate([result, alpha], axis=2)
    return result

def pattern_noise(size=512, channels=4, seed=42, scale=4.0, octaves=6, noise_type='fbm',
                  color_dark=(15,10,8), color_light=(60,45,35)):
    rng = _rng(seed)
    base = np.zeros((size, size))
    for o in range(octaves):
        freq = scale * (2 ** o)
        amp = 0.5 ** o
        noise = rng.rand(int(np.ceil(size * freq / scale) + 2), int(np.ceil(size * freq / scale) + 2))
        h, w = noise.shape
        yi = np.clip((np.arange(size) * freq / scale).astype(int), 0, h-1)
        xi = np.clip((np.arange(size) * freq / scale).astype(int), 0, w-1)
        base += amp * noise[np.ix_(yi, xi)]
    base = _normalize(base)
    if noise_type == 'ridged': base = _normalize(1.0 - np.abs(base * 2 - 1.0))
    elif noise_type == 'billow': base = _normalize(np.abs(base * 2 - 1.0))
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        result[:,:,ch] = (color_dark[ch] + (color_light[ch] - color_dark[ch]) * base).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

def pattern_voronoi(size=512, channels=4, seed=42, cells=30, edge_width=0.15,
                    edge_color=(255,180,50), fill_color=(10,8,6)):
    rng = _rng(seed)
    points = rng.rand(cells, 2) * size
    y, x = np.mgrid[0:size, 0:size]
    coords = np.stack([x.ravel(), y.ravel()], axis=1)
    dists = np.zeros((len(coords), 2))
    for k in range(2):
        d = np.sum((coords[:, np.newaxis, :] - points[np.newaxis, :, :])**2, axis=2)
        idx = np.argpartition(d, k, axis=1)[:, k]
        dists[:, k] = d[np.arange(len(d)), idx]
    edge = np.sqrt(dists[:, 0]) / (np.sqrt(dists[:, 0]) + np.sqrt(dists[:, 1]))
    edge = edge.reshape(size, size)
    mask = _normalize(edge)
    mask = ((mask > 0.3) & (mask < 0.7)).astype(float)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=1.0))
    mask = np.array(mask_img).astype(float) / 255.0
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        base = fill_color[ch] * np.ones((size, size), dtype=np.float32)
        result[:,:,ch] = (base + edge_color[ch] * mask).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

def pattern_plasma(size=512, channels=4, seed=42, complexity=4.0, colors=None):
    if colors is None:
        colors = [(0.0, (255,0,0)), (0.33, (80,5,0)), (0.66, (255,200,0)), (1.0, (120,0,0))]
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    v = np.zeros((size, size))
    for i in range(5):
        freq = complexity * (0.5 ** i)
        d = np.sqrt((x - rng.rand()*size)**2 + (y - rng.rand()*size)**2) * freq / size
        v += np.sin(d * 10 + i) * (0.5 ** i)
    v2 = np.sin(x * complexity / size * 8 + np.sin(y * complexity / size * 6))
    v = _normalize(v * 0.7 + v2 * 0.3)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for i in range(len(colors)-1):
        p1, c1 = colors[i]; p2, c2 = colors[i+1]
        mask = (v >= p1) & (v <= p2)
        if not np.any(mask): continue
        local = np.clip((v[mask] - p1) / (p2 - p1), 0, 1)
        for ch in range(3):
            result[mask, ch] = (c1[ch] + (c2[ch] - c1[ch]) * local).astype(np.uint8)
    if channels == 4:
        alpha = np.clip((v * 0.5 + 0.3) * 255, 0, 255).astype(np.uint8)[..., np.newaxis]
        return np.concatenate([result, alpha], axis=2)
    return result

def pattern_fire(size=512, channels=4, seed=42, scale=3.0, vertical_bias=0.3,
                 color_bottom=(255,60,0), color_top=(255,200,50)):
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    v = np.zeros((size, size))
    for o in range(4):
        freq = scale * (2 ** o); amp = 0.5 ** o
        n = rng.rand(int(size*freq/scale+5), int(size*freq/scale+5))
        h, w = n.shape
        yi = np.clip((y*freq/scale).astype(int), 0, h-1)
        xi = np.clip((x*freq/scale).astype(int), 0, w-1)
        v += amp * n[yi, xi]
    v = _normalize(v) + (1.0 - y/size) * vertical_bias
    v = _normalize(v)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        result[:,:,ch] = (color_bottom[ch] + (color_top[ch]-color_bottom[ch])*v).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.clip(v*255,0,255).astype(np.uint8)[...,np.newaxis]], axis=2)
    return result

def pattern_wood(size=512, channels=4, seed=42, rings=12, grain=0.3,
                 color_dark=(60,35,20), color_light=(140,90,50)):
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    cx, cy = size/2 + rng.randn()*20, size/2 + rng.randn()*20
    d = np.sqrt((x-cx)**2 + (y-cy)**2) / (size/2) * rings * np.pi
    v = _normalize(np.sin(d + np.sin(d * 0.5 + grain)) + 1)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        result[:,:,ch] = (color_dark[ch] + (color_light[ch]-color_dark[ch])*v).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

def pattern_weave(size=512, channels=4, seed=42, thread_width=8, gap=4,
                  color1=(120,60,30), color2=(80,40,20)):
    rng = _rng(seed)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    period = thread_width * 2 + gap * 2
    for y in range(size):
        for x in range(size):
            wx, wy = (x % period) < thread_width, (y % period) < thread_width
            c = color1 if (wx or wy) else color2
            if wx and wy: c = tuple(v//2 for v in color1)
            result[y, x] = c
    noise = rng.rand(size, size, 3).astype(np.float32) * 10
    result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

def pattern_runes(size=512, channels=4, seed=42, count=12, rune_color=(100,200,255), glow_color=(200,230,255)):
    rng = _rng(seed)
    result = np.zeros((size, size, 4), dtype=np.uint8)
    result[:,:,:3] = (5, 2, 15)
    for _ in range(count):
        cx, cy = rng.randint(20, size-20, 2)
        scale = rng.randint(8, 20)
        rotation = rng.uniform(0, 2*np.pi)
        for _ in range(rng.randint(3, 6)):
            x1 = int(cx + math.cos(rotation+rng.uniform(-0.5,0.5))*scale)
            y1 = int(cy + math.sin(rotation+rng.uniform(-0.5,0.5))*scale)
            x2 = int(cx + math.cos(rotation+rng.uniform(-0.5,0.5))*scale*rng.uniform(0.5,1.5))
            y2 = int(cy + math.sin(rotation+rng.uniform(-0.5,0.5))*scale*rng.uniform(0.5,1.5))
            steps = max(abs(x2-x1), abs(y2-y1))
            if steps == 0: continue
            for s in range(steps + 1):
                t = s / steps
                px = int(x1 + (x2-x1)*t + rng.randint(-1,1))
                py = int(y1 + (y2-y1)*t + rng.randint(-1,1))
                if 0 <= px < size and 0 <= py < size:
                    result[py,px,:3] = rune_color; result[py,px,3] = 220
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        gx,gy = px+dx, py+dy
                        if 0 <= gx < size and 0 <= gy < size:
                            result[gy,gx,:3] = np.maximum(result[gy,gx,:3], np.array(glow_color)//2)
                            result[gy,gx,3] = max(result[gy,gx,3], 100)
    return result

def pattern_marble(size=512, channels=4, seed=42, scale=4.0, veining=3.0, colors=None):
    if colors is None:
        colors = [(0.0, (200,195,185)), (0.2, (180,175,165)), (0.5, (150,145,140)), (0.7, (100,95,90)), (1.0, (60,55,50))]
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    v = np.zeros((size, size))
    for o in range(5):
        freq = scale * (2**o); amp = 0.5**o
        n = rng.rand(int(size*freq/scale+5), int(size*freq/scale+5))
        h, w = n.shape
        yi = np.clip((y*freq/scale).astype(int), 0, h-1)
        xi = np.clip((x*freq/scale).astype(int), 0, w-1)
        v += amp * n[yi, xi]
    v = _normalize(np.sin(v * veining * np.pi * 4 + np.sin(x/size*3 + y/size*2)))
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for i in range(len(colors)-1):
        p1, c1 = colors[i]; p2, c2 = colors[i+1]
        mask = (v >= p1) & (v <= p2)
        if not np.any(mask): continue
        local = np.clip((v[mask] - p1) / (p2 - p1), 0, 1)
        for ch in range(3):
            result[mask, ch] = (c1[ch] + (c2[ch]-c1[ch])*local).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

def pattern_veins(size=512, channels=4, seed=42,
                  density=8.0, branching=3,
                  vein_color=(255,200,100), bg_color=(10,5,5)):
    rng = _rng(seed)
    result = np.full((size, size, 3), bg_color, dtype=np.uint8)
    for _ in range(int(density)):
        x, y = rng.randint(0, size, 2)
        length = rng.randint(15, 45)
        angle = rng.uniform(0, 2*np.pi)
        for b in range(int(branching)):
            a = angle + rng.uniform(-1.2, 1.2)
            for step in range(length):
                px = int(x + math.cos(a)*step + rng.randint(-2, 2))
                py = int(y + math.sin(a)*step + rng.randint(-2, 2))
                if 0 <= px < size and 0 <= py < size:
                    intensity = 1.0 - step/length
                    for ch in range(3):
                        result[py,px,ch] = min(255, int(vein_color[ch]*intensity*0.7 + result[py,px,ch]*0.3))
    if channels == 4:
        bright = np.mean(result.astype(float), axis=2)
        alpha = np.clip(bright*0.8, 0, 255).astype(np.uint8)[..., np.newaxis]
        return np.concatenate([result, alpha], axis=2)
    return result

def pattern_stripes(size=512, channels=4, seed=42, count=8, style='wave',
                    color1=(255,80,0), color2=(5,5,10)):
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    if style == 'wave': v = np.sin((y/size)*count*np.pi*2 + np.sin(x/size*8+rng.rand()*2)*2)
    else: v = np.sin((y/size)*count*np.pi*2)
    v = _normalize(v)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        result[:,:,ch] = (color1[ch] + (color2[ch]-color1[ch])*v).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

def pattern_cloud(size=512, channels=4, seed=42, scale=3.0,
                  color=(200,180,160), bg_color=(5,5,10)):
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    v = np.zeros((size, size))
    for o in range(5):
        freq = scale*(2**o); amp = 0.5**o
        n = rng.rand(int(size*freq/scale+5), int(size*freq/scale+5))
        h,w = n.shape
        yi = np.clip((y*freq/scale).astype(int), 0, h-1)
        xi = np.clip((x*freq/scale).astype(int), 0, w-1)
        v += amp * n[yi, xi]
    v = _normalize(v)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        result[:,:,ch] = (bg_color[ch] + (color[ch]-bg_color[ch])*v).astype(np.uint8)
    if channels == 4:
        alpha = np.clip((v-0.3)*3.0*255, 0, 255).astype(np.uint8)[..., np.newaxis]
        return np.concatenate([result, alpha], axis=2)
    return result

def pattern_sparks(size=512, channels=4, seed=42, count=80,
                   spark_color=(255,220,100), glow_color=(255,100,20), radius=2.0):
    rng = _rng(seed)
    result = np.zeros((size, size, 4), dtype=np.uint8)
    for _ in range(count):
        x, y = rng.randint(0, size, 2)
        intensity = rng.uniform(0.5, 1.0)
        r = int(radius * rng.uniform(0.5, 1.5))
        for dy in range(-r*2, r*2+1):
            for dx in range(-r*2, r*2+1):
                d = math.sqrt(dx*dx + dy*dy)
                if d <= r * 2:
                    px, py = x+dx, y+dy
                    if 0 <= px < size and 0 <= py < size:
                        fade = max(0, 1.0 - d/(r*2))
                        for ch in range(3):
                            result[py,px,ch] = min(255, int((spark_color[ch]*(1-fade)+glow_color[ch]*fade)*intensity))
                        result[py,px,3] = min(255, int(255*fade))
    return result

def pattern_scales(size=256, channels=4, seed=42,
                   cell_size=16,
                   color_dark=(30,80,30), color_light=(60,150,60)):
    rng = _rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    cols = size // cell_size + 2
    rows = size // cell_size + 2
    centers = np.zeros((rows, cols, 2))
    for r in range(rows):
        for c in range(cols):
            ox = (c + 0.5) * cell_size + rng.randint(-3, 4)
            oy = (r + 0.5) * cell_size + (c % 2) * cell_size * 0.5 + rng.randint(-3, 4)
            centers[r, c] = [ox, oy]
    d = np.full((size, size), np.inf)
    for r in range(rows):
        for c in range(cols):
            cx, cy = centers[r, c]
            dd = np.sqrt((x - cx)**2 + (y - cy)**2)
            d = np.minimum(d, dd)
    value = np.clip(1.0 - d / (cell_size * 0.5), 0, 1)
    result = np.zeros((size, size, 3), dtype=np.uint8)
    for ch in range(3):
        result[:,:,ch] = np.clip(color_dark[ch] + (color_light[ch]-color_dark[ch])*value, 0, 255).astype(np.uint8)
    if channels == 4:
        return np.concatenate([result, np.full((size,size,1),255,np.uint8)], axis=2)
    return result

PATTERNS = {
    'gradient': pattern_gradient, 'noise': pattern_noise, 'voronoi': pattern_voronoi,
    'plasma': pattern_plasma, 'fire': pattern_fire, 'wood': pattern_wood,
    'weave': pattern_weave, 'runes': pattern_runes, 'marble': pattern_marble,
    'veins': pattern_veins, 'stripes': pattern_stripes,
    'cloud': pattern_cloud, 'sparks': pattern_sparks, 'scales': pattern_scales,
}

def forge(pattern_type, size=256, channels=4, seed=42, **kwargs):
    fn = PATTERNS.get(pattern_type)
    if fn is None: raise ValueError(f"Unknown pattern: {pattern_type}")
    return fn(size=size, channels=channels, seed=seed, **kwargs)

def to_image(arr):
    mode = 'RGBA' if arr.shape[2] == 4 else 'RGB'
    return Image.fromarray(arr, mode=mode)

def save_texture(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = to_image(arr)
    img.save(path)
    return img

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in PATTERNS.items():
        try:
            arr = fn(size=128, channels=4, seed=42)
            save_texture(arr, os.path.join(out_dir, f"test_{name}.png"))
            print(f"  ✅ test_{name}.png")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
