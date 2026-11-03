# The Last Normal Week

A serialised post-apocalyptic story by [Vishnu Gandarapu](https://vishnugandarapu.in), written in prose and published at [vishnugandarapu.in/last-normal-week](https://vishnugandarapu.in/last-normal-week/).

A meteorite lands in a Canadian forest. Ten weeks later, Indian summer might be the only thing that can stop what came out of it. Until then, five students, one campus outside Indore, and a country that refuses to fall.

## How the story is organised

Like a television season, so it can be adapted later:

- **Season** — a complete arc with its own title.
- **Episode** — several chapters, with its own theme and look on the site.
- **Chapter** — one page.

## What's in the repo

| Path | What it is |
|---|---|
| `bible/series.md` | Premise, world rules, cast, and season architecture. The source of truth. |
| `bible/style.md` | How the prose is written and how chapters and episode themes are set up. |
| `bible/season-01.md` | Episode-by-episode plan for Season 1. |
| `story/` | The story itself: `season-NN/episode-NN/` folders of chapter Markdown files, each episode with an `episode.json` for its title, summary, and theme. |
| `build.py` | Turns `story/` into the website in `site/`. Python 3, no dependencies. |
| `.github/workflows/pages.yml` | Builds and publishes the site to GitHub Pages on every push to `main`. |

## Writing a new chapter

1. Add `story/season-NN/episode-NN/NN-title.md` with front matter (`title`, `pov`, `date`, `place`). See `bible/style.md`.
2. For a new episode, add an `episode.json` with its own palette and fonts.
3. Run `python3 build.py`, then open `site/index.html` (or `python3 -m http.server -d site`) to preview.
4. Push to `main` to publish.

## Copyright

© Vishnu Gandarapu. All rights reserved. This is a work of fiction; names, characters, and events are invented, and any resemblance to real people is coincidental.
