'use strict';
// Query URLs are full document destinations, including direct visits and refreshes.
const workPageId=new URLSearchParams(location.search).get('work');
const browseKey='wa.browse.return';
if(workPageId){
 document.body.classList.add('work-detail-mode');
 $('#work-page').hidden=false;
 $('#project-content').innerHTML='<h1 id="project-title">작업을 불러오는 중입니다.</h1>';
 $('.skip').href='#work-page';
 document.querySelectorAll('a[href="#top"],a[href="#explore"]').forEach(a=>a.href='/');
 $('#saved-nav').addEventListener('click',()=>{try{sessionStorage.setItem(browseKey,JSON.stringify({category:'all',collection:'all',query:'',savedOnly:true,y:0}));}catch{}location.href='/';});
 let opening=false;
 async function loadWorkPage(){
  if(opening)return;opening=true;
  try{
   if(!allConcepts.some(p=>p.id===workPageId)){
    const current=await api('/portfolios/'+encodeURIComponent(workPageId));
    realWorks=realWorks.filter(p=>p.id!==workPageId);realWorks.push(current);
   }
   detail(workPageId);
   $('#project-title')?.focus({preventScroll:true});
  }catch(e){
   document.title='작업을 확인할 수 없습니다 — WakeAgain';
   $('#project-content').innerHTML=`<div class="work-unavailable"><h1 id="project-title">작업을 확인할 수 없습니다</h1><p>${esc(e.status===404?'삭제되었거나 비공개로 전환된 작업입니다.':e.message)}</p><a class="button secondary" href="/">다른 작업 둘러보기</a></div>`;
  }finally{opening=false;}
 }
 document.addEventListener('works-ready',loadWorkPage);
 // Loading a shared URL does not depend on the home gallery request succeeding.
 loadWorkPage();
}else{
 try{
  const previous=JSON.parse(sessionStorage.getItem(browseKey)||'null');
  if(previous){
   category=categories[previous.category]?previous.category:'all';
   collection=['all','experts','concepts'].includes(previous.collection)?previous.collection:'all';
   query=String(previous.query||'');savedOnly=!!previous.savedOnly;
   $('#search-input').value=query;render();
   const restore=()=>requestAnimationFrame(()=>scrollTo(0,Number(previous.y)||0));
   restore();document.addEventListener('works-ready',restore,{once:true});
  }
 }catch{}
 function rememberBrowse(){try{sessionStorage.setItem(browseKey,JSON.stringify({category,collection,query,savedOnly,y:scrollY}));}catch{}}
 document.addEventListener('click',e=>{if(e.target.closest('a[href^="/?work="]'))rememberBrowse();});
 window.addEventListener('pagehide',rememberBrowse);
}
