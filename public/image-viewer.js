'use strict';
function openImageViewer(images,title,description='',start=0){
 const previous=document.activeElement,viewer=document.createElement('dialog');
 viewer.className='image-viewer';viewer.setAttribute('aria-label',title+' 이미지 보기');
 let index=Math.min(start,images.length-1),zoom=false;
 viewer.innerHTML=`<header><strong>${esc(title)}</strong><button type="button" data-view-close aria-label="이미지 닫기">닫기 ×</button></header><div class="viewer-stage"><img alt=""></div><div class="viewer-controls"><button type="button" data-view-prev aria-label="이전 이미지">← 이전</button><span role="status"></span><button type="button" data-view-next aria-label="다음 이미지">다음 →</button><button type="button" data-view-zoom>원본 크기</button></div><p class="preserve-lines">${esc(description)}</p>`;
 document.body.append(viewer);const stage=viewer.querySelector('.viewer-stage'),img=viewer.querySelector('img');
 function paint(){img.src=images[index];img.alt=title+' · '+(index+1)+'번째 이미지';viewer.querySelector('[role=status]').textContent=(index+1)+' / '+images.length;viewer.querySelector('[data-view-prev]').disabled=index===0;viewer.querySelector('[data-view-next]').disabled=index===images.length-1;zoom=false;stage.classList.remove('original-size');viewer.querySelector('[data-view-zoom]').textContent='원본 크기';stage.scrollTop=0;stage.scrollLeft=0;}
 viewer.querySelector('[data-view-close]').onclick=()=>viewer.close();
 viewer.querySelector('[data-view-prev]').onclick=()=>{if(index>0){index--;paint();}};
 viewer.querySelector('[data-view-next]').onclick=()=>{if(index<images.length-1){index++;paint();}};
 viewer.querySelector('[data-view-zoom]').onclick=e=>{zoom=!zoom;stage.classList.toggle('original-size',zoom);e.target.textContent=zoom?'화면에 맞추기':'원본 크기';};
 viewer.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'&&index>0){e.preventDefault();index--;paint();}if(e.key==='ArrowRight'&&index<images.length-1){e.preventDefault();index++;paint();}});
 const overflow=document.body.style.overflow;document.body.style.overflow='hidden';
 viewer.addEventListener('close',()=>{document.body.style.overflow=overflow;viewer.remove();if(previous?.isConnected)previous.focus({preventScroll:true});});
 paint();viewer.showModal();viewer.querySelector('[data-view-close]').focus();
}
