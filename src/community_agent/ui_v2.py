from __future__ import annotations

DASHBOARD_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Escola Lendária Community Agent</title>
  <style>
    :root{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color-scheme:dark;--bg:#07111f;--panel:#0d1c2d;--line:#1b3856;--muted:#91a8c1;--text:#eff6ff;--accent:#8fb6ff;--ok:#59d99d}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text)}.wrap{max-width:1240px;margin:auto;padding:22px}header{padding:22px 0 18px}.eyebrow{color:var(--accent);text-transform:uppercase;letter-spacing:.16em;font-size:11px}h1{font-size:clamp(30px,5vw,48px);line-height:1.05;margin:7px 0 9px}.lead{max-width:850px;color:#b1c5dc;line-height:1.6}.status{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.badge{border:1px solid #28517a;background:#0b1c30;padding:7px 10px;border-radius:999px;font-size:12px}.badge.ok:before{content:'●';color:var(--ok);margin-right:7px}.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:20px 0}.step{padding:12px;border:1px solid var(--line);border-radius:13px;background:#091827;font-size:12px}.step b{display:block;font-size:14px;margin-bottom:4px}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:14px 0}.card,.panel{background:linear-gradient(180deg,#0d1c2d,#0a1727);border:1px solid var(--line);border-radius:16px}.card{padding:16px}.card span{color:var(--muted);font-size:11px}.card strong{display:block;font-size:27px;margin-top:6px}.grid{display:grid;grid-template-columns:1.15fr .85fr;gap:14px;margin-top:14px}.panel{padding:18px;overflow:auto}.wide{grid-column:1/-1}.head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}h2{margin:0 0 5px;font-size:19px}.muted{color:var(--muted);font-size:12px;line-height:1.55}.actions{display:flex;gap:8px;flex-wrap:wrap}.btn,button{border:1px solid #31577e;background:#10243a;color:var(--text);padding:9px 12px;border-radius:10px;cursor:pointer;font-weight:650}.btn.primary,button.primary{background:#e8f0ff;color:#0b1320;border-color:#e8f0ff}button:disabled{opacity:.55;cursor:wait}table{width:100%;border-collapse:collapse;margin-top:12px;font-size:12px}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #17304a;vertical-align:top}th{color:#a8bdd3;font-size:11px;text-transform:uppercase;letter-spacing:.05em}.score{display:inline-block;min-width:44px;text-align:center;padding:4px 7px;border-radius:999px;background:#193b51}.high{background:#5c2933}.medium{background:#5c491e}.rank{font-size:18px;font-weight:800}.pill{display:inline-block;padding:3px 7px;border-radius:999px;background:#17304a;font-size:10px;text-transform:uppercase}.evidence{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:13px}.metric{border:1px solid #1a3a58;background:#091827;border-radius:12px;padding:12px}.metric strong{display:block;font-size:22px;margin-top:5px}pre{white-space:pre-wrap;overflow:auto;background:#071522;border:1px solid #17304a;border-radius:12px;padding:12px;min-height:120px;font-size:11px;line-height:1.5}.scenario{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}select,textarea{width:100%;background:#081523;color:var(--text);border:1px solid #28435f;border-radius:9px;padding:9px}textarea{grid-column:1/-1;min-height:72px;resize:vertical}.scenario button{grid-column:1/-1}.safe{border-left:3px solid #4b9cff;background:#081726;padding:11px 13px;border-radius:0 11px 11px 0;margin-top:12px}.footer{color:#667f98;font-size:11px;padding:22px 0}@media(max-width:1000px){.cards{grid-template-columns:repeat(3,1fr)}.flow{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.wide{grid-column:auto}.evidence{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.wrap{padding:15px}.cards{grid-template-columns:1fr 1fr}.scenario{grid-template-columns:1fr}.scenario textarea,.scenario button{grid-column:auto}.flow{grid-template-columns:1fr}}
  </style>
</head>
<body><main class="wrap">
<header>
  <div class="eyebrow">Agents for Humans 2026 · Good Neighbor Agents</div>
  <h1>Escola Lendária<br>Community Agent</h1>
  <p class="lead">One operational loop for a small school: detect silent learner risk in the background, rank limited human attention with deterministic evidence, let Strands + Amazon Bedrock explain the situation, and keep consequential decisions human-controlled.</p>
  <div class="status"><span class="badge ok">Autonomous monitor</span><span class="badge ok">Strands Agents SDK</span><span class="badge">Deterministic guardrails</span><span class="badge">Read-only real source</span><span class="badge">Human-in-the-loop</span></div>
</header>

<section class="flow">
  <div class="step"><b>1 · Observe</b>Privacy-minimized learner activity</div>
  <div class="step"><b>2 · Detect</b>Autonomous silent-risk scan</div>
  <div class="step"><b>3 · Prioritize</b>Explainable human attention plan</div>
  <div class="step"><b>4 · Decide</b>Strands briefing + human judgment</div>
  <div class="step"><b>5 · Learn</b>Audit + operational evidence</div>
</section>

<section class="cards">
  <div class="card"><span>Learners</span><strong id="learners">—</strong></div>
  <div class="card"><span>Active risks</span><strong id="risks">—</strong></div>
  <div class="card"><span>Open human work</span><strong id="followups">—</strong></div>
  <div class="card"><span>High priority</span><strong id="high">—</strong></div>
  <div class="card"><span>Scans performed</span><strong id="scans">—</strong></div>
  <div class="card"><span>Duplicates suppressed</span><strong id="suppressed">—</strong></div>
</section>

<section class="grid">
  <div class="panel wide">
    <div class="head"><div><h2>1–3 · Autonomous monitor → human attention plan</h2><div class="muted">Priority scores are deterministic: urgency + active monitoring risk + waiting time. Strands can explain the order but cannot change it.</div></div><div class="actions"><button id="syncBtn">Sync real source</button><button id="scanBtn" class="primary">Run fresh community scan</button><button id="refreshBtn">Refresh</button></div></div>
    <table><thead><tr><th>Rank</th><th>Learner</th><th>Priority</th><th>Urgency</th><th>Why now</th><th>Owner</th><th>Human action</th></tr></thead><tbody id="attentionRows"></tbody></table>
  </div>

  <div class="panel">
    <div class="head"><div><h2>4 · Strands community briefing</h2><div class="muted">Uses privacy-safe community context, the fixed attention plan, and operational evidence.</div></div><button id="briefBtn" class="primary">Generate briefing</button></div>
    <pre id="briefing">Press “Generate briefing”. In policy mode the deterministic evidence still works without AWS.</pre>
    <div class="safe"><b>Authority boundary:</b><div class="muted">Payments, access, discipline, enrollment, deletion, medical/legal and safeguarding decisions are not AI-executable tools.</div></div>
  </div>

  <div class="panel">
    <h2>Event-driven scenario</h2><div class="muted">Use one learner from the current work queue to demonstrate the same safety boundary on an incoming event.</div>
    <div class="scenario"><select id="learnerSelect"></select><select id="eventType"><option value="repeated_failure">repeated_failure</option><option value="payment_confirmation">payment_confirmation</option><option value="question">question</option><option value="lesson_completed">lesson_completed</option><option value="bullying">bullying</option></select><textarea id="details">Learner failed the same exercise three times and needs coordinated support.</textarea><button id="eventBtn">Let the agent handle this event</button></div>
    <pre id="eventResult">Waiting for a scenario…</pre>
  </div>

  <div class="panel wide">
    <div class="head"><div><h2>5 · Operational evidence</h2><div class="muted">Observed agent behavior only — these numbers are not presented as causal proof of improved learning outcomes.</div></div></div>
    <div class="evidence"><div class="metric"><span class="muted">Condition observations</span><strong id="observations">—</strong></div><div class="metric"><span class="muted">New alerts</span><strong id="newAlerts">—</strong></div><div class="metric"><span class="muted">Conditions cleared</span><strong id="cleared">—</strong></div><div class="metric"><span class="muted">Human resolutions</span><strong id="resolutions">—</strong></div></div>
  </div>

  <div class="panel wide"><h2>Audit trail</h2><div class="muted">Every monitor run, policy decision, support note, escalation and human resolution is recorded.</div><table><thead><tr><th>Time</th><th>Learner</th><th>Action</th><th>Summary</th></tr></thead><tbody id="auditRows"></tbody></table></div>
</section>
<div class="footer">Judge-focused dashboard · privacy-minimized aliases · deterministic safety before model reasoning · Strands + Amazon Bedrock for bounded contextual reasoning</div>
</main>
<script>
const aliases=new Map();
function alias(id){if(!id)return '—';if(!aliases.has(id))aliases.set(id,`Learner ${String(aliases.size+1).padStart(2,'0')}`);return aliases.get(id)}
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
async function j(url,opt){const r=await fetch(url,opt);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Request failed');return d}
function setBusy(button,busy){button.disabled=busy}
async function refresh(){
  const [stats,monitor,plan,impact,audit]=await Promise.all([j('/stats'),j('/monitor/state'),j('/attention-plan'),j('/impact'),j('/audit?limit=24')]);
  learners.textContent=stats.learners;risks.textContent=stats.monitored_risks;followups.textContent=stats.open_followups;high.textContent=stats.high_priority;scans.textContent=impact.monitoring_runs;suppressed.textContent=impact.continuing_conditions_without_duplicate_alert;
  observations.textContent=impact.active_condition_observations;newAlerts.textContent=impact.new_alerts_created;cleared.textContent=impact.conditions_cleared;resolutions.textContent=impact.human_resolutions_recorded;
  attentionRows.innerHTML='';
  for(const x of plan.items){const tr=document.createElement('tr');tr.innerHTML=`<td class="rank">${esc(x.rank)}</td><td>${esc(alias(x.learner_id))}</td><td><span class="score ${x.priority_score>=120?'high':x.priority_score>=85?'medium':''}">${esc(x.priority_score)}</span></td><td><span class="pill">${esc(x.urgency)}</span></td><td>${esc(x.why_now)}<div class="muted">${esc(x.reason)}</div></td><td>${esc(x.owner_role)}</td><td><button onclick="resolveFollowup(${Number(x.id)})">Resolve</button></td>`;attentionRows.appendChild(tr)}
  if(!plan.items.length)attentionRows.innerHTML='<tr><td colspan="7" class="muted">No open human follow-up. Run the monitor or send a scenario.</td></tr>';
  const ids=[...new Set([...plan.items.map(x=>x.learner_id),...monitor.items.map(x=>x.learner_id)].filter(Boolean))];learnerSelect.innerHTML='';for(const id of ids){const o=document.createElement('option');o.value=id;o.textContent=alias(id);learnerSelect.appendChild(o)}if(!ids.length){const o=document.createElement('option');o.value='';o.textContent='No learner in current queue';learnerSelect.appendChild(o)}
  auditRows.innerHTML='';for(const x of audit.items){const tr=document.createElement('tr');tr.innerHTML=`<td>${esc(x.created_at)}</td><td>${esc(alias(x.learner_id))}</td><td>${esc(x.action_type)}</td><td>${esc(x.summary)}</td>`;auditRows.appendChild(tr)}
}
async function resolveFollowup(id){const note=prompt('Human resolution note:');if(!note)return;await j(`/followups/${id}/resolve`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resolution_note:note})});await refresh()}
scanBtn.onclick=async()=>{setBusy(scanBtn,true);try{await j('/monitor/run',{method:'POST'});await refresh()}catch(e){alert(e.message)}finally{setBusy(scanBtn,false)}};
syncBtn.onclick=async()=>{setBusy(syncBtn,true);try{await j('/source/supabase/sync',{method:'POST'});await refresh()}catch(e){alert(e.message)}finally{setBusy(syncBtn,false)}};
refreshBtn.onclick=refresh;
briefBtn.onclick=async()=>{setBusy(briefBtn,true);briefing.textContent='Building privacy-safe community briefing…';try{briefing.textContent=JSON.stringify(await j('/agent/community-briefing',{method:'POST'}),null,2)}catch(e){briefing.textContent='ERROR: '+e.message}finally{setBusy(briefBtn,false)}};
eventBtn.onclick=async()=>{if(!learnerSelect.value){eventResult.textContent='Run a scan first so a learner is available.';return}setBusy(eventBtn,true);try{const body={event_id:`judge-${Date.now()}`,learner_id:learnerSelect.value,event_type:eventType.value,details:details.value,severity_hint:eventType.value==='bullying'?'high':'medium',source:'judge-dashboard'};eventResult.textContent=JSON.stringify(await j('/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),null,2);await refresh()}catch(e){eventResult.textContent='ERROR: '+e.message}finally{setBusy(eventBtn,false)}};
refresh().catch(e=>{console.error(e);attentionRows.innerHTML=`<tr><td colspan="7">${esc(e.message)}</td></tr>`});
</script></body></html>
"""
