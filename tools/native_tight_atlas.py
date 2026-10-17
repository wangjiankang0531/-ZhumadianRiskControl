"""Crop unused atlas canvas; source placement, original pixels and gutters stay unchanged."""
POLICY = 'tight_square_gutter4_v1'
MIN_SIDE = 16
MAX_SIDE = 2048
ALIGNMENT = 8
GUTTER = 4


def tight_layouts(layouts):
    result = []
    for mapping, previous_side in layouts:
        if previous_side not in (1024, 2048) or not mapping:
            raise ValueError('Unexpected legacy atlas layout')
        extent = 0
        for x, y, width, height in mapping.values():
            if any(type(n) is not int for n in (x, y, width, height)) or min(width, height) <= 0 or min(x, y) < GUTTER:
                raise ValueError('Invalid original atlas rectangle')
            extent = max(extent, x + width + GUTTER, y + height + GUTTER)
        side = max(MIN_SIDE, (extent + ALIGNMENT - 1) // ALIGNMENT * ALIGNMENT)
        if side > previous_side or side > MAX_SIDE:
            raise ValueError('Tight atlas would crop source pixels or gutters')
        result.append((mapping, side))
    return result
