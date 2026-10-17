"""Dedicated edge-clamped pages keep a 2048-wide source at its original resolution."""
from pathlib import Path
if __package__:
    from . import native_texture_parts as textures, native_tight_atlas as tight
else:
    import native_texture_parts as textures
    import native_tight_atlas as tight

POLICY = 'edge_clamped_square_v1'
SAMPLER = {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071}


def layouts(sizes):
    regular, dedicated = {}, []
    for name, (width, height) in sorted(sizes.items(), key=lambda row: str(row[0])):
        if any(type(n) is not int or n <= 0 or n > 2048 for n in (width, height)):
            raise ValueError('Source texture exceeds dedicated edge-clamped page')
        if max(width, height) + 2 * textures.GUTTER <= 2048:
            regular[name] = (width, height)
        else:
            x = textures.GUTTER if width + 2 * textures.GUTTER <= 2048 else 0
            y = textures.GUTTER if height + 2 * textures.GUTTER <= 2048 else 0
            dedicated.append(({name: (x, y, width, height)}, 2048))
    return tight.tight_layouts(textures.atlas_layouts(regular)) + dedicated


def image(mapping, size):
    from PIL import Image
    if len(mapping) != 1 or size != 2048:
        raise ValueError('An edge-touching page must contain one source only')
    path, (x, y, width, height) = next(iter(mapping.items()))
    if min(x, y) < 0 or x + width > size or y + height > size:
        raise ValueError('Source rectangle escapes dedicated page')
    with Image.open(path) as source:
        if source.size != (width, height):
            raise ValueError('Source texture changed')
        tile = source.convert('RGB')
    result = Image.new('RGB', (size, size))
    result.paste(tile, (x, y))
    # Extend only border pixels; the source rectangle is copied byte for byte.
    if x:
        result.paste(tile.crop((0, 0, 1, height)).resize((x, height), Image.Resampling.NEAREST), (0, y))
    if x + width < size:
        result.paste(tile.crop((width - 1, 0, width, height)).resize((size - x - width, height), Image.Resampling.NEAREST), (x + width, y))
    if y:
        result.paste(result.crop((0, y, size, y + 1)).resize((size, y), Image.Resampling.NEAREST), (0, 0))
    if y + height < size:
        result.paste(result.crop((0, y + height - 1, size, y + height)).resize((size, size - y - height), Image.Resampling.NEAREST), (0, y + height))
    return result


def save(mapping, output, size):
    if all(min(x, y) >= textures.GUTTER and max(x + w, y + h) + textures.GUTTER <= size for x, y, w, h in mapping.values()):
        return textures.save_atlas(mapping, output, size)
    image(mapping, size).save(output, quality=98, subsampling=0)
