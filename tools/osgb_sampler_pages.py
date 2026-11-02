"""Full original images with exactly the source sampler's mip allocation.

Reuse the existing v2 full-rectangle contract. No image crop, resample,
triangle compaction, UV rewrite, sampler substitution, or asset writes.
"""
from pathlib import Path
from osgb_memory_pages import build_bundle as original_bundle, canonical, sha
from osgb_cropped_pages import page as sampler_page, FORMAT


def page(descriptor,payload,mesh,directory,source_name):
    if descriptor.get('schema')!='zhumadian.osgb.memory.v1':
        raise ValueError('A complete original memory frame is required')
    images=[]
    for image in descriptor['images']:
        if any(key in image for key in ('originalWidth','originalHeight','sourceRect','pixelsOmitted')):
            raise ValueError('Original sampler pages cannot reinterpret cropped or omitted pixels')
        width,height=image['width'],image['height']
        images.append({**image,'originalWidth':width,'originalHeight':height,'sourceRect':[0,0,width,height]})
    # v2 explicitly declares mip_levels and identity UV transform, including
    # for a full rectangle. Its existing WEB loader allocates the same levels.
    return sampler_page({**descriptor,'images':images},payload,mesh,directory,source_name)


def build_bundle(tile,catalog,reader,*,depth=None,parent=None,recipe_identity,selection=None):
    return original_bundle(tile,catalog,reader,depth=depth,parent=parent,
        recipe_identity=recipe_identity,selection=selection,page_builder=page,source_format=FORMAT)


def builder_identity():
    return sha(canonical({name:sha(Path(__file__).with_name(name).read_bytes())
        for name in ('osgb_sampler_pages.py','osgb_cropped_pages.py')}))
