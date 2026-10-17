"""Pack source-sized texture rectangles and partition OBJ faces without losing siblings."""

import math
from pathlib import Path

ATLAS_SIZE = 2048
GUTTER = 4


def texture_bins(sizes, size=ATLAS_SIZE):
    # Deterministic free-rectangle packing. Each source keeps its original pixels.
    bins = []
    for name, (width, height) in sorted(
        sizes.items(),
        key=lambda row: (-max(row[1]), -row[1][0] * row[1][1], str(row[0])),
    ):
        w, h = width + 2 * GUTTER, height + 2 * GUTTER
        if width <= 0 or height <= 0 or w > size or h > size:
            raise ValueError("source texture exceeds bounded native atlas")
        chosen = None
        for index, bucket in enumerate(bins):
            for rectangle in bucket["free"]:
                x, y, rw, rh = rectangle
                if w <= rw and h <= rh:
                    score = (min(rw - w, rh - h), rw * rh - w * h, index, y, x)
                    if chosen is None or score < chosen[0]:
                        chosen = (score, index, rectangle)
        if chosen is None:
            bins.append({"free": [(0, 0, size, size)], "mapping": {}})
            chosen = (None, len(bins) - 1, (0, 0, size, size))
        _, index, (x, y, rw, rh) = chosen
        bucket = bins[index]
        remaining = []
        for fx, fy, fw, fh in bucket["free"]:
            if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                remaining.append((fx, fy, fw, fh))
                continue
            if x > fx:
                remaining.append((fx, fy, x - fx, fh))
            if x + w < fx + fw:
                remaining.append((x + w, fy, fx + fw - x - w, fh))
            if y > fy:
                remaining.append((fx, fy, fw, y - fy))
            if y + h < fy + fh:
                remaining.append((fx, y + h, fw, fy + fh - y - h))
        bucket["free"] = [
            a
            for i, a in enumerate(remaining)
            if not any(
                i != j
                and a[0] >= b[0]
                and a[1] >= b[1]
                and a[0] + a[2] <= b[0] + b[2]
                and a[1] + a[3] <= b[1] + b[3]
                and (a != b or i > j)
                for j, b in enumerate(remaining)
            )
        ]
        bucket["mapping"][name] = (x + GUTTER, y + GUTTER, width, height)
    return [bucket["mapping"] for bucket in bins]


def atlas_side(mapping):
    extent = max(max(x + w + GUTTER, y + h + GUTTER) for x, y, w, h in mapping.values())
    return 1024 if extent <= 1024 else 2048


def atlas_layouts(sizes):
    """Keep source pixels; use fewer physical texels when small tail pages permit."""
    layouts = []
    for mapping in texture_bins(sizes):
        side = atlas_side(mapping)
        chosen = [(mapping, side)]
        if side == 2048 and all(
            max(w, h) + 2 * GUTTER <= 1024 for _, _, w, h in mapping.values()
        ):
            alternatives = [
                (m, 1024)
                for m in texture_bins(
                    {name: (w, h) for name, (_, _, w, h) in mapping.items()}, 1024
                )
            ]
            if sum(n * n for _, n in alternatives) < side * side:
                chosen = alternatives
        layouts.extend(chosen)
    return layouts


def save_atlas(mapping, output, size=ATLAS_SIZE):
    from PIL import Image

    atlas = Image.new("RGB", (size, size))
    for path, (x, y, w, h) in mapping.items():
        with Image.open(path) as source:
            if source.size != (w, h):
                raise ValueError("source texture changed")
            tile = source.convert("RGB")
        atlas.paste(tile, (x, y))
        for offset in range(1, GUTTER + 1):
            atlas.paste(tile.crop((0, 0, 1, h)), (x - offset, y))
            atlas.paste(tile.crop((w - 1, 0, w, h)), (x + w - 1 + offset, y))
            atlas.paste(tile.crop((0, 0, w, 1)), (x, y - offset))
            atlas.paste(tile.crop((0, h - 1, w, h)), (x, y + h - 1 + offset))
        for dx in range(1, GUTTER + 1):
            for dy in range(1, GUTTER + 1):
                for px, py, cx, cy in [
                    (x - dx, y - dy, 0, 0),
                    (x + w - 1 + dx, y - dy, w - 1, 0),
                    (x - dx, y + h - 1 + dy, 0, h - 1),
                    (x + w - 1 + dx, y + h - 1 + dy, w - 1, h - 1),
                ]:
                    atlas.putpixel((px, py), tile.getpixel((cx, cy)))
    atlas.save(output, quality=98, subsampling=0)


def face_count(obj, materials, selected):
    current = None
    count = 0
    with obj.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("usemtl "):
                current = materials[line.split()[1]]
            elif line.startswith("f ") and current in selected:
                count += 1
    return count


def slice_obj(obj, output, materials, selected, first, count):
    # Preserve original vertex references; write_geometry compacts only used vertices.
    ordinal = 0
    written = 0
    with obj.open(encoding="utf-8") as source, output.open(
        "w", encoding="utf-8", newline="\n"
    ) as target:
        current = None
        for line in source:
            if line.startswith("usemtl "):
                current = materials[line.split()[1]]
            if line.startswith("f "):
                if current not in selected:
                    continue
                if first <= ordinal < first + count:
                    target.write(line)
                    written += 1
                ordinal += 1
            else:
                target.write(line)
    material_text = obj.with_suffix(".mtl").read_text(encoding="utf-8")
    output.with_suffix(".mtl").write_text(
        "\n".join(
            (
                "map_Kd " + str((obj.parent / line.split(maxsplit=1)[1]))
                if line.strip().startswith("map_Kd ")
                else line
            )
            for line in material_text.splitlines()
        )
        + "\n",
        encoding="utf-8",
    )
    if written != count:
        raise ValueError("texture part face partition incomplete")


def face_counts(obj):
    import re

    result = {}
    current = None
    with obj.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith(("o ", "g ")):
                match = re.search(r"Tile_[+-]\d+_[+-]\d+_L\d+_0[0-9u]+", line)
                current = match.group() if match else None
            elif line.startswith("f "):
                if current is None:
                    raise ValueError("unattributed texture part face")
                result[current] = result.get(current, 0) + 1
    return result
