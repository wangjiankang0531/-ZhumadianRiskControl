"""Crop unused page canvas on each axis without cropping source pixels or gutters."""
if __package__:
    from . import native_edge_clamp_atlas as edge, native_texture_parts as textures
else:
    import native_edge_clamp_atlas as edge
    import native_texture_parts as textures

POLICY = 'edge_clamped_rect_v1'


def layouts(sizes):
    result = []
    for mapping, side in edge.layouts(sizes):
        width = max(x + w + 4 for x, y, w, h in mapping.values())
        height = max(y + h + 4 for x, y, w, h in mapping.values())
        extent = tuple(min(side, max(16, (n + 7) // 8 * 8)) for n in (width, height))
        if any(x + w > extent[0] or y + h > extent[1] for x, y, w, h in mapping.values()):
            raise ValueError('Rectangular atlas crops original pixels')
        result.append((mapping, extent))
    return result


def image(mapping, extent):
    # Keep the source RGB canvas in memory and encode the final JPEG only once.
    side = max(extent)
    interior = all(min(x, y) >= 4 and max(x + w, y + h) + 4 <= side for x, y, w, h in mapping.values())
    canvas = textures.atlas_image(mapping, side) if interior else edge.image(mapping, side)
    return canvas.crop((0, 0, *extent))


def save(mapping, output, extent):
    image(mapping, extent).save(output, quality=98, subsampling=0)
