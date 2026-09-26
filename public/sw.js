/* Retire only WakeAgain's previous project-market app-shell caches on cutover. */
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(key=>key.startsWith('wakeagain-shell-')).map(key=>caches.delete(key)));
  await self.clients.claim();
  await self.registration.unregister();
})()));
// No fetch handler: new requests always go to the server.
