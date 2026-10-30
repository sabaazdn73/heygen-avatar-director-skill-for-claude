# What makes an avatar look synthetic, and what to do about it

Use this as the review checklist in step 5 and as the source of direction notes in step 3. Each row: what you see, why it reads as fake, and the change to try. Some problems come from the model and cannot be directed away; say so when that is the case.

## Movement

| What you see | Why it reads as fake | Try |
|---|---|---|
| The same gesture repeated (one hand sweeping out again and again) | People rarely repeat a gesture exactly; repetition is the clearest machine tell | Give each beat a different, specific gesture, and leave some beats with hands at rest |
| Gesturing on every sentence | Real speakers gesture on the ideas they care about and rest between them | Only 1 in 2 or 3 beats gets a visible gesture; the rest get "hands resting, small nod" |
| Gesture lands on the wrong word | Gestures normally arrive just before or on the stressed word | Tie the gesture to a word in the line: "open palm toward camera on 'you'" |
| Frozen torso, only the mouth moves | Breathing and small weight shifts are always there in real footage | Ask for "slight natural sway, relaxed shoulders"; on Avatar V the reference look matters most |
| Sudden jump between frames | Usually a render glitch or a join between beats | Re-render the beat; for joins, keep aspect ratio, fit and background identical |
| Big energy on a calm line | Energy that does not match meaning feels performed | Lower `expressiveness` (photo avatars) or ask for "calm, still" in the motion prompt |

## Face and eyes

| What you see | Why it reads as fake | Try |
|---|---|---|
| Fixed stare, rare blinking | People blink every few seconds, more when thinking | On Avatar V set `more_blinking`; on others, short sentences give natural pauses |
| Mouth shapes stop matching the sound | Lip-sync drift on long or fast lines | Slow the line slightly (speed 0.9 to 0.95), shorten it, or split it into two beats |
| Smile frozen through serious content | Expression should follow the line | Write the emotion into the line itself; keep `expressiveness` low on serious beats |

## Hands

| What you see | Why it reads as fake | Try |
|---|---|---|
| Fingers merge, extra or missing fingers | A known model weakness | Prefer gestures with hands lower in frame or partly resting; re-render once; if it persists, tell the user it is a model limit |

## Voice and pacing (ask the user to listen)

| What you hear | Why it sounds fake | Try |
|---|---|---|
| Even rhythm, no pauses | Real speech speeds up and slows down | Vary `speed` by beat (0.9 to 1.05); end beats on full stops |
| Long sentence in one breath | No one speaks 35 words without a pause | Split into shorter sentences |
| Numbers or names said wrongly | Text-to-speech reads symbols literally | Write them out as spoken words, or use a HeyGen brand glossary |

## Before filming (digital twins)

The source footage sets the ceiling. For a digital twin, tell the user:
- Even, soft light on the face; no strong shadows or backlight.
- Camera at eye level, framing that matches the videos they will make.
- Speak naturally for the whole recording, with real pauses and small natural movements; do not sit frozen and do not over-gesture.
- Plain, steady background; clothes without fine stripes.
- Follow HeyGen's own current filming guide for the exact length and format.
