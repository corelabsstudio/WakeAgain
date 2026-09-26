'use strict';
let installPrompt;
window.addEventListener('beforeinstallprompt',event=>{
  event.preventDefault();
  installPrompt=event;
});
document.querySelector('#install-app')?.addEventListener('click',async()=>{
  if(window.matchMedia('(display-mode: standalone)').matches||navigator.standalone){
    toast('이미 홈 화면에서 실행 중입니다.');
    return;
  }
  if(installPrompt){
    const prompt=installPrompt;
    installPrompt=null;
    await prompt.prompt();
    return;
  }
  const ios=/iPad|iPhone|iPod/.test(navigator.userAgent);
  const instructions=ios
    ? 'Safari에서 아래쪽 공유 버튼을 누르고 ‘홈 화면에 추가’를 선택해 주세요.'
    : '브라우저 메뉴에서 ‘홈 화면에 추가’ 또는 ‘앱 설치’를 선택해 주세요.';
  show('휴대폰 홈 화면에 추가',`<p>${instructions}</p><p class="subtle">추가한 아이콘으로 WakeAgain을 바로 열 수 있습니다.</p>`,'WAKEAGAIN');
});
if('serviceWorker' in navigator){
  window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}
