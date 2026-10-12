# Site data and how the numbers are tallied

Everything numeric on the home page is derived, not typed. Sources, in order of what feeds what:

| Number | Source | Rebuild |
|---|---|---|
| talks, classes taught, podcasts | the three tables in `docs/ref/jz-content.md` (one row per delivery; add private classes there too) | parsed at build time by `src/lib/content.ts` |
| engineers taught live | `data/students.json`: per-class student counts keyed by the class date in the classes table | see below |
| labs built | next-gen-governance `services/ui_frontend/src/lib/labs/content/labs/*.mdx` + `docs/labs/*.md` here + github.com/JonZeolla repos matching `lab` (minus the deprecated `Lab` and `lab-resources`) | count by hand; comment on the stat in the page records the formula |
| public repos | github.com/jonzeolla profile | by hand |
| GitHub contribution calendar | the public widget `https://github.com/users/jonzeolla/contributions` (matches the profile number; the GraphQL API counts differently) | `src/lib/github.ts` at build time; snapshot in `src/data/github-contributions.json` |
| Trusted-by logos | student employers from the SANS rosters (`scripts/sans_rosters.py employers`), 22 chosen by hand, plus ClickUp | by hand |

## Students taught

Rule set agreed 2026-10-11:

1. SANS classes: count the rows in the roster spreadsheet(s) in each class folder, in person + live online. Rosters live in the
   Google Drive folders "SEC540 Classes" and "SEC545 Classes" (download both as zips, then run
   `python3 -I scripts/sans_rosters.py students ~/Downloads/*SEC540*.zip ~/Downloads/*SEC545*.zip`). Match each folder's
   count to the exact date in the classes table and record it in `students.json` with `"source": "roster"`.
2. Non-SANS classes without a count: 20 each (the `default` in `students.json`).
3. Known exceptions recorded as `"source": "given"`: Container Security 101 SANS workshops 50 each (2023-04-27, 2023-10-16),
   Mastering Policy as Code SANS workshop 35 (2023-11-01), AI-Native Software Development private classes: 2026-04-07 = 15,
   2026-10-07 = 30.
4. OnDemand recordings count as 0 (2025-03-17). Future classes are not counted.
5. Three SANS classes had no roster in the Drive export on 2026-10-11 and currently use the default: 2022-02-28 Cyber Security
   Central, 2024-07 Private, 2025-08-25 Emerging Threats VA Beach. Replace with real counts when found.

Total on 2026-10-11: 1,224 across 57 past classes (684 from rosters, 180 given, 360 default). Displayed as "1,200+ engineers
taught live" (rounded down to the hundred). "Live" means in person or live online; recordings are excluded.

## llms.txt

`src/pages/llms.txt.ts` renders it from the same data at build time. Edit that file for wording; the counts fill themselves.

## Checking the tally

`npm test` asserts the students total for 2026-10-11 (1,224) and the row counts; update the expected numbers there when the
data changes on purpose. The students sum is computed in `src/lib/students.ts`.
