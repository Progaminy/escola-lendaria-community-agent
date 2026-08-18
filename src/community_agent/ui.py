from __future__ import annotations

DASHBOARD_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Escola Lendária Community Agent</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, sans-serif; }
    body { margin:0; background:#0b1020; color:#ecf1ff; }
    header { padding:26px 30px 16px; border-bottom:1px solid #222b46; }
    h1 { margin:0 0 6px; font-size:24px; }
    h2 { margin-top:0; }
    .muted { color:#9ca9c9; }
    main { max-width:1240px; margin:auto; padding:24px; }
    .cards { display:grid; grid-template-columns:repeat(8,1fr); gap:12px; }
    .card,.panel { background:#121a2d; border:1px solid #24304f; border-radius:14px; }
    .card { padding:16px; }
    .card strong { display:block; font-size:26px; margin-top:6px; }
    .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }
    .panel { padding:18px; overflow:auto; }
    label { display:block; margin:10px 0 5px; color:#b7c2df; font-size:13px; }
    input,select,textarea,button { width:100%; box-sizing:border-box; border-radius:9px; border:1px solid #31405f; background:#0d1425; color:#edf2ff; padding:10px; }
    textarea { min-height:92px; resize:vertical; }
    button { background:#e6ebff; color:#11182a; font-weight:700; cursor:pointer; margin-top:12px; }
    button.secondary { background:#1e2944; color:#edf2ff; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    .panel { overflow-x:auto; }
    #followupRows button { width:auto; min-width:68px; padding:7px 9px; margin:0; white-space:nowrap; }
    .human-queue table { table-layout:fixed; }
    .human-queue th:nth-child(1){width:17%}
    .human-queue th:nth-child(2){width:39%}
    .human-queue th:nth-child(3){width:14%}
    .human-queue th:nth-child(4){width:16%}
    .human-queue th:nth-child(5){width:14%}
    .human-queue td { overflow-wrap:anywhere; }
    th,td { text-align:left; padding:10px 7px; border-bottom:1px solid #26314c; vertical-align:top; }
    .pill { display:inline-block; padding:3px 8px; border-radius:99px; background:#263455; font-size:11px; text-transform:uppercase; }
    .risk-high { font-weight:800; }
    pre { white-space:pre-wrap; background:#0c1324; padding:12px; border-radius:10px; min-height:130px; overflow:auto; }
    .wide { grid-column:1/-1; }
    @media (max-width:980px){ .cards{grid-template-columns:repeat(3,1fr)} }
    @media (max-width:800px){ .cards{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr} }
  </style>
</head>
<body>
<header>
  <h1>Escola Lendária Community Agent</h1>
  <div class="muted">Good Neighbor coordination layer • Strands Agents SDK • deterministic guardrails • human-in-the-loop</div>
</header>
<main>
  <section class="cards">
    <div class="card"><span class="muted">Learners</span><strong id="learners">—</strong></div>
    <div class="card"><span class="muted">Watchlist</span><strong id="watchlist">—</strong></div>
    <div class="card"><span class="muted">Human attention</span><strong id="humanLearners">—</strong></div>
    <div class="card"><span class="muted">Open follow-ups</span><strong id="openFollowups">—</strong></div>
    <div class="card"><span class="muted">High priority</span><strong id="highPriority">—</strong></div>
    <div class="card"><span class="muted">Real-source learners</span><strong id="sourceLearners">—</strong></div>
  </section>

  <section class="grid">
    <div class="panel">
      <h2>Send a school event</h2>
      <form id="eventForm">
        <label>Learner</label>
        <select id="learnerId" required>
          <option value="">Loading privacy-safe learner list…</option>
        </select>
        <label>Event type</label>
        <select id="eventType">
          <option>repeated_failure</option><option>question</option><option>inactivity</option><option>lesson_completed</option><option>payment_confirmation</option><option>bullying</option>
        </select>
        <label>Details</label>
        <textarea id="details">Learner failed the same exercise three times and needs coordinated support.</textarea>
        <label>Severity hint</label>
        <select id="severity"><option value="medium">medium</option><option value="low">low</option><option value="high">high</option></select>
        <button type="submit">Let the agent handle it</button>
      </form>
      <h3>Decision</h3><pre id="agentResult">Waiting for an event…</pre>
    </div>

    <div class="panel human-queue">
      <h2>Human attention queue</h2>
      <div class="muted">Consequential and high-risk cases are routed here instead of being executed autonomously.</div>
      <table><thead><tr><th>Learner</th><th>Active risks</th><th>Urgency</th><th>Owner</th><th>Action</th></tr></thead><tbody id="followupRows"></tbody></table>
    </div>



    <div class="panel wide">
      <div style="display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <div>
          <h2 style="margin-bottom:4px">Escola Lendária data source</h2>
          <div class="muted">Privacy-minimized Supabase sync: progress and activity only. Contacts, PINs, chats and private notes are excluded.</div>
        </div>
        <button id="syncSource" class="secondary" style="width:auto;min-width:220px;margin:0">Sync real learner state</button>
      </div>
      <pre id="sourceResult" style="min-height:70px">Checking source status…</pre>
    </div>

    <div class="panel wide">
      <div style="display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <div>
          <h2 style="margin-bottom:4px">Autonomous community monitor</h2>
          <div class="muted">Finds learners falling behind even when they never ask the agent for help.</div>
        </div>
        <button id="runMonitor" style="width:auto;min-width:220px;margin:0">Run autonomous scan now</button>
      </div>
      <pre id="monitorResult" style="min-height:70px">Waiting for the background monitor…</pre>
      <table><thead><tr><th>Learner</th><th>Course</th><th>Condition</th><th>Risk</th><th>Evidence</th><th>Owner</th></tr></thead><tbody id="monitorRows"></tbody></table>
    </div>

    <div class="panel wide">
      <h2>Recent agent decisions</h2>
      <table><thead><tr><th>Time</th><th>Learner</th><th>Status</th><th>Risk</th><th>Human?</th><th>Reason</th></tr></thead><tbody id="decisionRows"></tbody></table>
    </div>

    <div class="panel wide">
      <h2>Audit trail</h2>
      <table><thead><tr><th>Time</th><th>Learner</th><th>Action</th><th>Summary</th></tr></thead><tbody id="auditRows"></tbody></table>
    </div>
  </section>
</main>
<script>
async function json(url, options){ const r=await fetch(url, options); const data=await r.json(); if(!r.ok) throw new Error(data.detail || 'Request failed'); return data; }
function esc(x){ return String(x ?? '').replace(/[&<>"']/g, m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m])); }
const learnerAliases = new Map();
function learnerAlias(id){
  if(!id) return '—';
  if(!learnerAliases.has(id)){
    learnerAliases.set(
      id,
      `Learner ${String(learnerAliases.size + 1).padStart(2,'0')}`
    );
  }
  return learnerAliases.get(id);
}

async function refresh(){
  const [stats, source, m, f, d, a] = await Promise.all([
    json('/stats'),
    json('/source/status'),
    json('/monitor/state'),
    json('/followups'),
    json('/decisions?limit=20'),
    json('/audit?limit=30')
  ]);

  learners.textContent = stats.learners;
  openFollowups.textContent = stats.open_followups;
  highPriority.textContent = stats.high_priority;
  sourceLearners.textContent = source.local_synced_learners;

  const watchItems = m.items.filter(x => x.followup_id == null);
  const humanItems = m.items.filter(x => x.followup_id != null);
  const distinctHumanLearners = new Set(humanItems.map(x => x.learner_id));

  watchlist.textContent = watchItems.length;
  humanLearners.textContent = distinctHumanLearners.size;

  sourceResult.textContent = JSON.stringify(source,null,2);

  const currentLearner = learnerId.value;
  const learnerIds = [...new Set([
    ...m.items.map(x => x.learner_id),
    ...f.items.map(x => x.learner_id)
  ].filter(Boolean))];

  learnerId.innerHTML = '<option value="">Choose a learner…</option>';
  for(const id of learnerIds){
    const option = document.createElement('option');
    option.value = id;
    option.textContent = learnerAlias(id);
    learnerId.appendChild(option);
  }
  if(currentLearner && learnerIds.includes(currentLearner)){
    learnerId.value = currentLearner;
  } else if(learnerIds.length){
    learnerId.value = learnerIds[0];
  }

  monitorRows.innerHTML='';
  for(const x of m.items){
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${esc(learnerAlias(x.learner_id))}</td>
      <td>${esc(x.course||'—')}</td>
      <td>${esc(x.rule_key)}</td>
      <td class="${x.risk_score>=70?'risk-high':''}">${esc(x.risk_score)}</td>
      <td>${esc(x.evidence)}</td>
      <td>${esc(x.owner_role)}</td>`;
    monitorRows.appendChild(tr);
  }
  if(!m.items.length){
    monitorRows.innerHTML='<tr><td colspan="6" class="muted">No active monitoring condition.</td></tr>';
  }

  followupRows.innerHTML='';

  const urgencyRank = {low:1, medium:2, high:3};
  const groupedFollowups = new Map();

  for(const x of f.items){
    if(!groupedFollowups.has(x.learner_id)){
      groupedFollowups.set(x.learner_id,{
        learner_id:x.learner_id,
        urgency:x.urgency,
        items:[]
      });
    }

    const group=groupedFollowups.get(x.learner_id);
    group.items.push(x);

    if((urgencyRank[x.urgency]||0) > (urgencyRank[group.urgency]||0)){
      group.urgency=x.urgency;
    }
  }

  for(const group of groupedFollowups.values()){
    const reasons=group.items.map(x=>x.reason).join(' • ');
    const owners=[...new Set(group.items.map(x=>x.owner_role))].join(', ');
    const ids=group.items.map(x=>x.id).join(',');

    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${esc(learnerAlias(group.learner_id))}</td>
      <td>
        ${esc(reasons)}
        ${group.items.length>1
          ? `<div class="muted">${group.items.length} active risks</div>`
          : ''}
      </td>
      <td><span class="pill">${esc(group.urgency)}</span></td>
      <td>${esc(owners)}</td>
      <td>
        <button class="secondary"
          onclick="resolveLearnerFollowups([${ids}])">
          Resolve
        </button>
      </td>`;

    followupRows.appendChild(tr);
  }

  if(!groupedFollowups.size){
    followupRows.innerHTML='<tr><td colspan="5" class="muted">No human intervention needed.</td></tr>';
  }

  decisionRows.innerHTML='';
  for(const x of d.items){
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${esc(x.created_at)}</td>
      <td>${esc(learnerAlias(x.learner_id))}</td>
      <td>${esc(x.status)}</td>
      <td class="${x.risk_score>=70?'risk-high':''}">${esc(x.risk_score)}</td>
      <td>${x.human_action_needed?'YES':'no'}</td>
      <td>${esc(x.reason)}</td>`;
    decisionRows.appendChild(tr);
  }

  auditRows.innerHTML='';
  for(const x of a.items){
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${esc(x.created_at)}</td>
      <td>${esc(learnerAlias(x.learner_id))}</td>
      <td>${esc(x.action_type)}</td>
      <td>${esc(x.summary)}</td>`;
    auditRows.appendChild(tr);
  }
}
async function resolveItem(id){
  const note=prompt('Human resolution note:');
  if(!note) return;
  await json(`/followups/${id}/resolve`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({resolution_note:note})
  });
  await refresh();
}

async function resolveLearnerFollowups(ids){
  const note=prompt(
    `Resolution note for ${ids.length} active risk${ids.length>1?'s':''}:`
  );
  if(!note) return;

  for(const id of ids){
    await json(`/followups/${id}/resolve`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({resolution_note:note})
    });
  }

  await refresh();
}
syncSource.addEventListener('click', async ()=>{ syncSource.disabled=true; sourceResult.textContent='Synchronizing privacy-minimized learner state…'; try { const result=await json('/source/supabase/sync',{method:'POST'}); sourceResult.textContent=JSON.stringify(result,null,2); await refresh(); } catch(err){ sourceResult.textContent='ERROR: '+err.message; } finally { syncSource.disabled=false; } });
runMonitor.addEventListener('click', async ()=>{ runMonitor.disabled=true; monitorResult.textContent='Scanning the whole learner community…'; try { const result=await json('/monitor/run',{method:'POST'}); monitorResult.textContent=JSON.stringify(result,null,2); await refresh(); } catch(err){ monitorResult.textContent='ERROR: '+err.message; } finally { runMonitor.disabled=false; } });
eventForm.addEventListener('submit', async e=>{ e.preventDefault(); agentResult.textContent='Agent is processing…'; try { const result=await json('/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({learner_id:learnerId.value,event_type:eventType.value,details:details.value,severity_hint:severity.value,source:'demo-dashboard'})}); agentResult.textContent=JSON.stringify(result.result,null,2); await refresh(); } catch(err){ agentResult.textContent='ERROR: '+err.message; } });
refresh(); setInterval(refresh, 10000);
</script>
</body>
</html>
"""
