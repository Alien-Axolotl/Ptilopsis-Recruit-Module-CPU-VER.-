const net = require('net');
const { concurrently } = require('concurrently');

function listenOnFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, () => resolve(server));
  });
}

async function findFreePorts(count) {
  const servers = await Promise.all(Array.from({ length: count }, listenOnFreePort));
  const ports = servers.map((server) => server.address().port);
  await Promise.all(servers.map((server) => new Promise((resolve) => server.close(resolve))));
  return ports;
}

async function start() {
  const [frontendPort, backendPort] = await findFreePorts(2);

  process.env.FRONTEND_URL = `http://localhost:${frontendPort}`;
  process.env.VITE_API_BASE = `http://localhost:${backendPort}`;

  const { result } = concurrently([
    `npm run dev --prefix ../frontend -- --port ${frontendPort} --strictPort`,
    `..\\venv\\Scripts\\uvicorn.exe App.main:app --reload --reload-dir ../backend --app-dir ../backend --port ${backendPort}`,
    `wait-on http://localhost:${frontendPort} http-get://localhost:${backendPort}/health && electron .`,
  ], {
    killOthersOn: ['success', 'failure'],
    successCondition: 'first',
  });

  await result;
}

start().catch(() => {
  process.exitCode = 1;
});
