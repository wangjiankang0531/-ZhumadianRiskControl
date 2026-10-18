import test from 'node:test';
import assert from 'node:assert/strict';
import {referenceApiURL, referenceNavigation} from '../src/reference-deployment.js';

test('business API stays within root or IIS/Apache subdirectory', () => {
  for (const [base, expected] of [
    ['http://127.0.0.1:8792/#work-reservation', 'http://127.0.0.1:8792/api/demo/catalog'],
    ['https://www.joinlinksmart.com/zhumadian/#work-reservation', 'https://www.joinlinksmart.com/zhumadian/api/demo/catalog'],
    ['https://www.joinlinksmart.com/zhumadian/reference-demo.html', 'https://www.joinlinksmart.com/zhumadian/api/demo/catalog'],
  ]) assert.equal(referenceApiURL('catalog', base), expected);
  assert.equal(referenceApiURL('records?entity=hidden-danger&page=2', 'https://example.test/zhumadian/'), 'https://example.test/zhumadian/api/demo/records?entity=hidden-danger&page=2');
});

test('business API cannot replace the destination with an arbitrary URL', () => {
  for (const path of ['../health','/catalog','https://bad.test','catalog#leak','catalog/other']) assert.throws(() => referenceApiURL(path, 'https://example.test/zhumadian/'));
});

test('public business mode omits development-machine links; local mode keeps them', () => {
  assert.deepEqual(referenceNavigation({mode:'public-business'}), []);
  assert.equal(referenceNavigation().length, 2);
});
