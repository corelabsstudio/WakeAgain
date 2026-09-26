(function(root){
 'use strict';
 const prefix='wa.draft.v1.';
 function key(user,route){return prefix+encodeURIComponent(user)+'.'+encodeURIComponent(route);}
 function read(storage,user,route,now=Date.now()){
  try{const k=key(user,route),v=JSON.parse(storage.getItem(k)||'null');if(!v)return null;if(v.user!==user||v.updated<now-7*86400000){storage.removeItem(k);return null;}return v.data;}catch{return null;}
 }
 function write(storage,user,route,data,now=Date.now()){try{storage.setItem(key(user,route),JSON.stringify({user,updated:now,data}));return true;}catch{return false;}}
 function remove(storage,user,route){try{storage.removeItem(key(user,route));}catch{}}
 function clearUser(storage,user){try{const start=prefix+encodeURIComponent(user)+'.';for(const k of Object.keys(storage))if(k.startsWith(start))storage.removeItem(k);}catch{}}
 const api={read,write,remove,clearUser};if(typeof module!=='undefined')module.exports=api;else root.DraftStore=api;
})(typeof window!=='undefined'?window:globalThis);
