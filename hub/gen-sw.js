/* Retire the former gallery forwarding worker. Keep this URL through migration. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil((async () => {
  await self.clients.claim();
  await self.registration.unregister();
})()));
// No fetch or message forwarding: generation now runs in the private backend.
