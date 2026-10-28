"""Fix the pinned original reservation edit's missing work end-time assignment.

Build a separate source candidate. Never modify Reference, a runtime, a database,
workflow status, personnel selection, notifications or an installed release.
"""
from pathlib import Path
import hashlib

SOURCE_SHA256 = '36641cc68200ae32fc28a9b4b1606d40d09f9ee618bb93d5b7cba923cd8c972b'
BEGIN = '    public boolean updateById(WorkReservationBaseVo vo){'
END = '    public void sendMessage(WorkReservationBaseVo vo)'


def adapt(raw: bytes) -> bytes:
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('PINNED_ORIGINAL_WORK_RESERVATION_SERVICE_REQUIRED')
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8').replace('\r\n', '\n')
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError('EXACT_RESERVATION_EDIT_BOUNDARIES_REQUIRED')
    start = text.index(BEGIN)
    end = text.index(END, start)
    section = text[start:end]
    old = '        work.setStartTime(vo.getBase().getStartTime());\n'
    if section.count(old) != 1 or 'work.setEndTime(' in section:
        raise ValueError('EXACT_MISSING_END_TIME_ASSIGNMENT_REQUIRED')
    section = section.replace(old, old + '        work.setEndTime(vo.getBase().getEndTime());\n', 1)
    result = text[:start] + section + text[end:]
    return result.replace('\n', '\r\n').encode('utf-8') if crlf else result.encode('utf-8')


def build(source: Path, output: Path):
    candidate = adapt(source.read_bytes())
    if output.exists():
        raise ValueError('FRESH_CANDIDATE_OUTPUT_REQUIRED')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    return {'originalSHA256': SOURCE_SHA256,
            'candidateSHA256': hashlib.sha256(candidate).hexdigest(),
            'referenceChanged': False, 'installed': False}
