(()=>{
  const filters=[...document.querySelectorAll('[data-filter]')],cards=[...document.querySelectorAll('[data-book]')],search=document.querySelector('#book-search'),empty=document.querySelector('#empty-results'),count=document.querySelector('#results-count');
  let active='tout';
  const normalize=v=>(v||'').toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const render=()=>{
    const term=normalize(search?.value.trim());let visible=0;
    for(const card of cards){const matchesCategory=active==='tout'||card.dataset.category===active;const matchesText=normalize(card.dataset.search).includes(term);const show=matchesCategory&&matchesText;card.hidden=!show;card.style.display=show?'':'none';if(show)visible++;}
    if(empty)empty.classList.toggle('show',visible===0);
    if(count)count.textContent=`${visible} ouvrage${visible>1?'s':''} affiché${visible>1?'s':''}`;
  };
  filters.forEach(button=>button.addEventListener('click',()=>{active=button.dataset.filter;filters.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));render()}));
  search?.addEventListener('input',render);render();
  const toast=document.querySelector('#toast');let hideTimer;
  const notify=t=>{if(!toast)return;toast.textContent=t;toast.classList.add('visible');clearTimeout(hideTimer);hideTimer=setTimeout(()=>toast.classList.remove('visible'),2600)};
  document.querySelectorAll('[data-share]').forEach(btn=>btn.addEventListener('click',async()=>{
    const title=btn.dataset.title||document.title;
    try{if(navigator.share){await navigator.share({title,url:location.href});return;}if(navigator.clipboard){await navigator.clipboard.writeText(location.href);notify('Lien copié dans le presse-papiers');return;}notify('Copiez l’adresse de cette page pour la partager');}
    catch(e){if(e.name!=='AbortError')notify('Partage indisponible sur cet appareil');}
  }));
})();
