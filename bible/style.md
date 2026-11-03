# Style Guide

How the prose is written and how it is laid out on the site.

## Voice

- **Rotating close third person, present tense.** Each chapter stays inside one character's head: what they notice, how they name things, what they get wrong. The narration never knows more than that character does.
- **One viewpoint per chapter.** A chapter may switch viewpoint only at a section break, and only when the first character can no longer see the scene (for example, when Kamala loses consciousness). Most chapters never switch.
- **Cold opens and interludes may be unanchored.** Scenes with none of our characters present (the impact, a town at night) are told from outside, spare and visual, like a camera.
- **The viewpoint colours the language.** Ananya is dry and decisive and thinks in money and plans. Arjun notices small physical details and translates Hindi in his head. Kabir narrates in confident shorthand and gaming slang. Aditya thinks in patterns and probabilities. Sid's chapters run on jokes that get thinner as things get worse.

## Prose

- Short paragraphs. White space is pacing.
- Concrete over abstract: brands, temperatures, prices, times, place names, real streets and food.
- No exposition dumps. World facts arrive through what the viewpoint character sees on a screen, hears, or misreads.
- Dialogue in double quotes, attributed with "says" or by action. No adverbs on dialogue tags.
- The sound of the infected is always written `HNNNNG...` in italics and never explained.

## Code-switching

Write the original words in italics, followed by the English in square brackets:

> *Didi.* [Sis.]

Translate every non-English line, including single words like *Amma* [Mom].

## Screens

Phone messages, notifications, notices, news tickers, and headlines are set apart as screen blocks, one line each, written exactly as they appear on the screen:

```
> **MOM:** ARE YOU AWAKE
> **MOM:** CALL
```

Screens are part of the series' identity (the feed never goes dark), so use them for anything the characters read.

## Accuracy

Every geographic, biological, medical, and scientific detail is checked against reliable sources before it is published. See the world rules in [series.md](series.md).

## Chapter files

Chapters live in `story/season-NN/episode-NN/` as Markdown, numbered in reading order (`01-impact.md`). Each starts with front matter:

```
---
title: Impact
pov: none            # or the viewpoint character's first name
date: Thursday, 19 February 2026
place: Northern Canada
---
```

Use `* * *` on its own line for a section break.

## Episode themes

Every episode has its own look on the site, defined in that episode's `episode.json`:

- `palette` — light and dark colours (`bg`, `fg`, `muted`, `accent`, `rule`, `screen`).
- `fonts` — a display face for titles and a body face for the prose, both from Google Fonts.
- `mood` — one line describing what the theme is reaching for.

The theme should come from the episode's world. Episode 1 is late winter seen through a phone screen at night: cold paper and frost, with the red of a notification badge. Later episodes should look as different as their stories feel; the heat episodes should feel hot.
