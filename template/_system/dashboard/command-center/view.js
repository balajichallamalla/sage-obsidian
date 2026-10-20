// Command center for home.md — rendered by: await dv.view("_system/dashboard/command-center")
// Spec: _system/specs/2026-10-19-command-center-dashboard-design.md
const STALE_H = 12;
const m = window.moment;
const today = m().format("YYYY-MM-DD");
// Dataview can re-run this view while an earlier run is still awaiting data. Each run clears the
// container and claims it; an older run that resumes later sees it no longer owns it and stops.
const host = dv.container;
const runId = (host.__ccRun = (host.__ccRun || 0) + 1);
const isCurrent = () => host.__ccRun === runId;
host.querySelectorAll(":scope > .cc").forEach(e => e.remove()); // keep Dataview's injected view.css <style>
const root = host.createDiv({ cls: "cc" });

const COMMANDS = [
  ["/dash", "Refresh Slack, PRs, hours, calendar"],
  ["/prep", "Brief for a meeting or person"],
  ["/weekly", "This week's page + impact log"],
  ["/sync", "Pull all connectors"],
  ["/todo-sync", "Two-way Todoist sync"],
  ["/daily", "Refresh today's journal"],
  ["/ask", "Answer from the vault"],
  ["/search", "Ranked page search"],
  ["/ingest", "File notes or a link"],
  ["/inbox", "Triage inbox.md"],
  ["/lint", "Vault health check"],
  ["/sync-status", "Cursors and digests"],
];
const BOARD = [
  ["Triage", s => /triage|backlog/.test(s)],
  ["Accepted", s => /accepted|to do|todo|selected/.test(s)],
  ["In progress", s => /in progress/.test(s)],
  ["Review", s => /review|qa/.test(s)],
  ["Blocked", s => /blocked/.test(s)],
];

// ---------- helpers ----------
const load = async p => { try { return await dv.io.load(p); } catch (e) { return undefined; } };
const loadJson = async p => { const t = await load(p); try { return t ? JSON.parse(t) : null; } catch (e) { return null; } };
const el = (parent, tag, cls, text) => { const x = parent.createEl(tag, { cls }); if (text !== undefined) x.setText(String(text)); return x; };
const link = (parent, target, text, cls) => {
  const a = parent.createEl("a", { cls: "internal-link " + (cls || ""), text: text || target });
  a.setAttr("data-href", target); a.setAttr("href", target);
  a.addEventListener("click", e => { e.preventDefault(); app.workspace.openLinkText(target, "", e.metaKey || e.ctrlKey); });
  return a;
};
const ext = (parent, url, text, cls) => { const a = parent.createEl("a", { cls: "external-link " + (cls || ""), text, href: url }); a.setAttr("target", "_blank"); return a; };
const card = (parent, title, icon, cls) => {
  const c = el(parent, "div", "cc-card " + (cls || ""));
  const h = el(c, "div", "cc-card-title"); el(h, "span", "cc-ico", icon); el(h, "span", "", title);
  return c;
};
const ageText = iso => { if (!iso) return "never"; const h = m().diff(m(iso), "hours", true); return h < 1 ? `${Math.max(1, Math.round(h * 60))}m ago` : h < 48 ? `${Math.round(h)}h ago` : `${Math.round(h / 24)}d ago`; };
const isStale = s => !s || !s.ok || !s.data_at || m().diff(m(s.data_at), "hours", true) > STALE_H;
const staleNote = (parent, s) => { if (!s) el(parent, "div", "cc-empty", "Run /dash to fill this."); else if (isStale(s)) el(parent, "div", "cc-stale", `Stale since ${s.data_at ? m(s.data_at).format("ddd HH:mm") : "never"}${s.note ? " — " + s.note : ""}`); };
const section = (body, heading) => { if (!body) return ""; const r = new RegExp(`^## ${heading}\\s*$([\\s\\S]*?)(?=^## |$(?![\\s\\S]))`, "m"); const x = body.match(r); return x ? x[1] : ""; };
const lower = v => String(v ?? "").toLowerCase();
const slugOf = v => { const x = String(v ?? "").match(/\[\[([^\]|#]+)/); return x ? x[1].split("/").pop() : String(v ?? ""); };
const isMine = v => ME.some(m => lower(v).includes(m));
const safe = async (name, fn) => { if (!isCurrent()) { root.remove(); return; } try { await fn(); } catch (e) { el(root, "div", "cc-error", `${name} failed: ${e.message}`); console.error(e); } };

// ---------- data ----------
const cfg = (await loadJson("_system/config.json")) || {};
const ME = ((cfg.owner && cfg.owner.match) || [(cfg.owner && cfg.owner.first_name) || ""]).map(s => String(s).toLowerCase()).filter(Boolean);
const FIRST = (cfg.owner && cfg.owner.first_name) || "there";
const snap = (await loadJson("_system/state/dashboard.json")) || { sources: {}, calendar: [], slack: [], prs: [], jira_hours: {} };
const syncState = (await loadJson("_system/state/sync-state.json")) || { sources: {} };
const journalPath = `journal/${today}.md`;
const journal = await load(journalPath);
const tickets = dv.pages('"wiki/tickets"').where(p => isMine(p.assignee)).array();
const openTickets = tickets.filter(t => !/^(closed|done)/.test(lower(t.status)));
const inboxPage = dv.page("inbox");
const todoTasks = dv.pages('"wiki" or "journal"').file.tasks.array().concat(inboxPage ? inboxPage.file.tasks.array() : [])
  .filter(t => t.text.includes("#todo/") && !t.completed && t.status === " ");
const dueOf = t => (t.due ? m(t.due.toISODate ? t.due.toISODate() : String(t.due)).format("YYYY-MM-DD") : null);
const dueNow = todoTasks.filter(t => dueOf(t) && dueOf(t) <= today);
const overdue = dueNow.filter(t => dueOf(t) < today);
const in7 = m().add(7, "days").format("YYYY-MM-DD");
const soon = todoTasks.filter(t => dueOf(t) && dueOf(t) > today && dueOf(t) <= in7);
const pendingDigests = dv.pages('"_system/state/digests"').where(p => p.status === "pending").array();

const calFresh = snap.sources.calendar && snap.sources.calendar.data_at && m(snap.sources.calendar.data_at).format("YYYY-MM-DD") === today;
const prepBlocks = {};
section(journal, "Meeting prep").split(/^### /m).slice(1).forEach(b => {
  const [head, ...rest] = b.split("\n"); const owe = rest.find(l => l.startsWith("- I owe:"));
  prepBlocks[head.trim()] = owe ? owe.replace("- I owe:", "").replace(/\[\[([^\]|]+\|)?([^\]]+)\]\]/g, "$2").trim() : "";
});
const meetings = calFresh ? snap.calendar.filter(e => !e.declined)
  : Object.keys(prepBlocks).map(h => ({ start: h.slice(0, 5), title: h.slice(6), attendees: 0, large: false }));
const nowHM = m().format("HH:mm");
const nextMeeting = meetings.find(e => (e.end || e.start) >= nowHM);

// ---------- header ----------
await safe("Header", async () => {
  const h = el(root, "div", "cc-header");
  const left = el(h, "div");
  const hr = m().hour();
  el(left, "div", "cc-hello", `Good ${hr < 12 ? "morning" : hr < 17 ? "afternoon" : "evening"}, ${FIRST}`);
  const counts = {}; openTickets.forEach(t => { if (t.sprint) counts[t.sprint] = (counts[t.sprint] || 0) + 1; });
  const sprint = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  el(left, "div", "cc-sub", `${m().format("dddd, MMM D")} · Week ${m().isoWeek()}${sprint ? " · Sprint " + sprint[0] : ""}`);
  const chips = el(h, "div", "cc-chips");
  const chip = (label, cls, title) => { const c = el(chips, "span", "cc-chip " + cls, label); if (title) c.setAttr("title", title); };
  for (const [name, s] of Object.entries(syncState.sources || {})) {
    const lr = s.last_run || {}; if (!lr.at) continue;
    const bad = lr.status === "error"; const old = m().diff(m(lr.at), "hours", true) > STALE_H;
    chip(`${name} ${m(lr.at).format("HH:mm")}`, bad ? "is-red" : old ? "is-amber" : "is-green", lr.note || "");
  }
  const ds = snap.sources || {};
  if (snap.generated_at) chip(`dash ${m(snap.generated_at).format("HH:mm")}`, Object.values(ds).some(s => !s.ok) ? "is-amber" : "is-green");
  if (pendingDigests.length) chip(`${pendingDigests.length} digest waiting`, "is-amber");
});

// ---------- tiles ----------
await safe("Tiles", async () => {
  const g = el(root, "div", "cc-tiles");
  const tile = (label, value, sub, cls, anchor) => {
    const t = el(g, "div", "cc-tile " + (cls || "")); el(t, "div", "cc-tile-label", label);
    const v = el(t, "div", "cc-tile-value"); v.innerHTML = value; if (sub) el(t, "div", "cc-tile-sub", sub);
    if (anchor) t.addEventListener("click", () => root.querySelector("#" + anchor)?.scrollIntoView({ behavior: "smooth" }));
    return t;
  };
  tile("Meetings today", meetings.length, nextMeeting ? `next ${nextMeeting.start}` : "none left", "", "cc-today");
  const jh = snap.jira_hours || {}; const tot = jh.total_h ?? null; const tgt = jh.target_h || 40;
  const ht = tile("Hours logged", tot === null ? "—" : `${Math.round(tot * 10) / 10}<small>/${tgt}h</small>`, jh.week || "run /dash", "", "cc-hours");
  const bar = el(ht, "div", "cc-bar"); el(bar, "div", "cc-bar-fill").style.width = `${Math.min(100, Math.round(((tot || 0) / tgt) * 100))}%`;
  tile("To-dos due", dueNow.length, overdue.length ? `${overdue.length} overdue` : "none overdue", overdue.length ? "is-red" : "", "cc-todos");
  tile("Slack waiting", snap.sources.slack ? snap.slack.length : "—", `${snap.slack.filter(s => s.kind === "dm").length} DMs`, snap.slack.length ? "is-accent" : "", "cc-inbox");
  const oldest = snap.prs.map(p => p.requested).filter(Boolean).sort()[0];
  tile("PRs to review", snap.sources.prs ? snap.prs.length : "—", oldest ? `oldest ${m().diff(m(oldest), "days")}d` : "", "", "cc-inbox");
  const blocked = openTickets.filter(t => /blocked/.test(lower(t.status))).length;
  tile("Open tickets", openTickets.length, blocked ? `${blocked} blocked` : "none blocked", blocked ? "is-amber" : "", "cc-board");
});

// ---------- today row ----------
await safe("Today", async () => {
  const row = el(root, "div", "cc-row cc-row-today");
  const cal = card(row, "Today", "◷"); cal.id = "cc-today";
  if (!meetings.length) el(cal, "div", "cc-empty", calFresh ? "No meetings today." : "No meetings found. Run /dash or /prep.");
  for (const e of meetings) {
    const it = el(cal, "div", "cc-meeting" + (e === nextMeeting ? " is-next" : "") + ((e.end || e.start) < nowHM ? " is-past" : ""));
    el(it, "div", "cc-time", e.start);
    const body = el(it, "div", "cc-mbody"); el(body, "div", "cc-mtitle", e.title);
    const key = Object.keys(prepBlocks).find(k => k.slice(6).toLowerCase() === lower(e.title));
    const sub = el(body, "div", "cc-msub");
    if (e.large) sub.setText(`${e.attendees} people · no brief`);
    else if (key !== undefined) { if (prepBlocks[key]) sub.setText("You owe: " + prepBlocks[key] + " · "); link(sub, `${journalPath}#${key}`, "prep"); }
    else sub.setText("no brief yet");
  }
  if (!calFresh && snap.sources.calendar) staleNote(cal, snap.sources.calendar);

  const td = card(row, "To-dos", "☑", "cc-todo-card"); td.id = "cc-todos";
  const form = el(td, "div", "cc-add");
  const input = form.createEl("input", { type: "text", placeholder: "Add a to-do…" });
  const cat = form.createEl("select");
  ["follow-up", "project", "review", "ticket", "idea", "growth"].forEach(c => cat.createEl("option", { text: c, value: c }));
  const due = form.createEl("input", { type: "date" }); due.value = today;
  const btn = form.createEl("button", { text: "Add", cls: "mod-cta" });
  const msg = el(td, "div", "cc-msg");
  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) { msg.setText("Type the to-do first."); return; }
    const line = `- [ ] ${text} #todo/${cat.value}${due.value ? " 📅 " + due.value : ""}`;
    let file = app.vault.getAbstractFileByPath(journalPath);
    if (!file) {
      const tpl = (await load("_system/templates/daily.md")) || `---\ntype: daily\ndate: ${today}\n---\n# ${today}\n\n## To-dos\n`;
      file = await app.vault.create(journalPath, tpl.replaceAll("{{date:YYYY-MM-DD}}", today));
    }
    await app.vault.process(file, body => {
      if (!/^## To-dos\s*$/m.test(body)) return body.trimEnd() + `\n\n## To-dos\n${line}\n`;
      const lines = body.split("\n"); let i = lines.findIndex(l => /^## To-dos\s*$/.test(l)) + 1;
      while (i < lines.length && !/^## /.test(lines[i])) i++;
      let j = i; while (j > 0 && lines[j - 1].trim() === "") j--;
      lines.splice(j, 0, line); return lines.join("\n");
    });
    input.value = ""; msg.setText("Added to today's journal — Todoist gets it on the next sync.");
  });
  input.addEventListener("keydown", e => { if (e.key === "Enter") btn.click(); });
  const list = el(td, "div", "cc-tasks");
  const renderTasks = (target, tasks) => { const prev = dv.container; dv.container = target; dv.taskList(tasks, false); dv.container = prev; };
  if (dueNow.length) renderTasks(list, dueNow.sort((a, b) => (dueOf(a) > dueOf(b) ? 1 : -1)));
  else el(list, "div", "cc-empty", "Nothing due today.");
  if (soon.length) { const d = list.createEl("details"); d.createEl("summary", { text: `Next 7 days (${soon.length})` }); renderTasks(d, soon); }
  link(el(td, "div", "cc-foot"), "todos", "All to-dos →");
});

// ---------- inbox row ----------
await safe("Inbox", async () => {
  const row = el(root, "div", "cc-row cc-row-inbox"); row.id = "cc-inbox";
  const sl = card(row, "Slack — needs you", "✉");
  if (snap.sources.slack && !snap.slack.length) el(sl, "div", "cc-empty", "Nothing waiting.");
  for (const s of snap.slack) {
    const it = el(sl, "div", "cc-item");
    el(it, "span", "cc-badge is-" + s.kind, { dm: "DM", mention: "@you", thread: "thread" }[s.kind]);
    const b = el(it, "div", "cc-ibody"); el(b, "div", "", `${s.who}${s.where ? " · " + s.where : ""}: ${s.text}`);
    const sub = el(b, "div", "cc-msub", (s.ts ? ageText(s.ts) + " · " : "")); ext(sub, s.url, "open in Slack");
  }
  staleNote(sl, snap.sources.slack);

  const right = card(row, "PRs to review", "⇄");
  if (snap.sources.prs && !snap.prs.length) el(right, "div", "cc-empty", "No reviews waiting.");
  for (const p of snap.prs) {
    const it = el(right, "div", "cc-item"); const b = el(it, "div", "cc-ibody");
    ext(b, p.url || "#", `${p.repo}#${p.number} ${p.title}`);
    el(b, "div", "cc-msub", `${p.author}${p.requested ? " · waiting " + m().diff(m(p.requested), "days") + "d" : ""}`);
  }
  staleNote(right, snap.sources.prs);

  el(right, "div", "cc-card-title cc-subtitle", "⧗ Waiting on others");
  const since = m().subtract(14, "days").format("YYYY-MM-DD");
  const recent = dv.pages('"wiki/meetings"').where(p => p.date && m(String(p.date.toISODate ? p.date.toISODate() : p.date)).format("YYYY-MM-DD") >= since)
    .sort(p => p.date, "desc").array();
  let shown = 0;
  for (const p of recent) {
    const body = await load(p.file.path);
    for (const l of section(body, "Action items").split("\n")) {
      const x = l.match(/^- (?!\[)\s*\[\[([^\]|]+)(?:\|[^\]]+)?\]\]\s*[—:-]+\s*(.+)$/);
      if (!x || isMine(x[1]) || shown >= 6) continue;
      const it = el(right, "div", "cc-item cc-wait"); const b = el(it, "div", "cc-ibody");
      link(b, x[1].split("/").pop(), x[1].split("/").pop().replace(/-/g, " ")); b.appendText(": " + x[2].replace(/\[\[([^\]|]+\|)?([^\]]+)\]\]/g, "$2").slice(0, 110));
      const sub = el(b, "div", "cc-msub"); link(sub, p.file.name, m(String(p.date)).format("MMM D") + " meeting"); shown++;
    }
  }
  if (!shown) el(right, "div", "cc-empty", "Nobody owes you anything from the last 2 weeks.");
});

// ---------- ticket board ----------
await safe("Board", async () => {
  const c = card(root, "My tickets", "▦", "cc-board-card"); c.id = "cc-board";
  const board = el(c, "div", "cc-board");
  const cols = BOARD.map(([name]) => ({ name, items: [] })); const other = { name: "Other", items: [] };
  for (const t of openTickets) { const s = lower(t.status); const i = BOARD.findIndex(([, f]) => f(s)); (i < 0 ? other : cols[i]).items.push(t); }
  if (other.items.length) cols.push(other);
  for (const col of cols) {
    const cEl = el(board, "div", "cc-col" + (col.name === "Blocked" ? " is-blocked" : ""));
    el(cEl, "div", "cc-col-head", `${col.name} · ${col.items.length}`);
    for (const t of col.items.sort((a, b) => String(a.file.name).localeCompare(b.file.name))) {
      const tk = el(cEl, "div", "cc-ticket");
      link(tk, t.file.name, t.file.name, "cc-key");
      el(tk, "div", "cc-ttitle", String(t.title || "").replace(/^[A-Z]+-\d+:\s*/, "").replace(/^\[[^\]]+\]\s*/g, "").slice(0, 60));
      const meta = el(tk, "div", "cc-tmeta");
      if (t.project) el(meta, "span", "cc-proj", slugOf(t.project).replace(/-/g, " "));
      if (t.updated) el(meta, "span", "", `${m().diff(m(String(t.updated)), "days")}d`);
    }
  }
  const weekStart = m().startOf("isoWeek").format("YYYY-MM-DD");
  const done = tickets.filter(t => /^(closed|done)/.test(lower(t.status)) && t.updated && m(String(t.updated)).format("YYYY-MM-DD") >= weekStart);
  if (done.length) { const d = c.createEl("details", { cls: "cc-done" }); d.createEl("summary", { text: `Done this week (${done.length})` }); done.forEach(t => { link(d, t.file.name, t.file.name, "cc-key"); d.appendText(" "); }); }
});

// ---------- hours ----------
await safe("Hours", async () => {
  const c = card(root, "Hours this week", "◔", "cc-hours-card"); c.id = "cc-hours";
  const jh = snap.jira_hours || {};
  if (!jh.by_day) { staleNote(c, snap.sources.jira_hours); return; }
  const wrap = el(c, "div", "cc-hours");
  const bars = el(wrap, "div", "cc-hbars");
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri"].concat(["Sat", "Sun"].filter(d => jh.by_day[d] > 0));
  const max = Math.max(8, ...days.map(d => jh.by_day[d] || 0));
  const todayName = m().format("ddd");
  for (const d of days) {
    const v = jh.by_day[d] || 0; const col = el(bars, "div", "cc-hcol" + (d === todayName ? " is-today" : ""));
    el(col, "div", "cc-hval", v ? Math.round(v * 10) / 10 : "");
    const b = el(col, "div", "cc-hbar"); b.style.height = `${Math.round((v / max) * 100)}%`;
    el(col, "div", "cc-hday", d);
  }
  const top = el(wrap, "div", "cc-htop");
  el(top, "div", "cc-tile-label", `${Math.round((jh.total_h || 0) * 10) / 10}h of ${jh.target_h || 40}h · ${jh.week}`);
  (jh.by_ticket || []).slice(0, 3).forEach(t => { const r = el(top, "div", "cc-hrow"); link(r, t.key, t.key, "cc-key"); el(r, "span", "cc-msub", ` ${Math.round(t.hours * 10) / 10}h`); });
  staleNote(c, snap.sources.jira_hours);
});

// ---------- footer ----------
await safe("Footer", async () => {
  const row = el(root, "div", "cc-row cc-row-foot");
  const j = card(row, "Journal", "✎");
  const focus = section(journal, "Focus").split("\n").map(s => s.trim()).filter(Boolean)[0];
  el(j, "div", focus ? "" : "cc-empty", focus ? "Focus: " + focus.replace(/^- /, "") : "No focus set for today.");
  const jl = el(j, "div", "cc-foot"); link(jl, journalPath.replace(/\.md$/, ""), "Today →"); jl.appendText("  ");
  link(jl, `journal/${m().subtract(1, "day").format("YYYY-MM-DD")}`, "Yesterday");

  const w = card(row, "This week", "★");
  const weekly = dv.pages('"wiki/weekly"').sort(p => p.file.name, "desc").array()[0];
  if (weekly) { const body = await load(weekly.file.path); const tl = section(body, "TL;DR").split("\n").map(s => s.trim()).filter(Boolean)[0] || "";
    el(w, "div", "cc-clamp", tl.replace(/\[\[([^\]|]+\|)?([^\]]+)\]\]/g, "$2")); }
  const impact = await load("wiki/syntheses/impact-log.md");
  const wins = (impact || "").split("\n").filter(l => /^- \d{4}-\d{2}-\d{2} — /.test(l));
  const month = wins.filter(l => l.startsWith("- " + m().format("YYYY-MM"))).length;
  el(w, "div", "cc-msub", `${month} wins this month · ${wins.length} total`);
  const wl = el(w, "div", "cc-foot"); if (weekly) { link(wl, weekly.file.name, weekly.file.name); wl.appendText("  "); } link(wl, "impact-log", "Impact log →");

  const cm = card(row, "Commands", "⌘");
  const grid = el(cm, "div", "cc-cmds");
  COMMANDS.forEach(([c, d]) => { const r = el(grid, "div", "cc-cmd"); el(r, "code", "", c); el(r, "span", "cc-msub", d); });
});
