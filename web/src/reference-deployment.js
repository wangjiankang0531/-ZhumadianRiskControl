/** Keep a synthetic-business deployment inside its current directory. */
export function referenceApiURL(path, href) {
  if (typeof path !== 'string' || !/^[a-z][a-z-]*(?:\?[^#]*)?$/.test(path)) throw Error('Invalid business API path');
  return new URL('api/demo/' + path, new URL('./', href)).href;
}

export function referenceNavigation(deployment) {
  if (deployment?.mode === 'public-business') return [];
  return [
    ['三维一张图', 'http://127.0.0.1:8767/?topic=emergency'],
    ['原业务门户', 'http://127.0.0.1:8767/portal.html'],
  ];
}
