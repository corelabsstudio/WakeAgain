'use strict';
// Keep the existing form and submit handlers; reveal only the current group.
function guidedForm(groups){
 const form=document.querySelector('#active-form');if(!form||form.dataset.guided)return;
 form.dataset.guided='true';form.noValidate=true;
 const intro=document.querySelector('#app-content > p:not(.draft-status)');if(intro)intro.remove();
 const bar=document.createElement('ol');bar.className='flow-steps';bar.setAttribute('aria-label','작성 단계');
 const panels=groups.map((g,i)=>{const panel=document.createElement('section');panel.className='flow-panel';panel.innerHTML=`<h2 tabindex="-1">${esc(g.title)}</h2><p>${esc(g.description)}</p><div class="form-grid"></div>`;const grid=panel.querySelector('.form-grid');for(const selector of g.fields){const el=form.querySelector(selector);if(el)grid.append(el);}form.append(panel);bar.insertAdjacentHTML('beforeend',`<li><span>${i+1}</span>${esc(g.label)}</li>`);return panel;});
 form.before(bar);
 // Empty original grids no longer take up space. Field nodes retain their values/events.
 form.querySelectorAll(':scope > .form-grid').forEach(el=>{if(!el.children.length)el.remove();});
 const actions=form.querySelector('.app-actions');if(actions)form.append(actions);
 const previous=document.createElement('button');previous.type='button';previous.className='button secondary';previous.textContent='이전';
 const next=document.createElement('button');next.type='button';next.className='button primary';next.textContent='다음';
 const controls=document.createElement('div');controls.className='flow-controls';controls.append(previous);if(actions)controls.append(actions);controls.append(next);form.append(controls);
 let index=0;
 const paint=(focus=false)=>{panels.forEach((p,i)=>p.hidden=i!==index);[...bar.children].forEach((li,i)=>{li.toggleAttribute('data-current',i===index);if(i===index)li.setAttribute('aria-current','step');else li.removeAttribute('aria-current');});previous.hidden=index===0;next.hidden=index===panels.length-1;if(actions)actions.hidden=index!==panels.length-1;if(focus)panels[index].querySelector('h2').focus();};
 const valid=panel=>{const bad=[...panel.querySelectorAll('input,select,textarea')].find(e=>!e.checkValidity());if(bad){bad.reportValidity();return false;}return true;};
 previous.onclick=()=>{index--;paint(true);};next.onclick=()=>{if(valid(panels[index])){index++;paint(true);}};
 form.addEventListener('submit',e=>{if(index<panels.length-1){e.preventDefault();e.stopImmediatePropagation();next.click();return;}const bad=[...form.elements].find(el=>el.willValidate&&!el.checkValidity());if(bad){e.preventDefault();e.stopImmediatePropagation();const target=panels.findIndex(p=>p.contains(bad));if(target>=0){index=target;paint();}bad.reportValidity();}},true);
 paint();
}
const stepBrief=briefForm;
briefForm=async function(...args){await stepBrief(...args);const form=$('#active-form');if(!form)return;
 if(form.querySelector('[name=line]'))guidedForm([
 {label:'작업 선택',title:'어떤 작업을 맡기시나요?',description:'필요한 작업을 한 줄로 알려주세요.',fields:['.form-grid']},
 {label:'세부 조건',title:'작업 조건을 골라주세요',description:'선택한 내용으로 의뢰 초안을 정리합니다.',fields:['#guide-questions']}
 ]);
 else if(form.querySelector('[name=budget]')){const field=n=>`#f-${n}`;const move=n=>{const el=form.querySelector(field(n));if(el)el.parentElement.dataset.flowField=n;};['scope','materials','budget','deadline','reference'].forEach(move);guidedForm([
 {label:'내용 확인',title:'맡길 내용을 확인해 주세요',description:'자동으로 정리한 문장을 직접 고칠 수 있어요.',fields:['.form-grid','[data-flow-field=scope]','[data-flow-field=materials]']},
 {label:'조건 확인',title:'세부 조건을 확인해 주세요',description:'견적에 포함할 항목을 선택하세요.',fields:['#brief-conditions','#brief-scope-note']},
 {label:'예산·일정',title:'예산과 완료일은 어떻게 되나요?',description:'저장한 초안은 아직 전문가에게 전달되지 않습니다.',fields:['[data-flow-field=budget]','[data-flow-field=deadline]','[data-flow-field=reference]']}
 ]);}
};
const stepQuote=quoteForm;
quoteForm=async function(...args){await stepQuote(...args);const form=$('#active-form');if(!form?.querySelector('[name=amount]'))return;for(const n of ['title','amount','days','revisions','scope','exclusions'])form.querySelector(`[name=${n}]`).parentElement.dataset.flowField=n;
 guidedForm([
 {label:'범위·납품물',title:'어디까지 작업하시나요?',description:'포함되는 작업과 별도 비용이 드는 항목을 구분해 주세요.',fields:['[data-flow-field=title]','[data-flow-field=scope]','[data-flow-field=exclusions]']},
 {label:'금액·기간',title:'금액과 작업 기간을 정해 주세요',description:'수정 횟수까지 함께 안내합니다.',fields:['[data-flow-field=amount]','[data-flow-field=days]','[data-flow-field=revisions]','label.check']}
 ]);
};
