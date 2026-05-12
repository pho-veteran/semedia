# Audit HTML Report and Remediation Design

Date: 2026-05-12

## Purpose

Create a polished standalone HTML version of `docs/implementations/codebase-audit-report-2026-05-12.md` for both executive review and engineering handoff, then run a controlled high-priority remediation pass against the audit findings.

## Scope

This work has two coordinated outputs:

1. A static, offline-readable HTML audit report generated from the existing Markdown report.
2. Surgical code/test fixes for high-priority audit findings that can be safely handled without schema migrations, vector-index infrastructure, durable queues, or broad architecture rewrites.

Out of scope for this pass:

- ANN/vector database migration.
- Durable job queue implementation.
- Full canonical scene-identity migration across persisted benchmark artifacts.
- Large retrieval-score calibration project.
- External assets, CDNs, hosted report viewers, or new frontend app routes.

## HTML Report Design

The HTML report will be a self-contained file saved beside the Markdown source:

- Source: `docs/implementations/codebase-audit-report-2026-05-12.md`
- Output: `docs/implementations/codebase-audit-report-2026-05-12.html`

The report optimizes for both audiences:

- Executive layer at the top:
  - audit date and scope;
  - overall risk posture;
  - KPI-style cards for architecture, retrieval, identifiers, captions, and benchmark rigor;
  - top high-impact findings;
  - ranked remediation roadmap.
- Engineering layer below:
  - original report sections preserved with citations;
  - sticky table of contents;
  - severity/impact visual accents;
  - collapsible deep-dive sections where useful;
  - printable layout.

Implementation constraints:

- Static HTML/CSS, with optional small vanilla JavaScript for section toggles.
- No external dependencies, CDNs, fonts, or images.
- Preserve all technical meaning and file/line citations from the Markdown source.
- Do not modify application code while generating the report.

## Subagent Roles

### Haiku subagent — report builder

The Haiku subagent will create the standalone HTML report only. It may read the Markdown report and write the HTML output. It must not edit backend, frontend, tests, benchmark artifacts, or project configuration.

Expected output from Haiku:

- `docs/implementations/codebase-audit-report-2026-05-12.html`
- brief summary of layout choices and any content transformations.

### Sonnet subagent — code audit and fixes

The Sonnet subagent will perform a high-priority code audit/fix pass. It should prioritize safe, testable changes from the audit:

1. Low-risk correctness:
   - fix `_stable_scene_key()` tuple fallback;
   - add bounded `top_k` behavior;
   - align frontend `SearchResult` typing with backend `scene_index` and `scene_key` fields.
2. Evaluation hardening:
   - prevent duplicate retrieved IDs from inflating metrics;
   - keep strict benchmark behavior explicit and safe;
   - improve negative-query/sign-off behavior only if it can be done surgically with tests.
3. Retrieval quality groundwork:
   - consider candidate-breadth settings before fusion if it can be implemented with focused tests;
   - report, rather than half-implement, anything requiring broad architecture changes.

Sonnet constraints:

- Keep edits surgical.
- Add or update tests for each behavior changed.
- Use Docker-based test commands.
- Do not implement ANN/vector DB, durable queues, schema migrations, or full benchmark ID migration in this pass.
- Do not commit changes unless the user explicitly asks.

## Verification Strategy

The coordinator will inspect subagent changes before reporting success.

HTML report verification:

- Confirm the HTML file exists.
- Confirm it contains executive summary, top findings, recommendations, and preserved citations.
- Confirm it is self-contained and does not reference external assets.

Code verification:

- Run targeted Docker service tests for changed backend/evaluation files.
- Run frontend Docker build/lint/test only if frontend code changes are made and Docker configuration supports it.
- If full-stack or browser validation becomes necessary, explicitly state what was and was not validated.

## Success Criteria

- The HTML report is readable offline, useful to executives, and detailed enough for engineers.
- High-priority fixes are either implemented with tests or explicitly deferred with a clear reason.
- All completed fixes have targeted Docker verification evidence.
- No unrelated refactors or broad architecture rewrites are introduced.
