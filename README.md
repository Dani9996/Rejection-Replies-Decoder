# Rejection Decoder

A free, no-install tool that reads a job rejection email and estimates two things:

1. **Automated / templated** — is this a mass-mailed boilerplate rejection?
2. **AI-generated** — does the wording look like it was written by an AI?

Everything runs locally in your browser. Nothing is uploaded — you can safely paste real emails.

## Try it

Open **`index.html`** in any browser (just double-click it). Paste a rejection email, click **Analyze**, and you get two scored verdicts plus the exact phrases that triggered them.

There are three example buttons (templated / AI / human) so you can see how it behaves before pasting your own.

> **Want it online?** Drop this repo into GitHub Pages (Settings → Pages → deploy from `main`) and `index.html` becomes a live link you can share.

## How it works

The tool doesn't "understand" the email. It hunts for known signals and counts them:

- **Boilerplate phrases** common in mass rejections ("after careful consideration", "other candidates")
- **Automation markers** — no-reply addresses, requisition IDs, unsubscribe links, applicant-tracking-system branding
- **AI-style phrasing and over-used words** ("I hope this email finds you well", "robust", "delve")
- A weak structural tell: unusually uniform sentence length

Each family of signals contributes to a 0–1 score, mapped to plain labels: *unlikely → possible → likely → very likely*.

## An honest limitation

**This is a heuristic, not proof.** Email text alone can't conclusively show who or what wrote it — a person can send boilerplate, and a company can hand-write something that trips the AI flag. The tool says "likely", never "definitely", and always shows its evidence so you can judge for yourself.

## What's in this repo

| File | What it is |
|------|------------|
| `index.html` | The full browser tool — open this |
| `detector.py` | The same logic as a Python module |
| `cli.py` | Command-line version (`python3 cli.py -f email.txt`) |
| `slides/` | Carousel images explaining the tool |

## Tuning it

All the phrase lists live near the top of `index.html` (and `detector.py`). Add your own patterns to the lists to fit the rejections you actually receive.

## License

MIT — free to use, change, and share.
