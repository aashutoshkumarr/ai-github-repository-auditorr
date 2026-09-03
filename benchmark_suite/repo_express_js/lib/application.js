'use strict';

const app = exports = module.exports = {};

app.init = function() {
  this.settings = {};
  this.routes = [];
};

app.use = function(fn) {
  this.routes.push({ type: 'middleware', handler: fn });
  return this;
};

app.get = function(path, fn) {
  this.routes.push({ type: 'route', method: 'GET', path: path, handler: fn });
  return this;
};

app.post = function(path, fn) {
  this.routes.push({ type: 'route', method: 'POST', path: path, handler: fn });
  return this;
};

app.handle = function(req, res, callback) {
  for (const r of this.routes) {
    if (r.type === 'route' && r.path === req.url) {
      return r.handler(req, res);
    }
  }
  if (callback) callback();
};
