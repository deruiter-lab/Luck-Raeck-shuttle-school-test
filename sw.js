/* Shuttle-school: werkt ook zonder internet na het eerste bezoek */
const VER='20261109210165';
/* test en productie draaien op hetzelfde domein: elk houdt zijn eigen caches */
const PRE=/-test\//i.test(self.registration.scope)?'shuttle-test-':'shuttle-school-';
const CACHE=PRE+VER;
const AUDIO_CACHE=PRE+'audio-m2';
const CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>(k.startsWith(PRE)||k.startsWith('shuttle-audio-'))&&k!==CACHE&&k!==AUDIO_CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const r=e.request; if(r.method!=='GET') return;
  if(r.mode==='navigate'){ /* nieuwste versie als er internet is, anders de bewaarde */
    e.respondWith(fetch(r).then(res=>{const cp=res.clone();caches.open(CACHE).then(c=>c.put('./index.html',cp));return res;}).catch(()=>caches.match('./index.html')));
    return; }
  if(r.url.includes('/audio/')){ /* lijst met ingesproken fragmenten altijd vers ophalen */
    if(r.url.endsWith('.json')){ e.respondWith(fetch(r).then(res=>{const cp=res.clone();caches.open(AUDIO_CACHE).then(c=>c.put(r,cp));return res;}).catch(()=>caches.match(r))); return; }
    return; } /* geluid zelf niet onderscheppen: iPhones vragen het in stukjes op */
  e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{
    if(res.ok&&(r.url.startsWith(self.location.origin)||/fonts\.(googleapis|gstatic)\.com|cdnjs\.cloudflare\.com/.test(r.url))){const cp=res.clone();caches.open(CACHE).then(c=>c.put(r,cp));}
    return res;}).catch(()=>hit)));
});
