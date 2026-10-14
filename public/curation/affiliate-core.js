(function(root){
 function linkState(product,config,now=Date.now()){
  const blocked=reason=>({enabled:false,reason,url:null});
  if(product.demo)return blocked('데모 상품 · 제휴 승인 전');
  if(!product.affiliateApproved)return blocked('제휴 승인 확인 전');
  const program=config.programs.find(item=>item.id===product.programId&&item.approved===true);
  if(!program)return blocked('제휴 프로그램 확인 전');
  if(!product.disclosure)return blocked('수수료 관계 고지 준비 중');
  if(product.stock==='soldout')return blocked('판매처 품절');
  if(product.stock!=='available')return blocked('판매 가능 여부 확인 전');
  if(!product.expiresAt||!Number.isFinite(Date.parse(product.expiresAt))||Date.parse(product.expiresAt)<=now)return blocked('링크 만료 또는 유효기간 확인 전');
  if(!product.lastVerifiedAt||!Number.isFinite(Date.parse(product.lastVerifiedAt))||Date.parse(product.lastVerifiedAt)>now||now-Date.parse(product.lastVerifiedAt)>(program.maxVerificationAgeHours||24)*3600000)return blocked('링크 재확인 필요');
  let url;try{url=new URL(product.affiliateUrl);}catch(_){return blocked('제휴 링크 연결 준비 중');}
  if(url.protocol!=='https:'||url.username||url.password||(url.port&&url.port!=='443'))return blocked('올바른 HTTPS 제휴 링크 필요');
  if(!Array.isArray(program.allowedHosts)||!program.allowedHosts.includes(url.hostname))return blocked('승인된 판매처 주소 필요');
  let tracking=false;
  if(program.trackingMode==='path'&&program.trackingPathPattern){try{tracking=new RegExp(program.trackingPathPattern).test(url.pathname);}catch(_){}}
  else tracking=Array.isArray(program.requiredTrackingParams)&&program.requiredTrackingParams.length>0&&program.requiredTrackingParams.every(key=>url.searchParams.get(key));
  if(!tracking)return blocked('사용자 추적 링크 확인 전');
  if(!product.linkVerified)return blocked('발급 링크 검증 전');
  return {enabled:true,reason:'판매처에서 구매하기',url:url.href};
 }
 function publicProducts(config){return config.products.filter(item=>!item.demo&&item.affiliateApproved===true);}
 function compareProducts(products,ids){return ids.slice(0,3).map(id=>products.find(item=>item.id===id)).filter(Boolean);}
 const api={linkState,publicProducts,compareProducts};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Affiliate=api;
})(typeof globalThis!=='undefined'?globalThis:this);
