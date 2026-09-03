'use strict';

const EventEmitter = require('events').EventEmitter;
const proto = require('./application');

function createApplication() {
  const app = function(req, res, next) {
    app.handle(req, res, next);
  };

  Object.assign(app, EventEmitter.prototype, proto);
  app.init();
  return app;
}

exports = module.exports = createApplication;
exports.application = proto;
