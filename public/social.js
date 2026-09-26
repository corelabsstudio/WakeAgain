'use strict';
const emailLogin=login;
const consentText='회원 식별정보·이름·제공에 동의한 이메일을 가입과 서비스 이용에 사용합니다. 계정 삭제 요청은 운영 문의로 접수합니다.';
function socialButtons(p,link=false){return ['kakao','google'].map(k=>`<button type="button" class="social-button ${k}" data-social="${k}" ${p[k].linked&&link?'disabled':''}><span aria-hidden="true">${k==='kakao'?'●':'G'}</span>${k==='kakao'?'카카오':'Google'}${link?(p[k].linked?' 연결됨':' 연결하기'):'로 시작하기'}${p[k].ready?'':' · 연결 준비 중'}</button>`).join('');}
function bindSocial(link=false){$$('[data-social]').forEach(b=>b.addEventListener('click',()=>run(async()=>{
 const issue=$('#social-error');issue.textContent='';
 if(!$('#social-consent').checked){issue.textContent='계정 정보 수집·이용에 동의해 주세요.';$('#social-consent').focus();return;}
 try{const r=await post('/auth/oauth/'+b.dataset.social+'/start',{intent:link?'link':'login',consent:true});location.assign(r.url);}
 catch(e){issue.textContent=e.message;issue.scrollIntoView({block:'nearest'});}
},b)));$('#social-consent').addEventListener('change',()=>{$('#social-error').textContent='';});}
login=async function(next=()=>dashboard()){
 const p=await api('/auth/providers');
 show('WakeAgain 로그인',`<div class="login-panel"><p>쓰고 계신 계정으로 간편하게 시작하세요.<br>처음이라면 회원가입도 함께 진행됩니다.</p><div class="social-buttons">${socialButtons(p)}</div><label class="check"><input id="social-consent" type="checkbox">${consentText} 수집·이용에 동의합니다.</label><p class="app-error" id="social-error" role="alert"></p><p class="subtle"><a href="/legal/privacy.html" target="_blank" rel="noopener">개인정보처리방침</a> · <a href="/legal/terms.html" target="_blank" rel="noopener">이용약관</a></p>${p.email_ready?`<div class="login-divider">또는</div><button type="button" class="button secondary email-login" id="email-login">이메일 인증으로 시작하기</button><p class="subtle">기존 계정이 있다면 기존 방식으로 로그인한 후 ‘로그인·연락처’에서 다른 계정을 연결해 주세요.</p>`:""}</div>`,'WELCOME');
 bindSocial();$('#email-login')?.addEventListener('click',()=>emailLogin(next));
};
async function accountSettings(){
 user=await api('/me');const p=await api('/auth/providers');
 show('로그인·연락처',`<p>연결한 계정으로 같은 작업 공간에 들어올 수 있습니다.</p><div class="social-buttons">${socialButtons(p,true)}</div><label class="check"><input id="social-consent" type="checkbox">${consentText} 계정 연결에 동의합니다.</label><p class="app-error" id="social-error" role="alert"></p><h3>이메일</h3>${user.email?`<p>${esc(user.email)} · 인증됨</p>`:(p.email_ready?`<p>카카오에서 이메일을 받지 않았습니다. 이메일 알림을 받으려면 인증해 주세요.</p><form id="active-form">${input('email','알림 받을 이메일','','email','required maxlength="254"')}${err}<button class="button primary">인증번호 받기</button></form>`:`<p>이메일 인증은 준비 중입니다.</p>`)}<div class="app-actions">${button('작업 공간으로','dashboard')}</div>`);
 bindSocial(true);
 if(!user.email&&p.email_ready)bindForm(async d=>{
  const r=await post('/auth/code',d);
  show('이메일 인증',`<p>${esc(d.email)}로 보낸 인증번호를 입력해 주세요.</p>${r.development_code?`<p class="dev-code">개발용 인증번호: ${r.development_code}</p>`:''}<form id="active-form">${input('code','인증번호','','text','required pattern="[0-9]{6}" maxlength="6" inputmode="numeric"')}${err}<button class="button primary">이메일 등록</button></form>`);
  bindForm(async v=>{await post('/auth/contact-email',{...d,...v,name:user.name.length>=2?user.name:'회원'});await accountSettings();toast('이메일을 인증했습니다.');});
 });
}
const socialDashboard=dashboard;
dashboard=async function(tab='requests'){if(tab==='account')return accountSettings();await socialDashboard(tab);if(user)$('.app-tabs')?.insertAdjacentHTML('beforeend','<button data-action="dashboard" data-value="account">로그인·연락처</button>');};
window.addEventListener('load',()=>run(async()=>{
 const url=new URL(location.href),status=url.searchParams.get('auth');if(!status)return;
 url.searchParams.delete('auth');history.replaceState(null,'',url.pathname+url.search+url.hash);
 const messages={success:'로그인했습니다.',linked:'로그인 계정을 연결했습니다.',expired:'로그인 요청이 만료되거나 브라우저가 달라졌습니다. 다시 시작해 주세요.',cancelled:'로그인을 취소했습니다.',failed:'로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.',in_use:'이미 다른 계정에 연결되어 있습니다.',existing:'같은 이메일로 가입한 계정이 있습니다. 기존 방식으로 로그인한 뒤 로그인·연락처에서 연결해 주세요.'};
 user=await api('/session');updateAccount();
 if(status==='success'&&user)await (window.resumeWorkspace?window.resumeWorkspace():dashboard('portfolio'));else if(status==='linked'&&user)await dashboard('account');else await login();
 toast(messages[status]||'로그인을 다시 시작해 주세요.');
}));
