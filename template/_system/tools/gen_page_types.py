#!/usr/bin/env python3
"""Generate _system/page-types/<type>.md and _system/templates/<type>.md from one table.

Usage: python3 _system/tools/gen_page_types.py
Edit TYPES below, re-run, commit. Keep field lists in sync with _system/tests/check_vault.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COMMON = [
    ("type", "yes", "Page type (fixed per folder)"),
    ("title", "yes", "Human-readable title"),
    ("aliases", "yes", "Alternate names so [[links]] resolve; check before creating pages"),
    ("status", "yes", "See status values below"),
    ("tags", "yes", "Free tags; to-do tags go on checkboxes, not here"),
    ("sources", "yes", "Wikilinks into raw/ or external URLs this page is built from"),
    ("created", "yes", "YYYY-MM-DD"),
    ("updated", "yes", "YYYY-MM-DD — bump on every edit"),
]

# extra fields: (name, default, note) — default "[]" means list
TYPES = {
    "person": {
        "folder": "people", "file": "firstname-lastname.md",
        "purpose": "Someone {{sage.owner.first_name}} works with: manager, director, peer, report, stakeholder.",
        "status": ["active", "former"],
        "extra": [("role", "", "Job title"), ("team", "", "Team / org"),
                  ("relation", "peer", "manager | director | peer | report | stakeholder"),
                  ("emails", "[]", "Work email addresses — first key for matching people across sources"),
                  ("slack", "", "Slack user ID, e.g. U0123456789"),
                  ("jira", "", "Jira account ID"),
                  ("github", "", "GitHub login")],
        "sections": [("Role & context", "What they own, what they care about."),
                     ("Working with them", "Preferences, communication style, what lands well."),
                     ("Open threads", "Things in flight between {{sage.owner.first_name}} and them."),
                     ("Timeline", "Dated one-liners, newest first: `- 2026-10-18 — [[meeting]]: …`")],
    },
    "project": {
        "folder": "projects", "file": "<project-slug>.md",
        "purpose": "A body of work with a goal: initiative, feature, migration, epic.",
        "status": ["planned", "active", "paused", "done"],
        "extra": [("owner", "", "[[person]]"), ("repos", "[]", "[[repo]] list"),
                  ("tickets", "[]", "[[JIRA-KEY]] list"), ("start", "", "YYYY-MM-DD"),
                  ("target", "", "YYYY-MM-DD")],
        "sections": [("Goals", "Why this exists; success criteria."),
                     ("Current status", "2–5 bullets, kept current."),
                     ("Key decisions", "Links to [[decisions]]."),
                     ("Open questions", "Unresolved items."),
                     ("Timeline", "Dated one-liners, newest first.")],
    },
    "repo": {
        "folder": "repos", "file": "<repo-name>.md",
        "purpose": "A code repository: architecture and tribal knowledge.",
        "status": ["active", "archived"],
        "extra": [("url", "", "GitHub URL"), ("language", "", "Primary language"),
                  ("owners", "[]", "[[person]] list")],
        "sections": [("Architecture", "Main modules and how data flows."),
                     ("Conventions", "Patterns, naming, testing approach."),
                     ("Gotchas", "Things that bite; known traps."),
                     ("How to run & test", "Commands.")],
    },
    "ticket": {
        "folder": "tickets", "file": "<JIRA-KEY>.md",
        "purpose": "A Jira work item — summary and context only; Jira is the system of record.",
        "status": ["mirrors Jira status (e.g. To Do, In Progress, In Review, Done)"],
        "extra": [("key", "", "Jira key, e.g. XOM-1234"), ("url", "", "Jira URL"),
                  ("project", "", "[[project]]"), ("assignee", "", "[[person]]"),
                  ("sprint", "", "Sprint name")],
        "sections": [("Why it matters", "Business/tech reason."),
                     ("Scope & acceptance", "What done means."),
                     ("Notes & progress", "Dated notes, newest first.")],
    },
    "pr": {
        "folder": "prs", "file": "<repo>-<number>.md",
        "purpose": "A GitHub pull request — summary and review context; GitHub is the record.",
        "status": ["open", "merged", "closed"],
        "extra": [("repo", "", "[[repo]]"), ("number", "", "PR number"), ("url", "", "PR URL"),
                  ("author", "", "[[person]]"), ("ticket", "", "[[JIRA-KEY]]")],
        "sections": [("What changed", "The change in 3–6 bullets."),
                     ("Review notes", "Key feedback and how it was resolved."),
                     ("Follow-ups", "Work spun out of this PR.")],
    },
    "meeting": {
        "folder": "meetings", "file": "YYYY-MM-DD-<slug>.md",
        "purpose": "Compiled summary of one meeting (raw notes stay in raw/meetings/).",
        "status": None,
        "extra": [("date", "", "YYYY-MM-DD"), ("attendees", "[]", "[[person]] list"),
                  ("project", "", "[[project]] if any")],
        "sections": [("Discussion", "Key points by topic."),
                     ("Decisions", "Each linked to a [[decision]] page when significant."),
                     ("Action items", "{{sage.owner.first_name}}'s as `- [ ] … #todo/<cat>`; others' as plain bullets with [[owner]].")],
    },
    "one-on-one": {
        "folder": "one-on-ones", "file": "1on1-<person-slug>.md",
        "purpose": "ONE running page per 1:1 relationship. Newest session first.",
        "status": ["active", "ended"],
        "extra": [("person", "", "[[person]]"), ("cadence", "", "weekly | biweekly | monthly"),
                  ("last", "", "YYYY-MM-DD of latest session")],
        "sections": [("Open threads", "Topics still in progress across sessions."),
                     ("Feedback themes", "Recurring feedback, with dates."),
                     ("My commitments", "{{sage.owner.first_name}}'s to-dos as checkboxes."),
                     ("Their commitments", "What they said they'd do; plain bullets."),
                     ("Session history", "`### YYYY-MM-DD` blocks, newest first, each linking its raw file.")],
    },
    "concept": {
        "folder": "concepts", "file": "<concept-slug>.md",
        "purpose": "Domain or technical knowledge; glossary terms.",
        "status": None,
        "extra": [],
        "sections": [("Explanation", "Plain-language explanation."),
                     ("How it applies here", "Where it shows up in {{sage.owner.first_name}}'s work.")],
    },
    "idea": {
        "folder": "ideas", "file": "<idea-slug>.md",
        "purpose": "An idea or proposal, tracked from seed to outcome.",
        "status": ["seed", "exploring", "proposed", "adopted", "dropped"],
        "extra": [("origin", "", "Where it came from: [[raw/thoughts/…]] or [[meeting]]"),
                  ("effort", "", "S | M | L"), ("impact", "", "low | medium | high")],
        "sections": [("Problem", "What pain this addresses."),
                     ("Proposal", "The idea."),
                     ("Open questions", "What needs answering."),
                     ("Next steps", "Checkboxes with #todo/idea.")],
    },
    "decision": {
        "folder": "decisions", "file": "YYYY-MM-DD-<slug>.md",
        "purpose": "An ADR-style record of a significant decision.",
        "status": ["proposed", "accepted", "superseded"],
        "extra": [("date", "", "YYYY-MM-DD"), ("deciders", "[]", "[[person]] list"),
                  ("supersedes", "", "[[decision]] this replaces, if any")],
        "sections": [("Context", "What forced the decision."),
                     ("Decision", "What was decided."),
                     ("Alternatives considered", "And why not."),
                     ("Consequences", "What this changes.")],
    },
    "synthesis": {
        "folder": "syntheses", "file": "<slug>.md",
        "purpose": "A saved answer, comparison, or analysis from /ask.",
        "status": None,
        "extra": [("question", "", "The question that produced this page")],
        "sections": [("Answer", "The synthesised answer."),
                     ("Evidence", "Bullets citing [[pages]].")],
    },
    "weekly": {
        "folder": "weekly", "file": "YYYY-Www.md (ISO week, e.g. 2026-W43.md)",
        "purpose": "One page per ISO week, written by /weekly from week_facts.py output only.",
        "status": None,
        "extra": [("week", "", "ISO week, e.g. 2026-W43"),
                  ("start", "", "Monday, YYYY-MM-DD"),
                  ("end", "", "Sunday, YYYY-MM-DD")],
        "sections": [("Shipped", "Merged PRs, closed tickets, tools/agents shipped — `[[link]] — what (date)`."),
                     ("Decisions", "Decision pages dated this week."),
                     ("Progress by project", "One line per project with timeline activity this week."),
                     ("Open loops & blockers", "Blocked tickets, overdue to-dos, pending digests."),
                     ("Next week", "Open to-dos due next week; {{sage.owner.first_name}}'s tickets in progress."),
                     ("Numbers", "Meetings filed, pages created/updated, to-dos done/added.")],
    },
}


def spec_md(t, d):
    rows = [c for c in COMMON if not (c[0] == "status" and d["status"] is None)]
    lines = [
        "---", "type: page-type-spec", f"title: Page type — {t}", "---",
        f"# Page type: {t}", "",
        f"**Folder:** `wiki/{d['folder']}/`  ",
        f"**File name:** `{d['file']}`  ",
        f"**Purpose:** {d['purpose']}  ",
        f"**Template:** `_system/templates/{t}.md`", "",
        "## Frontmatter", "", "| Field | Required | Notes |", "|---|---|---|",
    ]
    esc = lambda s: s.replace("|", "\\|")  # pipes in notes would break the table
    lines += [f"| `{n}` | {r} | {esc(note)} |" for n, r, note in rows]
    lines += [f"| `{n}` | yes | {esc(note)} |" for n, _, note in d["extra"]]
    lines += ["", "## Status values", ""]
    if d["status"] is None:
        lines.append("No `status` field for this type.")
    else:
        lines.append(", ".join(f"`{s}`" for s in d["status"]))
    lines += ["", "## Body sections", "", "In this order:", "",
              "1. `## TL;DR` — 2–4 lines a reader can stop after."]
    for i, (h, note) in enumerate(d["sections"], start=2):
        lines.append(f"{i}. `## {h}` — {note}")
    n = len(d["sections"]) + 2
    lines += [f"{n}. `## Related` — wikilinks to related pages.",
              f"{n + 1}. `## Sources` — links into `raw/` or external URLs.", "",
              "## Rules", "",
              "- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.",
              "- Bump `updated:` on every edit.",
              "- Every claim must trace to `sources:`.",
              "- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.", ""]
    return "\n".join(lines)


def template_md(t, d):
    fm = ["---", f"type: {t}", 'title: "{{title}}"', "aliases: []"]
    if d["status"] is not None:
        fm.append(f"status: {d['status'][0].split(' ')[0] if t != 'ticket' else 'To Do'}")
    fm += ["tags: []", "sources: []", "created: {{date:YYYY-MM-DD}}", "updated: {{date:YYYY-MM-DD}}"]
    fm += [f"{n}: {default}".rstrip() for n, default, _ in d["extra"]]
    fm.append("---")
    body = ["# {{title}}", "", "## TL;DR", ""]
    for h, _ in d["sections"]:
        body += [f"## {h}", ""]
    body += ["## Related", "", "## Sources", ""]
    return "\n".join(fm + body)


def main():
    for t, d in TYPES.items():
        (ROOT / "_system/page-types" / f"{t}.md").write_text(spec_md(t, d), encoding="utf-8")
        (ROOT / "_system/templates" / f"{t}.md").write_text(template_md(t, d), encoding="utf-8")
        print(f"wrote page-types/{t}.md and templates/{t}.md")


if __name__ == "__main__":
    main()
