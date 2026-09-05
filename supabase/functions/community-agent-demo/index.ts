const REPO = "https://github.com/Progaminy/escola-lendaria-community-agent";
const VIDEO = "https://youtu.be/RcocWXhlpHc?si=gKgfsBtqiRPv8GEp";
const FAST_PATH = `${REPO}/blob/main/docs/JUDGE_FAST_PATH.md`;
const VERIFY = `${REPO}/blob/main/docs/VERIFICATION_REPORT.md`;
const SMOKE_TEST = `${REPO}/blob/main/scripts/judge_smoke_test.py`;

const esc = (value: unknown) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function daysSince(value: unknown): number | null {
  if (!value) return null;
  const ms = Date.parse(String(value));
  return Number.isFinite(ms)
    ? Math.max(0, Math.floor((Date.now() - ms) / 86_400_000))
    : null;
}

function unresolvedWrongAttempts(value: unknown): number {
  if (!value || typeof value !== "object") return 0;
  if (Array.isArray(value)) {
    return value.reduce((sum, item) => sum + unresolvedWrongAttempts(item), 0);
  }

  const item = value as Record<string, unknown>;
  const completed =
    item.completed === true ||
    item.isCompleted === true ||
    item.status === "completed";
  const direct = Number(item.wrongAttempts ?? item.wrong_attempts ?? 0);
  let total = !completed && Number.isFinite(direct) && direct > 0 ? direct : 0;

  for (const [key, nested] of Object.entries(item)) {
    if (key === "wrongAttempts" || key === "wrong_attempts") continue;
    total += unresolvedWrongAttempts(nested);
  }
  return total;
}

function responseHeaders(contentType: string): HeadersInit {
  return {
    "Content-Type": contentType,
    "Cache-Control": "no-store, max-age=0",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  };
}

Deno.serve(async (req: Request) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response("Method not allowed", {
      status: 405,
      headers: { ...responseHeaders("text/plain; charset=utf-8"), Allow: "GET, HEAD" },
    });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const secretKeys = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") || "{}");
    const secretKey = secretKeys.default || Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!supabaseUrl || !secretKey) throw new Error("Server-side source key unavailable");

    const source = await fetch(
      `${supabaseUrl}/rest/v1/learning_user_state?select=user_id,last_access_at,updated_at,state&limit=1000`,
      { headers: { apikey: secretKey, Accept: "application/json" } },
    );
    if (!source.ok) throw new Error(`Read-only source request failed (${source.status})`);

    const rows = await source.json() as Array<Record<string, unknown>>;
    const assessed = rows.map((row, index) => {
      const inactivityDays = daysSince(row.last_access_at ?? row.updated_at);
      const state = row.state && typeof row.state === "object"
        ? row.state as Record<string, unknown>
        : {};
      const wrongAttempts = unresolvedWrongAttempts(state.progress ?? {});
      let risk = 0;
      const reasons: string[] = [];

      if (inactivityDays !== null && inactivityDays >= 14) {
        risk = Math.max(risk, 90);
        reasons.push(`${inactivityDays} days inactive`);
      } else if (inactivityDays !== null && inactivityDays >= 7) {
        risk = Math.max(risk, 65);
        reasons.push(`${inactivityDays} days inactive`);
      }

      if (wrongAttempts >= 5) {
        risk = Math.max(risk, 85);
        reasons.push(`${wrongAttempts} unresolved wrong attempts`);
      } else if (wrongAttempts >= 3) {
        risk = Math.max(risk, 70);
        reasons.push(`${wrongAttempts} unresolved wrong attempts`);
      }

      return {
        alias: `Learner ${String(index + 1).padStart(2, "0")}`,
        risk,
        reasons,
        inactivity_days: inactivityDays,
        unresolved_wrong_attempts: wrongAttempts,
        route: risk >= 70 ? "human-review" : risk >= 50 ? "watch" : "none",
      };
    });

    const watch = assessed.filter((x) => x.risk >= 50).sort((a, b) => b.risk - a.risk);
    const human = assessed.filter((x) => x.risk >= 70);
    const high = assessed.filter((x) => x.risk >= 85);
    const repeated = assessed.filter((x) => x.unresolved_wrong_attempts >= 3);
    const inactive = assessed.filter((x) => (x.inactivity_days ?? 0) >= 7);
    const generated = new Date().toISOString();

    const publicSummary = {
      project: "Escola Lendária Community Agent",
      track: "Good Neighbor Agents",
      generated_at: generated,
      source_mode: "live-read-only-privacy-minimized",
      demo_scope: "public read-only verifier; full Strands agent and human queue are in the repository",
      privacy: {
        learner_names_returned: false,
        raw_learner_ids_returned: false,
        contacts_returned: false,
        pins_returned: false,
        chats_or_notes_returned: false,
        payment_data_returned: false,
      },
      safety: {
        consequential_actions: "human-controlled",
        public_endpoint_writes: false,
        source_access: "read-only",
      },
      metrics: {
        learners_scanned: assessed.length,
        watchlist: watch.length,
        human_attention: human.length,
        high_priority: high.length,
        inactivity_signals: inactive.length,
        repeated_failure_signals: repeated.length,
      },
      top_risks: watch.slice(0, 10).map((x) => ({
        alias: x.alias,
        risk: x.risk,
        evidence: x.reasons,
        route: x.route,
      })),
      implementation: {
        full_agent: "Strands Agents SDK + Amazon Bedrock",
        runtime_adapter: "Amazon Bedrock AgentCore",
        deterministic_guardrails: true,
        persistent_monitoring: true,
        constrained_model_tools: true,
        deterministic_attention_plan: true,
        model_identifier_minimization: true,
        repository: REPO,
      },
      judge_verification: {
        fast_path: FAST_PATH,
        verification_report: VERIFY,
        end_to_end_smoke_test: SMOKE_TEST,
        video: VIDEO,
      },
      measurement_scope: "live operational risk evidence; not a causal learning-outcome claim",
    };

    const url = new URL(req.url);
    if (url.searchParams.get("format") === "json") {
      if (req.method === "HEAD") {
        return new Response(null, { status: 200, headers: responseHeaders("application/json; charset=utf-8") });
      }
      return new Response(JSON.stringify(publicSummary, null, 2), {
        status: 200,
        headers: responseHeaders("application/json; charset=utf-8"),
      });
    }

    const rowsHtml = publicSummary.top_risks.map((x) => `
      <tr>
        <td>${esc(x.alias)}</td>
        <td><span class="risk ${x.risk >= 85 ? "r-high" : x.risk >= 70 ? "r-human" : "r-watch"}">${x.risk}</span></td>
        <td>${esc(x.evidence.join(" • ") || "Normal progress")}</td>
        <td>${x.route === "human-review" ? "Human review" : "Watch"}</td>
      </tr>`).join("");

    const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Escola Lendária Community Agent — Live Demo</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#07111f;color:#eef5ff}.wrap{max-width:1180px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;flex-wrap:wrap}header{padding:30px 0 18px}.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#8fb6ff}h1{font-size:clamp(30px,5vw,50px);margin:7px 0 10px;line-height:1.04}.lead{color:#aac0d9;max-width:820px;line-height:1.6}.badge{display:inline-flex;gap:8px;align-items:center;border:1px solid #214468;background:#0b1c30;border-radius:999px;padding:8px 12px;font-size:12px}.dot{width:8px;height:8px;border-radius:50%;background:#42d392;box-shadow:0 0 14px #42d392}.actions{display:flex;gap:8px;flex-wrap:wrap}.btn{display:inline-block;color:#eef5ff;text-decoration:none;border:1px solid #28517a;padding:9px 12px;border-radius:10px;background:#0c1d30;font-size:13px;cursor:pointer}.btn.primary{background:#1769d2;border-color:#4089e8}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:11px;margin:24px 0}.card,.panel{background:linear-gradient(180deg,#0d1c2d,#0a1727);border:1px solid #1b3856;border-radius:16px}.card{padding:17px}.card span{color:#8fa7c1;font-size:11px}.card strong{display:block;font-size:29px;margin-top:7px}.panel{padding:20px;margin:14px 0;overflow:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.proof-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px}.proof{padding:14px;border:1px solid #1a3a58;border-radius:12px;background:#091827}.proof .n{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;background:#183b62;color:#a9ceff;font-weight:700;font-size:12px;margin-bottom:9px}h2{margin:0 0 6px;font-size:20px}h3{margin:0 0 6px;font-size:15px}.muted{color:#8fa7c1;font-size:13px;line-height:1.55}table{width:100%;border-collapse:collapse;margin-top:16px;font-size:13px}th,td{text-align:left;padding:12px 9px;border-bottom:1px solid #17304a;vertical-align:top}.risk{display:inline-block;min-width:42px;text-align:center;padding:5px 8px;border-radius:999px}.r-high{background:#5b2530}.r-human{background:#59451c}.r-watch{background:#193b51}.callout{border-left:3px solid #4b9cff;padding:12px 14px;background:#0a1929;border-radius:0 12px 12px 0}.checks{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:12px}.check{padding:12px;border:1px solid #1a3a58;border-radius:12px;background:#091827}.check b{display:block;font-size:13px;margin-bottom:4px}.ok{color:#65dea7}.architecture{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;font-size:12px;line-height:1.55;color:#b8cbe0;background:#071522;padding:14px;border-radius:12px}footer{padding:22px 0 34px;color:#7089a4;font-size:12px}@media(max-width:980px){.cards{grid-template-columns:repeat(3,1fr)}.proof-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:760px){.grid{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.wrap{padding:16px}.card strong{font-size:25px}.checks,.proof-grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<header><div class="top"><div><div class="eyebrow">Agents for Humans 2026 · Good Neighbor Agents</div><h1>Escola Lendária<br>Community Agent</h1><p class="lead">A proactive school coordination agent that notices silent learner risk before a learner has to ask for help. This public demo executes a live, read-only scan against privacy-minimized learner progress and returns only anonymous risk signals.</p></div><div class="actions"><button class="btn primary" onclick="location.reload()">↻ Run fresh scan</button><a class="btn" href="?format=json" target="_blank">{ } Verify JSON</a><a class="btn" href="${FAST_PATH}" target="_blank" rel="noreferrer">Judge fast path ↗</a></div></div><div class="badge"><span class="dot"></span> Live source · ${esc(generated)}</div></header>
<section class="cards"><div class="card"><span>Learners scanned</span><strong>${publicSummary.metrics.learners_scanned}</strong></div><div class="card"><span>Watchlist</span><strong>${publicSummary.metrics.watchlist}</strong></div><div class="card"><span>Human attention</span><strong>${publicSummary.metrics.human_attention}</strong></div><div class="card"><span>High priority</span><strong>${publicSummary.metrics.high_priority}</strong></div><div class="card"><span>7+ day inactivity</span><strong>${publicSummary.metrics.inactivity_signals}</strong></div><div class="card"><span>Repeated failure</span><strong>${publicSummary.metrics.repeated_failure_signals}</strong></div></section>
<section class="panel"><h2>Silent-risk monitor — live evidence</h2><div class="muted">Temporary aliases only. Raw learner IDs are used server-side solely to read records and are never returned to this public page or JSON verifier.</div><table><thead><tr><th>Learner</th><th>Risk</th><th>Evidence</th><th>Route</th></tr></thead><tbody>${rowsHtml || '<tr><td colspan="4">No active risk detected.</td></tr>'}</tbody></table></section>
<section class="panel"><h2>Judge proof — four things to verify</h2><div class="muted">The public page proves the read-only live source. The repository then makes the full agent claims reproducible instead of asking judges to trust the pitch.</div><div class="proof-grid"><div class="proof"><span class="n">1</span><h3>Live community signal</h3><div class="muted">Refresh the page or inspect JSON to see a fresh privacy-minimized scan.</div></div><div class="proof"><span class="n">2</span><h3>Deterministic priority</h3><div class="muted">The full agent ranks human work outside the LLM from urgency, active risk and waiting time.</div></div><div class="proof"><span class="n">3</span><h3>Human authority</h3><div class="muted">Payment, access, discipline, enrollment, deletion, safeguarding and medical/legal decisions cannot be model-executed.</div></div><div class="proof"><span class="n">4</span><h3>Reproducible evidence</h3><div class="muted">CI runs security, lint, tests and a live-HTTP judge smoke test covering the end-to-end safety path.</div></div></div><div class="actions" style="margin-top:14px"><a class="btn" href="${VERIFY}" target="_blank" rel="noreferrer">Verification report ↗</a><a class="btn" href="${SMOKE_TEST}" target="_blank" rel="noreferrer">Smoke test source ↗</a></div></section>
<div class="grid"><section class="panel"><h2>Safety invariants</h2><div class="checks"><div class="check"><b class="ok">✓ Read-only public demo</b><span class="muted">No write endpoint and no mutation of learner state.</span></div><div class="check"><b class="ok">✓ No learner identity output</b><span class="muted">Names, raw IDs, contacts and PINs are never rendered.</span></div><div class="check"><b class="ok">✓ Consequential actions stay human</b><span class="muted">Payments, access, discipline and safeguarding are not AI-executable tools.</span></div><div class="check"><b class="ok">✓ Deterministic model-note guardrail</b><span class="muted">Model-authored notes are independently validated before persistence.</span></div></div></section><section class="panel"><h2>What the full agent adds</h2><div class="callout"><strong>Strands + Bedrock reasoning after deterministic safety.</strong><br><span class="muted">The repository adds persistent conditions, deduplication, clearing, deterministic attention ranking, human follow-ups, audit trails, privacy-safe community briefing, five constrained Strands tools, Amazon Bedrock reasoning and an AgentCore runtime adapter.</span></div><div class="actions" style="margin-top:14px"><a class="btn" href="${REPO}" target="_blank" rel="noreferrer">Source code ↗</a><a class="btn" href="${VIDEO}" target="_blank" rel="noreferrer">End-to-end video ↗</a></div></section></div>
<section class="panel"><h2>Architecture at a glance</h2><div class="architecture">Real Escola Lendária learner progress
        ↓ read-only / privacy-minimized
Autonomous monitor + persistent state
        ↓
Deterministic guardrail policy + attention ranking
        ↓ safe contextual cases only
Strands Agents SDK + Amazon Bedrock
        ↓ five constrained tools
Human attention queue → human resolution → audit trail
        ↳ Amazon Bedrock AgentCore runtime adapter</div></section>
<section class="panel"><h2>Why this is a Good Neighbor Agent</h2><p class="muted">A request-only chatbot sees the learner who speaks. Community Agent is designed to notice the learner who goes quiet. The beneficiary is the school community as a whole: one agent reduces repetitive monitoring work while surfacing only cases where human judgment is useful.</p><div class="callout"><strong>Measurement boundary:</strong> <span class="muted">this demo shows operational risk evidence and coordination behavior; it does not claim causal improvement in grades, retention or completion.</span></div></section>
<footer>Public judge view · live read-only monitoring · no personal learner information rendered · structured verification available at <b>?format=json</b></footer>
</div></body></html>`;

    if (req.method === "HEAD") {
      return new Response(null, { status: 200, headers: responseHeaders("text/html; charset=utf-8") });
    }
    return new Response(html, { status: 200, headers: responseHeaders("text/html; charset=utf-8") });
  } catch (error) {
    return new Response(
      `Live demo temporarily unavailable: ${error instanceof Error ? error.message : "unknown error"}`,
      { status: 503, headers: responseHeaders("text/plain; charset=utf-8") },
    );
  }
});
