"""Six anonymous static GETs; no login, business APIs, cookies or server writes."""
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from html.parser import HTMLParser
from datetime import datetime, timezone
import gzip, hashlib, json, time, urllib.request

ROOT = Path(__file__).resolve().parent / 'public-performance-recheck-r856'
BASE = 'https://www.joinlinksmart.com'

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('src'):
            self.urls.append(a['src'])

def run():
    ROOT.mkdir(exist_ok=False)
    rows = []
    def fetch(path, label, repeat):
        url = urljoin(BASE, path)
        parsed = urlsplit(url)
        assert parsed.scheme == 'https' and parsed.netloc == 'www.joinlinksmart.com'
        assert parsed.path.startswith('/zhumadian/') and not parsed.query
        request = urllib.request.Request(url, headers={
            'Accept-Encoding': 'gzip',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0.0.0 Safari/537.36'})
        start = time.perf_counter()
        with urllib.request.urlopen(request, timeout=30) as response:
            final = urlsplit(response.url)
            assert final.scheme == 'https' and final.netloc == parsed.netloc
            assert final.path.startswith('/zhumadian/') and not final.query
            first = time.perf_counter() - start
            raw = response.read(8 * 1024**2 + 1)
            assert len(raw) <= 8 * 1024**2
            headers = {k: response.headers.get(k) for k in (
                'Content-Type', 'Content-Encoding', 'Cache-Control', 'ETag', 'Vary')}
            status = response.status
        elapsed = time.perf_counter() - start
        encoding = headers['Content-Encoding']
        assert encoding in (None, 'identity', 'gzip')
        body = gzip.decompress(raw) if encoding == 'gzip' else raw
        rows.append(dict(label=label, repeatedRequest=repeat, path=parsed.path,
            httpStatus=status, ttfbSeconds=round(first, 4), totalSeconds=round(elapsed, 4),
            wireBytes=len(raw), decodedBytes=len(body), decodedSHA256=hashlib.sha256(body).hexdigest(),
            headers=headers))
        (ROOT/'measurements.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf8')
        print(json.dumps(rows[-1]), flush=True)
        return body
    try:
        for path, label in [('/zhumadian/home', 'home'),
                            ('/zhumadian/emergency/home/index', 'emergency')]:
            body = fetch(path, label+'-html', False)
            parser = Scripts(); parser.feed(body.decode('utf8'))
            entries = []
            for value in parser.urls:
                p = urlsplit(urljoin(BASE+path, value))
                if (p.netloc == 'www.joinlinksmart.com' and p.path.startswith('/zhumadian/')
                        and p.path.endswith('.js') and not p.query):
                    entries.append(p.path)
            assert len(entries) == 1, 'Expected one original entry script'
            fetch(entries[0], label+'-js', False)
            fetch(entries[0], label+'-js', True)
        proof = dict(completed=True, measuredAtUTC=datetime.now(timezone.utc).isoformat(),
            rows=rows, anonymousOnly=True, requests=6, browserCacheMeasured=False,
            authenticatedPagesOrBusinessAPIsMeasured=False, cookieOrAuthorizationSent=False,
            requestCacheControlSent=False, desktopUsed=False, publicChanged=False)
        (ROOT/'result.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf8')
    except Exception as error:
        (ROOT/'failure.json').write_text(json.dumps(dict(type=type(error).__name__,
            completedRequests=len(rows)))+'\n', encoding='utf8')
        raise

if __name__ == '__main__':
    run()
