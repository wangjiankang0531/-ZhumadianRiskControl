"""Patch one pinned experimental async parent-restoration controller; no program starts."""
import argparse
import hashlib
from pathlib import Path

BASE_SHA256 = '861f4c1c51af848970e6c81cfe6145992c94f4697c413b44c143fd818edd4997'


def patched_restore(raw):
    if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
        raise ValueError('Pinned parent restore source differs')
    nl = b'\r\n' if b'\r\n' in raw else b'\n'
    declaration = b'  std::vector<int> completeRootFallbacks;' + nl
    if raw.count(declaration) != 1:
        raise ValueError('Unexpected root fallback declaration')
    result = raw.replace(declaration, b'')
    old = (b'        if (parentRestoreFailed.contains({id,parent})) completeRootFallbacks.push_back(id);' + nl
           + b'        else restoreCandidates.emplace_back(id,parent);')
    new = (b'        // Keep the complete child cut when its parent cannot be restored.' + nl
           + b'        // Ordinary visibility/budget eviction remains responsible for root removal.' + nl
           + b'        if (!parentRestoreFailed.contains({id,parent})) restoreCandidates.emplace_back(id,parent);')
    if result.count(old) != 1:
        raise ValueError('Unexpected failure admission branch')
    result = result.replace(old, new)
    start = result.index(b'  std::sort(completeRootFallbacks.begin()')
    end = result.index(b'  const auto restorationCurrent', start)
    result = result[:start] + result[end:]
    old = b'      return !resident.contains(entry.first) || !resident.at(entry.first).families.contains(entry.second) ||'
    new = b'      return parentRestoreFailed.contains(entry) || !resident.contains(entry.first) || !resident.at(entry.first).families.contains(entry.second) ||'
    if result.count(old) != 1:
        raise ValueError('Unexpected restore candidate revalidation')
    result = result.replace(old, new)
    if b'completeRootFallbacks' in result:
        raise ValueError('Incomplete failed-restore eviction removal')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.input.resolve() == a.output.resolve():
        raise ValueError('Distinct fresh output required')
    result = patched_restore(a.input.read_bytes())
    with a.output.open('xb') as target:
        target.write(result)


if __name__ == '__main__':
    main()
