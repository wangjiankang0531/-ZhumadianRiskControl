"""Read SHA-pinned PNGs from an owned local QA runtime; emit Pillow RGBA digests."""
import argparse
import hashlib
import io
import json
import re
import time
import urllib.request
from urllib.parse import urlparse
from PIL import Image


def prepare(base, identity):
    parsed = urlparse(base)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('An explicit loopback runtime is required')
    base = base.rstrip('/')

    def request(path, method='GET'):
        req = urllib.request.Request(base + '/' + path, method=method)
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read()

    _, raw = request('api/runtime/status')
    status = json.loads(raw)
    if status.get('identity') != identity or status.get('readOnly') is not True or status.get('protectedWrites') != 0:
        raise ValueError('Runtime ownership/readonly identity differs')
    fixtures = []
    for route in ('api/lod/789/1', 'api/lod-family/789/Tile_789_L20_0uuuu2.osgb'):
        for _ in range(200):
            code, raw = request(route)
            if code != 202:
                break
            time.sleep(.1)
        if code != 200:
            raise RuntimeError('Source plan did not become ready')
        marker = json.loads(raw)
        token = marker.get('cache_lease', '')
        if not re.fullmatch('[0-9a-f]{32}', token):
            raise ValueError('Missing source lease')
        try:
            parts = [p for p in marker['parts'] if any(f['name'] == 'texture.png' for f in p['files'])]
            part = max(parts, key=lambda p: next(f['bytes'] for f in p['files'] if f['name'] == 'texture.png'))
            directory = part['directory']
            if not re.fullmatch('part_[0-9]{3}', directory):
                raise ValueError('Invalid source part')
            record = next(f for f in part['files'] if f['name'] == 'texture.png')
            folder = ('family_tile_%s_%s' % (marker['tile_id'], marker['family_key'])) if marker.get('family_key') else ('tile_%s_depth_%s' % (marker['tile_id'], marker['depth']))
            if not re.fullmatch('[A-Za-z0-9_.-]+', folder) or record['bytes'] > 33*1048576:
                raise ValueError('Invalid or oversized PNG')
            _, png = request('native/%s/%s/texture.png?lease=%s' % (folder, directory, token))
            if len(png) != record['bytes'] or hashlib.sha256(png).hexdigest() != record['sha256']:
                raise ValueError('PNG content differs')
            with Image.open(io.BytesIO(png)) as image:
                if image.mode != 'RGBA' or image.width * image.height * 4 > 32*1048576:
                    raise ValueError('Unexpected original RGBA storage')
                image.load()
                fixtures.append(dict(name=route + '/' + directory, route=route, directory=directory, bytes=len(png), pngSHA256=record['sha256'], rgbaSHA256=hashlib.sha256(image.tobytes()).hexdigest(), width=image.width, height=image.height))
        finally:
            request('api/lod-lease/%s/release' % token, 'POST')
    return fixtures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--identity', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.base, args.identity), indent=2))
