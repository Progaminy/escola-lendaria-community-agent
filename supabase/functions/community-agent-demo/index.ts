// Privacy-safe public live preview for the Agents for Humans submission.
// This function is read-only. It never returns names, contacts, PINs, chats,
// payment information, raw learner IDs, or other private learner data.

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

Deno.serve(async (req: Request) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response("Method not allowed", {
      status: 405,
      headers: { Allow: "GET, HEAD" },
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
      };
    });

    const watch = assessed.filter((x) => x.risk >= 50).sort((a, b) => b.risk - a.risk);
    const human = assessed.filter((x) => x.risk >= 70);
    const high = assessed.filter((x) => x.risk >= 85);
    const rowsHtml = watch.slice(0, 10).map((x) => `
      <tr><td>${x.alias}</td><td>${x.risk}</td><td>${x.reasons.join(" • ")}</td><td>${x.risk >= 70 ? "Human review" : "Watch"}</td></tr>
    `).join("");

    const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Escola Lendária Community Agent — Live Demo</title><style>body{font-family:system-ui;margin:0;background:#07111f;color:#eef5ff}.w{max-width:1080px;margin:auto;padding:24px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.c,.p{background:#0d1c2d;border:1px solid #1b3856;border-radius:16px;padding:18px}.c strong{display:block;font-size:30px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:11px;border-bottom:1px solid #17304a}.muted{color:#9bb0c7}@media(max-width:720px){.cards{grid-template-columns:1fr 1fr}}</style></head><body><main class="w"><p class="muted">Agents for Humans 2026 · Good Neighbor Agents</p><h1>Escola Lendária Community Agent</h1><p class="muted">Live, read-only, privacy-minimized monitoring preview. The full Strands/Bedrock agent, persistent monitor, safety boundary and audit trail are in the public repository and demo video.</p><section class="cards"><div class="c">Learners scanned<strong>${assessed.length}</strong></div><div class="c">Watchlist<strong>${watch.length}</strong></div><div class="c">Human attention<strong>${human.length}</strong></div><div class="c">High priority<strong>${high.length}</strong></div></section><section class="p" style="margin-top:14px"><h2>Silent-risk monitor</h2><p class="muted">Temporary aliases only. No raw learner identifiers are returned.</p><table><thead><tr><th>Learner</th><th>Risk</th><th>Evidence</th><th>Route</th></tr></thead><tbody>${rowsHtml || '<tr><td colspan="4">No active risk detected.</td></tr>'}</tbody></table></section><section class="p" style="margin-top:14px"><strong>Good Neighbor principle:</strong><p class="muted">A request-only chatbot sees the learner who speaks. Community Agent is designed to notice the learner who goes quiet, while keeping consequential decisions human-controlled.</p><p><a style="color:#9ec5ff" href="https://github.com/Progaminy/escola-lendaria-community-agent">Source code</a> · <a style="color:#9ec5ff" href="https://youtu.be/RcocWXhlpHc?si=gKgfsBtqiRPv8GEp">Demo video</a></p></section></main></body></html>`;

    return req.method === "HEAD"
      ? new Response(null, { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } })
      : new Response(html, {
          status: 200,
          headers: {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
          },
        });
  } catch (error) {
    return new Response(
      `Live demo temporarily unavailable: ${error instanceof Error ? error.message : "unknown error"}`,
      { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } },
    );
  }
});
