# jonzeolla.com

Two builds, one site:

- **Astro** (`src/`, `public/`, `astro.config.mjs`) renders the home page, `/talks.html`, `/llms.txt`, and the redirect stubs for old URLs.
- **Sphinx** (`docs/`) renders the hands-on labs at `/labs/*.html` (plus `/ref/*` and `_static/`), skinned with Furo to the same tokens.

`task build` runs both and merges the Sphinx output into `dist/`, which is what GitHub Pages serves.

## Getting set up

You need [`task`](https://taskfile.dev/installation/), [`uv`](https://docs.astral.sh/uv/getting-started/installation/), Node 22.6+ (npm), and Docker for the lab tests.

```
task init        # uv sync, npm ci, Playwright browsers
task build       # dist/ = Astro site + Sphinx labs
task open        # open dist/index.html
task dev         # Astro dev server (home page and /talks only; labs need task build)
task test-site   # unit tests, astro check, offline link check over dist/
task test        # lab tests on a throwaway EC2 instance (macOS only; see tests/README.md)
task update      # bump Python and Node dependencies (the weekly Update workflow opens a PR from this)
```

## Where content lives

| What | Where | Notes |
|---|---|---|
| Talks, classes, podcasts | `docs/ref/jz-content.md` | Three markdown tables. Parsed by `src/lib/content.ts`; feeds the home page's Upcoming list, `/talks.html`, `/llms.txt`, and the counts. Add new rows here, including private classes. |
| Students taught | `data/students.json` | Per-class counts with their source; see `data/README.md` for the rules and `scripts/sans_rosters.py` for refreshing from SANS rosters. |
| Hero copy, links, hand-maintained counts | `src/lib/site.ts` | Labs built and public repos carry their formula in a comment. |
| Featured recordings | `src/data/featured.ts` | Thumbnails in `public/yt/`; `scripts/thumbnails.sh` fetches YouTube stills or renders a card for talks with stock art. |
| Lab modules | `src/data/labs.ts` | Mirrors the lab guides in next-gen-governance. |
| "Trusted by" logos | `src/data/logos.ts`, `public/wm/`, `public/wm-dark/` | `scripts/logos_dark.py` makes the dark-mode variants. |
| GitHub calendar | fetched at build from the public contributions widget; snapshot in `src/data/github-contributions.json` | The daily Deploy workflow keeps it fresh. |
| Labs | `docs/labs/*.md` | Sphinx + MyST; tested end to end by `tests/test_labs.py`. |

## Lab tests

`task test` builds the labs, scrapes each page with Playwright, deploys an EC2 instance with OpenTofu, and runs the lab's commands over SSH the way a learner would. Set `LAB` to run one lab; `task destroy` tears environments down. Details and lessons learned in [tests/README.md](./tests/README.md).

The tests save and restore your clipboard; that is imperfect.

## Known issues

1. A heredoc can't be used in a `{code-block} console`, because the non-prompt lines won't be copied by the copy button.
