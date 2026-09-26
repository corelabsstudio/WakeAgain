/* Keep installation available while removing the retired project's cached shell. */
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(key=>key.startsWith('wakeagain-shell-')).map(key=>caches.delete(key)));
  await self.clients.claim();
})()));
// No fetch handler: private pages and API requests always go to the server.
