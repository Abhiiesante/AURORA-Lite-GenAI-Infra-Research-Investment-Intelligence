#!/usr/bin/env node
/**
 * Prepares the web app for static export by stubbing dynamic API routes.
 * For now we simply create a marker that components can check to avoid calling local API handlers.
 * In the future we could transform imports automatically.
 */
const fs = require('fs');
const path = require('path');
const marker = path.join(__dirname, '..', '.static-export');
try {
  fs.writeFileSync(marker, 'static export mode');
  console.log('[prepare-static-export] marker created');
} catch (e) {
  console.warn('[prepare-static-export] failed to create marker', e);
}
