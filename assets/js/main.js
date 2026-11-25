(()=>{
  const filters=[...document.querySelectorAll('[data-filter]')],cards=[...document.querySelectorAll('[data-book]')],groups=[...document.querySelectorAll('[data-category-group]')],search=document.querySelector('#book-search'),empty=document.querySelector('#empty-results'),count=document.querySelector('#results-count');
  let active='tout';
  const normalize=v=>(v||'').toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const render=()=>{
    const term=normalize(search?.value.trim());let visible=0;
    for(const card of cards){const matchesCategory=active==='tout'||card.dataset.category===active;const matchesText=normalize(card.dataset.search).includes(term);const show=matchesCategory&&matchesText;card.hidden=!show;card.style.display=show?'':'none';if(show)visible++;}
    for(const group of groups){const groupVisible=[...group.querySelectorAll('[data-book]')].filter(c=>!c.hidden).length;group.hidden=groupVisible===0;group.style.display=groupVisible===0?'none':'';const badge=group.querySelector('[data-category-count]');if(badge)badge.textContent=`${groupVisible} ouvrage${groupVisible>1?'s':''}`;}
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
  const API='https://abacus.jasoncameron.dev';
  const safeKey=s=>String(s||'').toLowerCase().replace(/[^a-z0-9_-]/g,'-').slice(0,55);
  const fmt=n=>Number(n||0).toLocaleString(document.documentElement.lang==='ar'?'ar-EG':'fr-FR');
  const readCount=async(ns,key)=>{try{const r=await fetch(`${API}/get/${ns}/${key}`);if(!r.ok)return 0;const d=await r.json();return Number(d.value||0);}catch{return null;}};
  const hitCount=async(ns,key)=>{try{const r=await fetch(`${API}/hit/${ns}/${key}`,{keepalive:true});if(!r.ok)return null;const d=await r.json();return Number(d.value||0);}catch{return null;}};
  const visitEl=document.querySelector('[data-visit-counter]');
  if(visitEl){
    const ns=visitEl.dataset.visitCounter,key=safeKey(visitEl.dataset.visitKey||'visits'),out=visitEl.querySelector('[data-visit-count]');
    const flag=`visited_${ns}_${key}`;
    const done=sessionStorage.getItem(flag);
    (done?readCount(ns,key):hitCount(ns,key)).then(v=>{if(v!==null&&out){out.textContent=fmt(v);if(!done)sessionStorage.setItem(flag,'1');}});
  }
  const dlEl=document.querySelector('[data-dl-counter]');
  if(dlEl){
    const ns=dlEl.dataset.dlNs||'institut-excellence-v1',slug=dlEl.dataset.dlCounter,key=safeKey('dl-'+slug),out=dlEl.querySelector('[data-dl-count]');
    readCount(ns,key).then(v=>{if(v!==null&&out)out.textContent=fmt(v);});
    document.querySelectorAll('[data-dl-trigger]').forEach(el=>el.addEventListener('click',()=>{
      hitCount(ns,key).then(v=>{if(v!==null&&out)out.textContent=fmt(v);});
    }));
  }
  const promoStage=document.querySelector('[data-promo-stage]');
  if(promoStage){
    const facade=promoStage.querySelector('[data-promo-trigger]'),video=promoStage.querySelector('[data-promo-video]'),vStat=document.querySelector('[data-video-counter]'),vOut=vStat?.querySelector('[data-video-count]');
    const vNs=vStat?.dataset.videoNs||'institut-excellence-v1',vKey=safeKey('vid-'+(vStat?.dataset.videoCounter||'promo'));
    let countedPlay=false;
    if(vOut)readCount(vNs,vKey).then(v=>{if(v!==null)vOut.textContent=fmt(v);});
    const launchVideo=(scrollInto)=>{
      if(scrollInto)document.querySelector('#presentation')?.scrollIntoView({behavior:'smooth',block:'center'});
      const mobile=window.matchMedia('(max-width: 680px)').matches;
      const targetSrc=mobile?promoStage.dataset.srcMobile:promoStage.dataset.srcDesktop;
      const targetPoster=mobile?promoStage.dataset.posterMobile:promoStage.dataset.posterDesktop;
      if(!video.getAttribute('src')||video.getAttribute('src')!==targetSrc){
        video.setAttribute('poster',targetPoster||'');
        video.setAttribute('src',targetSrc||'');
        video.load();
      }
      if(facade)facade.hidden=true;
      video.hidden=false;
      video.play().catch(()=>{});
      if(!countedPlay){
        countedPlay=true;
        hitCount(vNs,vKey).then(v=>{if(v!==null&&vOut)vOut.textContent=fmt(v);});
      }
    };
    facade?.addEventListener('click',()=>launchVideo(false));
    document.querySelectorAll('[data-play-promo]').forEach(btn=>btn.addEventListener('click',e=>{
      e.preventDefault();
      launchVideo(btn.tagName==='A');
    }));
  }
})();
