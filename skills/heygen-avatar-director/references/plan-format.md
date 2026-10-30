# Direction plan format

One JSON file per video. Top-level settings apply to every beat; a beat can override `engine`, `avatar_id`, `voice_id`, `speed`, `pitch` and `more_blinking`.

```json
{
  "title": "Product intro",
  "avatar_id": "LOOK_ID",
  "avatar_type": "photo_avatar",
  "voice_id": "VOICE_ID",
  "engine": "avatar_iv",
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "fit": "cover",
  "voice_settings": { "speed": 1.0, "pitch": 0, "locale": "en-US" },
  "more_blinking": true,
  "beats": [
    {
      "id": "b1",
      "script": "One or more short sentences.",
      "motion_prompt": "small open-palm gesture toward the camera on 'you', then hands rest",
      "expressiveness": "medium",
      "speed": 0.97
    }
  ]
}
```

| Field | Where | Notes |
|---|---|---|
| `avatar_id` | top or beat | A look id from `heygen.py looks` |
| `avatar_type` | top | `photo_avatar`, `digital_twin` or `studio_avatar`. Lets the dry run catch settings the engine would reject |
| `voice_id` | top or beat | Optional if the look has a default voice |
| `engine` | top or beat | `avatar_v`, `avatar_iv` (HeyGen's default) or `avatar_iii`. Check the look's `supported_api_engines` |
| `motion_prompt` | beat | Gesture and body movement in plain words. Rejected on Avatar IV for video avatars |
| `expressiveness` | beat | `low`, `medium`, `high`. Photo avatars only; not on Avatar V |
| `speed` | top (`voice_settings`) or beat | 0.5 to 1.5, default 1 |
| `pitch` | top (`voice_settings`) or beat | -50 to 50 |
| `more_blinking` | top or beat | Avatar V only |
| `reference_look_id` | top | Avatar V only: a digital twin look in the same group to use as the motion reference |
| `fit`, `background`, `remove_background` | top | Passed through unchanged; keep them the same for every beat so joins do not jump |

`heygen.py render plan.json --dry-run` prints the exact request for each beat and explains anything it dropped.
