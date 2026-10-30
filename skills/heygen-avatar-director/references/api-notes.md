# HeyGen v3 API notes used by this skill

Checked against HeyGen's developer docs (developers.heygen.com) in October 2026. If HeyGen changes the API, trust their docs over this file.

- Base URL `https://api.heygen.com`, API key in the `x-api-key` header.
- `GET /v3/users/me`: check the key.
- `GET /v3/avatars/looks`: list looks (`avatar_type`, `ownership`, `group_id`, `limit` up to 50, `token` for the next page). Each look has `id` (pass it as `avatar_id`), `avatar_type`, `supported_api_engines`, `default_voice_id`.
- `GET /v3/voices`: list voices (`type`, `language`, `gender`, `engine`, `limit` up to 100).
- `POST /v3/videos` with `type: "avatar"`: create a video. Optional `Idempotency-Key` header (1 to 255 characters) replays the first response for 24 hours, so retries do not create duplicates.
- `GET /v3/videos/{video_id}`: `status` is `pending`, `processing`, `completed` or `failed`; `video_url` when completed; `failure_code` and `failure_message` when failed.

## Controls and where they work

| Control | Field | Works on |
|---|---|---|
| Gesture and body movement | `motion_prompt` | Photo avatars; video avatars only on Avatar V. Rejected for video avatars on Avatar IV, and for photo avatars with no Avatar V-eligible look when using Avatar V |
| Energy and range of movement | `expressiveness`: `low` (default), `medium`, `high` | Photo avatars; not on Avatar V |
| More natural blinking | `engine.more_blinking` | Avatar V |
| Motion reference | `engine.reference_look_id` | Avatar V; a digital twin look in the same group |
| Pace and pitch | `voice_settings.speed` (0.5 to 1.5), `voice_settings.pitch` (-50 to 50) | Script plus voice, not uploaded audio |
| Pronunciation | `brand_glossary_id` | Text-to-speech audio |

There is no emotion field: emotion has to come from the words, the pace and the gesture.

Avatar V is opt-in per look: use it only when `avatar_v` appears in the look's `supported_api_engines`.
