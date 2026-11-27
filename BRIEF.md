# Production brief

## Goal
Daily YouTube Shorts (2–3 a day) that teach lesser-known cybersecurity
concepts. Each video teaches one real concept.

## Audience
Beginner-friendly: a security beginner must be able to follow every video.
Still technical enough that a security engineer learns the real mechanism.
- Use everyday analogies first (a door opening, twenty questions, a wax seal),
  then the real term once (for example "a door: really, a network port").
- At most two technical terms per video, each defined on screen.
- One idea per scene. No jargon chains.

## Topics
- Hidden gems only. Avoid well-known topics such as confused deputy, SQLi, XSS,
  phishing and Stuxnet.
- Concept first. Real incidents appear only as a short payoff at the end.
- Backlog: Partitioning Oracle attacks, WorstFit (CVE-2024-4577), Psychic
  Signatures (CVE-2022-21449), Unicode case-mapping collisions.
- Done: Invisible Salamanders (scheduled 2026-11-28 16:00 IST).

## Accuracy (strict)
- Every claim is checked against primary sources (papers, CVE advisories,
  vendor docs), fetched only from official or author-hosted copies.
- Sources are listed in each video's script.md.
- No assumptions and no invented stories. If a claim can't be verified, it's left out.

## Storytelling
- Format: cartoon characters Rio and Mina talk on the rooftop; a glowing screen
  rises for diagram moments.
- Not a textbook reading. Hook with stakes → open question → basics → twist →
  mechanism → real-world payoff → fix → CTA ("Follow for more hidden gems").
- Keep open loops, use short punchy lines and pauses, and put sound cues on twists.
- 60–90 s.

## Visual style
- 1080×1920, 30 fps, H.264 MP4. Dark navy background, faint grid, glowing
  yellow diagrams.
- Bold captions word by word: white, with the key word in yellow.
- Progress bar at the top. "◆ 0xLore" brand watermark top-right; no topic header.
- Cover image (cover.jpg) for every Short, branded 0xLore.
- AI voiceover. Music must be royalty-free or generated in code.

## Posting schedule (YouTube, Asia/Calcutta)
Based on Metricool's best-time data for the channel (checked 2026-11-28):
- 2 a day: **10:00** and **16:00**
- 3 a day: **10:00**, **13:00**, **16:00**
- Weekdays are much stronger than weekends. The 16:00 slot peaks every day.

## Published log
| Date (IST) | Topic | Metricool post |
|---|---|---|
| 2026-11-28 16:00 | Invisible Salamanders (v3) | id 444814380 |

## Production QA checklist (every video, before it's sent for review)
1. **Before writing:** one-paragraph mechanism summary from the source. Every
   scene and visual must match it, not just every sentence.
2. **Automatic checks in the renderer (the render aborts on failure):** text
   inside the safe zone (x 40–1040, y 250–1540), captions fit (auto-shrink), no
   overlay flicker, no empty diagram screen over 0.25 s, hook within 1.5 s,
   end tail ≤ 1.8 s, length ≤ 90 s.
3. **Output format:** 1080×1920 9:16, SAR 1:1, 30 fps, H.264 yuv420p (high
   profile), AAC 48 kHz stereo, −14 LUFS (±1). Cover 1080×1920, with its text
   inside the centre 4:5 crop.
4. **After rendering:** review one frame per second. Check that the title and
   cover don't overclaim, and that the facts in the visuals match the sources.
   Send the QA results with the video.

## Platform safe zones (Shorts / Reels)
- Top ~250 px: status bar and search/menu icons. Only the watermark (top
  centre) goes here.
- Bottom ~380 px: channel name, caption text, sound/remix bar. Characters' feet
  can go here; never text.
- Right ~140 px of the lower half: like/comment/share buttons.
