# HeyGen Avatar Director Skill for Claude

**Make HeyGen AI avatars look and move more naturally, with Claude as the director.** An open-source Claude Agent Skill that writes a script made for speaking, plans gestures and settings beat by beat, renders through the official HeyGen API, reviews every take frame by frame and re-renders only the weak parts.

> **Status: early development (v0.1).** The idea and the workflow are in place, and the scripts follow HeyGen's documented v3 API, but they have not yet been run against a live HeyGen account. Please open an issue if a call fails for you.
>
> Not affiliated with HeyGen or Anthropic. You use your own HeyGen API key and pay HeyGen for what you render.

## Why

Most of what makes an AI avatar look synthetic is not the face. It is:

- **a script written for reading**, with long sentences no one would say in one breath;
- **one gesture, repeated** for a whole minute, or a gesture on every single sentence;
- **flat pacing**, the same speed and energy for a joke and for a serious point;
- **takes nobody reviewed**, so a frozen stretch, a wrong mouth shape or a strange hand stays in the final video.

HeyGen exposes controls for most of this (`motion_prompt`, `expressiveness`, voice speed and pitch, Avatar V with more natural blinking). This skill makes Claude use them on purpose, line by line, and then check the result like an editor would. It cannot change HeyGen's model; when a problem comes from the model, it says so.

## How it works

1. **Avatar and voice.** Claude lists your HeyGen looks and voices and checks which engines each look supports.
2. **Script for speaking.** Short sentences, contractions, numbers written the way they are said, a pause where a person would breathe.
3. **Direction plan.** The script is split into beats of one to three sentences. Each beat gets a specific gesture tied to what it says, an energy level and a pace. Some beats get almost no movement on purpose.
4. **Dry run, then render.** The dry run prints every request and catches settings the chosen engine would reject, before any credits are spent. Each beat renders as its own clip.
5. **Review.** For every clip Claude makes a contact sheet of frames and a movement-per-second report, and checks them against a naturalness checklist: repeated gestures, frozen torso, fixed stare, lip-sync drift, hands, jumps.
6. **Fix and join.** Only weak beats are re-rendered, with a written reason for each change. The beats are joined into the final video.

## What using it looks like

> **You:** Make a 30-second intro video with my HeyGen avatar. It always looks a bit robotic.
>
> **Claude:** Here's a script in 3 beats, and a plan: beat 1 small nod and hands resting, beat 2 calm and still with a slight lean in on the key line, beat 3 one open-palm gesture on "every answer". Pace 1.0, 0.94, 0.97. Render?
>
> **You:** Go.
>
> **Claude:** *(renders, reviews)* Beat 2 repeats the same hand sweep three times and the torso freezes from 4 to 6 s. Re-rendering beat 2 with "hands rest, one small nod". Beats 1 and 3 look natural. Here's the final video.

## Setup

1. **HeyGen API key.** In HeyGen, go to Settings → API and create a key. API usage is billed by HeyGen; check their pricing page first.
2. **Set the key in your own shell** (never paste it into a chat or a file you commit):
   ```bash
   export HEYGEN_API_KEY="your key"
   ```
3. **ffmpeg** for the review and join tools (`brew install ffmpeg` on macOS).
4. **Add the skill to Claude.**
   - **Claude Code, as a plugin:** `claude plugin marketplace add sabaazdn73/heygen-avatar-director-skill-for-claude`, then `claude plugin install heygen-avatar-director@heygen-avatar-director`. Or run `/plugin` inside Claude Code and add it from there.
   - **Claude Code, as a plain skill:** copy `skills/heygen-avatar-director/` to `~/.claude/skills/heygen-avatar-director/`.
   - **Claude app:** zip the `skills/heygen-avatar-director` folder and upload it under **Settings → Capabilities → Skills**. Claude needs a shell that can reach api.heygen.com, so use it in Claude Code or with your computer linked.
5. Check the key: `python3 skills/heygen-avatar-director/scripts/heygen.py whoami`

## The scripts

```bash
# HeyGen API (standard library only)
python3 scripts/heygen.py looks --private
python3 scripts/heygen.py voices --language English
python3 scripts/heygen.py render plan.json --dry-run
python3 scripts/heygen.py render plan.json
python3 scripts/heygen.py wait --state plan.state.json --out renders/

# Review and join (needs ffmpeg)
python3 scripts/media.py sheet renders/b1.mp4 --every 0.5
python3 scripts/media.py motion renders/b1.mp4
python3 scripts/media.py join final.mp4 renders/b1.mp4 renders/b2.mp4 renders/b3.mp4
```

The plan format is in [`references/plan-format.md`](skills/heygen-avatar-director/references/plan-format.md), with an example in [`examples/plan.json`](skills/heygen-avatar-director/examples/plan.json). The review checklist is in [`references/naturalness.md`](skills/heygen-avatar-director/references/naturalness.md).

## Roadmap

- [ ] First end-to-end run on a live HeyGen account, with before and after examples
- [ ] Gesture library: tested motion prompts that read as natural, by type of line
- [ ] Side-by-side comparison of the same script with default settings and with direction
- [ ] Optional use of HeyGen's MCP server instead of the API key

## Responsible use

Only make avatars of yourself or of people who have given their consent, and follow HeyGen's terms. Tell your audience when a video uses an AI avatar.

## License

MIT, see [LICENSE](LICENSE).
