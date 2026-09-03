const assert = require('assert');
const express = require('../lib/express');

describe('express baseline', function() {
  it('should create express application', function() {
    const app = express();
    assert.strictEqual(typeof app.handle, 'function');
    assert.strictEqual(typeof app.use, 'function');
    assert.strictEqual(typeof app.get, 'function');
  });

  it('should register get routes properly', function() {
    const app = express();
    app.get('/api/health', function(req, res) {
      return { ok: true };
    });
    assert.strictEqual(app.routes.length, 1);
    assert.strictEqual(app.routes[0].path, '/api/health');
  });
});
