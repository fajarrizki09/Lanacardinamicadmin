const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const compiledApp = path.join(root, 'api', 'static', 'modules', 'app.js');
const runtimeApp = path.join(root, 'api', 'static', 'app.js');

if (fs.existsSync(compiledApp)) {
  fs.copyFileSync(compiledApp, runtimeApp);
  fs.rmSync(compiledApp);
  console.log('Copied compiled app.js to api/static/app.js');
}
