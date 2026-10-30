---
name: heygen-avatar-director
description: Direct HeyGen AI avatar videos so they look and move more naturally. Use when the user wants a HeyGen avatar or talking-head video, or wants to fix an avatar that looks robotic, stiff, flat or repetitive. Writes a script made for speaking, plans gestures and settings beat by beat, renders through the HeyGen API, reviews the result frame by frame and re-renders only the weak beats.
---

# HeyGen Avatar Director Skill for Claude

HeyGen renders the avatar. Claude directs it: what is said, how fast, with which gesture, and whether the take is good enough to keep. Most of what makes an avatar look synthetic comes from its inputs (a script written for reading, one gesture repeated for a minute, flat pacing) and from takes nobody reviewed. This skill fixes those two things. It cannot change HeyGen's model itself.

Status: early version. The scripts follow HeyGen's documented v3 API; tell the user if a call fails and show the error message.

## 0. Setup (once)
- The user needs a HeyGen API key (HeyGen → Settings → API), exported as `HEYGEN_API_KEY`. Never print, log or commit the key; ask the user to set it in their own shell.
- API usage is billed by HeyGen on the user's account. Say this once before the first render, and point to HeyGen's pricing page rather than quoting numbers.
- Check the key: `python3 scripts/heygen.py whoami`
- Review tools need `ffmpeg` on the PATH.

## 1. Pick the avatar and the voice
```
python3 scripts/heygen.py looks --private            # the user's own avatars
python3 scripts/heygen.py looks --type photo_avatar
python3 scripts/heygen.py voices --language English --gender female
```
- Note each look's `avatar_type` and `supported_api_engines`. They decide which controls exist (see step 3 and `references/api-notes.md`).
- Prefer the look's `default_voice_id` for a digital twin, so the voice matches the face.
- If the user has no avatar yet, say what makes good source footage (`references/naturalness.md`, "Before filming") and stop there: creating the avatar happens in HeyGen.

## 2. Write the script for speaking, not reading
- Short sentences, 8 to 16 words. One idea per sentence.
- Contractions ("it's", "you'll"). Numbers written the way they are said ("twenty twenty-six", "about three percent").
- Mark where a person would breathe: a full stop or a line break, not a comma chain.
- Cut list structures ("firstly, secondly") unless the user wants them; people rarely talk in lists.
- Read the script aloud in your head at 150 words a minute. Anything that would make a person stumble will make the avatar stumble.
- Show the script to the user before rendering anything.

## 3. Write the direction plan
Split the script into beats of 1 to 3 sentences. For each beat, decide:
- **Gesture** (`motion_prompt`): one short, concrete instruction tied to what the line means, for example "small open-palm gesture toward the camera on 'you'", "slight nod, hands resting", "counts on two fingers". Vary them. Leave some beats with almost no movement: constant gesturing is one of the strongest synthetic tells.
- **Energy** (`expressiveness`, photo avatars on Avatar IV only): `low` for calm or serious lines, `medium` for most lines, `high` only for a real peak.
- **Pace** (`speed`): 0.9 to 1.05 for most lines; slower on the key line.
- **Engine**: Avatar V (`engine: avatar_v`) gives the most natural motion and lip-sync where the look supports it, and allows `more_blinking`. On Avatar V, `expressiveness` is not available. On the default Avatar IV, `motion_prompt` is rejected for video avatars (digital twins and studio avatars).

Save the plan as JSON (format in `references/plan-format.md`, example in `examples/plan.json`) and show it to the user as a short table: beat, line, gesture, energy, pace. Wait for a yes before rendering.

Check it first without spending credits:
```
python3 scripts/heygen.py render plan.json --dry-run
```
The dry run prints every request body and warns about any setting the chosen engine or avatar type would reject.

## 4. Render
```
python3 scripts/heygen.py render plan.json            # one video per beat, ids saved to plan.state.json
python3 scripts/heygen.py wait --state plan.state.json --out renders/
```
- One beat per video, because a gesture instruction applies to a whole video. Beats are joined at the end.
- Each request has an idempotency key built from the beat's content, so a retry of the same beat does not render (and bill) twice.

## 5. Review every beat before keeping it
```
python3 scripts/media.py sheet renders/b1.mp4 --every 0.5     # contact sheet of frames
python3 scripts/media.py motion renders/b1.mp4                # movement per second
```
- Look at the contact sheet yourself, beat by beat, against the checklist in `references/naturalness.md`: frozen torso, the same gesture repeated, hands that are malformed or merge, gestures on the wrong words, a fixed stare, mouth shapes that stop matching the sound, sudden jumps between frames.
- `motion` prints a movement score per second and flags seconds that are frozen or jittery compared with the rest of the clip. Use it to find where to look; judge with your own eyes.
- You cannot hear the audio. Ask the user to listen for pacing and pronunciation, or read the caption file if HeyGen returned one (saved next to the clip as `.srt`).
- For each weak beat, write down the problem and the change (for example "repeats the same right-hand sweep three times → gesture: 'hands rest, one small nod'"). Re-render only that beat. Stop after two re-renders of the same beat and tell the user what still looks off.

## 6. Join and deliver
```
python3 scripts/media.py join final.mp4 renders/b1.mp4 renders/b2.mp4 renders/b3.mp4
```
- Check the joins on a contact sheet: the avatar's position and framing should not jump between beats. If it does, use the same `aspect_ratio`, `fit` and background for every beat.
- Send the final video with a short note: which beats were re-rendered and why.

## Rules
- Never put the API key in a file, a command shown to the user, or a commit.
- Never render without the user's go-ahead on the script and the plan.
- Only use avatars the user owns or has rights to. Do not make an avatar of a real person without their consent.
- Be honest about limits: if a problem comes from the model (for example hands), say so instead of promising a fix.
