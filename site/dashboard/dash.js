const fmt = n => (n||0).toLocaleString();
const COL={live:'#22c55e',sandbox:'#f59e0b',pending:'#3b82f6',off:'#9ca3af'};
const ORD={live:0,sandbox:1,pending:2,off:3};
const EMO={Blog:'📝',Facebook:'👥',Instagram:'📸',YouTube:'🔔',Blogger:'✍️',Tumblr:'🌀',Telegraph:'📄',
  Bluesky:'🦋',Mastodon:'🐘',Threads:'🧵',Telegram:'✈️','GitHub Pages':'🐙',Pinterest:'📌',Email:'📧',
  LinkedIn:'💼',TikTok:'🎵','Google Business':'📍'};
function $(id){return document.getElementById(id);}
function sortCh(ch){return [...ch].sort((a,b)=>(ORD[a.status]??9)-(ORD[b.status]??9));}

function renderScoreboard(d){
  const el=$('scoreboard'); if(!el||!d.channels) return;
  el.innerHTML=sortCh(d.channels).map(c=>{
    const big=c.followers!=null?c.followers:c.count;
    const unit=c.followers!=null?'followers':c.unit;
    const sub=c.status==='pending'?'Pending':(unit+' · '+c.status);
    return `<div class="ccard" style="--st:${COL[c.status]||'#9ca3af'}">
      <div class="cc-top"><span class="cc-emo">${EMO[c.name]||'•'}</span><span class="cc-grade gcolor-${c.grade||'F'}">${c.grade||'—'}</span></div>
      <div class="cc-val">${fmt(big)}</div><div class="cc-lab">${c.name}</div><div class="cc-sub">${sub}</div></div>`;
  }).join('');
}

function renderFunnel(d){
  const el=$('funnel'); if(!el||!d.funnel) return;
  const f=d.funnel,t=d.trends||{};
  const stages=[
    {label:'👀 Reach',val:f.reach,tr:t.reach},
    {label:'🔥 Engagement',val:f.engagement,tr:t.engagement},
    {label:'👥 Audience (followers + email)',val:f.audience,tr:t.audience},
    {label:'🎯 Consent Resolve clicks',val:f.cr_clicks,tr:null}];
  const max=Math.max(1,...stages.map(s=>s.val));
  el.innerHTML=stages.map(s=>{
    const w=Math.max(5,Math.round(100*s.val/max));
    const tr=(s.tr!=null&&s.tr!==0)?`<span class="ftr ${s.tr>0?'up':'down'}">${s.tr>0?'▲':'▼'}${fmt(Math.abs(s.tr))}/wk</span>`:'';
    return `<div class="fstage"><div class="fhead"><span>${s.label}</span><span class="fval">${fmt(s.val)}${tr}</span></div><div class="fbar"><div class="ffill" style="width:${w}%"></div></div></div>`;
  }).join('');
  const tj=$('trajectory'); if(tj){const up=(t.audience||0)>0||(t.engagement||0)>0;tj.textContent=up?'📈 building':'— warming up';tj.className='traj '+(up?'up':'flat');}
}

function renderGoals(d){
  if(!$('goals')||!d.goals) return;
  $('goalLabel').textContent=d.goals.label;
  $('countdown').textContent=d.goals.days_left+' days left';
  $('goals').innerHTML=d.goals.items.map(g=>{
    const cls=g.on_track?'ok':'behind';
    return `<div class="goal"><div class="gtop"><span class="gname">${g.icon} ${g.label}</span>
      <span class="gnum"><b>${fmt(g.current)}</b> / ${fmt(g.target)}</span></div>
      <div class="track"><div class="fill ${cls}" data-w="${g.pct}"></div></div>
      <div class="gfoot"><span class="gtag ${cls}">${g.on_track?'● On track':'● Behind pace'}</span><span class="gpct">${g.pct}%</span></div></div>`;}).join('');
  setTimeout(()=>document.querySelectorAll('#goals .fill').forEach(f=>f.style.width=f.dataset.w+'%'),120);
  if($('goalRationale')) $('goalRationale').textContent=d.goals.rationale||'';
}

function renderStrategist(d){
  if(!$('coachHead')||!d.strategist||!d.strategist.headline) return;
  const s=d.strategist;
  $('coachHead').textContent=s.headline;
  $('coachUpd').textContent='Updated '+(s.updated||'')+(s.next_review?(' · next review '+s.next_review):'');
  $('coachRead').textContent=s.read||'';
  $('coachNext').textContent=s.next_move||'';
}

function renderAgents(d){
  if(!$('agents')||!d.agents) return;
  const order=['Publishing','Visual formats','Engagement','Funnel','Ops','Other'];
  const byCat={}; d.agents.forEach(a=>{(byCat[a.cat||'Other']=byCat[a.cat||'Other']||[]).push(a)});
  let html='';
  order.forEach(cat=>{ if(!byCat[cat])return;
    html+=`<div class="agcat">${cat} · ${byCat[cat].length}</div>`;
    html+=byCat[cat].map(ag=>`<div class="agent"><div><div class="n">${ag.name}</div><div class="s">${ag.schedule}</div></div><div class="badge"><span class="dot"></span>LIVE</div></div>`).join('');
  });
  $('agents').innerHTML=html;
}

function renderChannels(d){
  if(!$('channels')||!d.channels) return;
  const lab={live:'Live',sandbox:'Sandbox',pending:'Pending',off:'Not connected'};
  $('channels').innerHTML=sortCh(d.channels).map(c=>{
    let right;
    if(c.status==='off') right=lab.off;
    else if(c.status==='pending') right=`Pending — ${c.unit}`;
    else { const extra=c.stat?`${c.stat} · `:((c.followers!=null)?`${c.followers} followers · `:''); right=`${extra}${c.count} ${c.unit} · ${lab[c.status]}`; }
    return `<div class="chan"><div><div class="n"><span class="sdot" style="background:${COL[c.status]||'#9ca3af'}"></span>${EMO[c.name]||''} ${c.name}</div></div><div class="c">${right}</div></div>`;
  }).join('');
}

function renderQueue(d){
  if(!$('pr')||!d.content) return;
  const c=d.content;
  const pTot=(c.posts_published-1+c.posts_remaining)||1, rTot=(c.reels_published+c.reels_remaining)||1;
  $('pr').textContent=c.posts_remaining+' left'; $('rr').textContent=c.reels_remaining+' left';
  setTimeout(()=>{$('prf').style.width=(100*c.posts_remaining/pTot)+'%';$('rrf').style.width=(100*c.reels_remaining/rTot)+'%';},100);
}

function renderAds(d){
  if(!$('ads')||!d.ads) return;
  const a=d.ads, live=(a.status||'').toUpperCase()==='ACTIVE';
  $('ads').innerHTML=`<div class="adrow"><span class="k">Status</span><span class="pill ${live?'':'paused'}">${a.status||'—'}</span></div>
    <div class="adrow"><span class="k">Daily budget</span><span>${a.daily_budget?('$'+a.daily_budget.toFixed(0)+'/day'):'—'}</span></div>
    <div class="adrow"><span class="k">Spent (total)</span><span>$${(parseFloat(a.spend)||0).toFixed(2)}</span></div>
    <div class="adrow"><span class="k">Impressions</span><span>${fmt(a.impressions)}</span></div>
    <div class="adrow"><span class="k">Video views</span><span>${fmt(a.video_views)}</span></div>`;
}

function renderAgenda(d){
  if(!$('agenda')||!d.upcoming) return;
  const mo=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  $('agenda').innerHTML=d.upcoming.length?d.upcoming.map(u=>{const dt=new Date(u.date+'T12:00');
    return `<div class="ag"><div class="date"><div class="d">${dt.getDate()}</div><div class="m">${mo[dt.getMonth()]}</div></div>
      <span class="em">${u.icon}</span><div><div class="t">${u.title}</div><div class="s">${u.sub}</div></div>
      <span class="tag ${u.type}">${u.type==='reel'?'REEL':'POST'}</span></div>`;}).join('')
    :'<p style="color:var(--muted);font-size:13px">Queue empty — refill coming.</p>';
}

function renderActivity(cl){
  if(!$('feed')) return;
  $('feed').innerHTML=(cl.entries||[]).slice(0,30).map(e=>`<div class="ev"><div class="em">${e.icon}</div><div class="body">
    <div class="tx">${e.text}</div><div class="tm">${new Date(e.ts).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})}</div></div></div>`).join('');
}

function renderMafia(d){
  if(!$('mafiaMetrics')||!d.mafia) return;
  const m=d.mafia;
  const g=$('mafiaGrade'); g.textContent=m.overall; g.className='mafia-grade gcolor-'+m.overall;
  $('mafiaSummary').textContent=m.summary;
  $('mafiaMetrics').innerHTML=m.metrics.map(x=>
    `<div class="mcard"><div class="ml">${x.label}</div><div class="mv">${fmt(x.value)}</div><div class="mg gcolor-${x.grade}">${x.grade}</div></div>`).join('');
}

function setMafia(on){
  const mv=$('mafiaView'), nv=$('normalView'); if(!mv||!nv) return;
  mv.style.display=on?'':'none'; nv.style.display=on?'none':'';
  try{ localStorage.setItem('mafia',on?'1':'0'); }catch(e){}
}
function initMafia(){
  const t=$('mafiaToggle'); if(!t) return;
  let on=false; try{ on=localStorage.getItem('mafia')==='1'; }catch(e){}
  if(location.search.indexOf('mafia=1')>=0) on=true;
  t.checked=on; setMafia(on);
  t.addEventListener('change',()=>setMafia(t.checked));
}

async function load(){
  let d,cl;
  try{ d=await (await fetch('data.json?'+Date.now())).json(); }catch(e){ return; }
  try{ cl=await (await fetch('changelog.json?'+Date.now())).json(); }catch(e){ cl={entries:[]}; }
  if($('updated')) $('updated').textContent=new Date(d.updated).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  renderScoreboard(d); renderMafia(d); renderFunnel(d); renderGoals(d); renderStrategist(d);
  renderAgents(d); renderChannels(d); renderQueue(d); renderAds(d); renderAgenda(d); renderActivity(cl);
}
initMafia(); load(); setInterval(load, 60000);
