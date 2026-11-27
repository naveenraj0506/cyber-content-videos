# Partitioning Oracle Attacks: v3 (final candidate)

## Mechanism summary (every scene must match this)
The Shadowsocks server silently drops packets it can't decrypt, but opens a UDP
port when decryption works, and the attacker can detect that port. AES-GCM
isn't key-committing, so one packet can decrypt under 4,091 password-derived
keys. Port closed → all 4,091 crossed off. Port open → the password is in that
batch, and the attacker finds it by offline trial decryption of the reply.
Simulations: 1 in 5 passwords recovered with 124 packets vs ~60,000 for plain
guessing. (Len, Grubbs, Ristenpart, USENIX Security 2021, §1, §4.)

## v3.1 changes
- Clarified that it's network encryption: a password shared by client and proxy is hashed into a symmetric secret key that encrypts the traffic (§4: "password-based AEAD with a user-chosen password shared between a client and the proxy server"; "hashing the user password to obtain a key"). It's not a private key or an app login.
- New line: the attack works because passwords are guessable, and the attacker orders batches by likelihood using breach data (§4: subsets with "maximum aggregate probability"; training on breach data).
- QA re-run: PASS; 75.8 s; −14.1 LUFS; 9:16.

## Changes from v2 (review findings)
- Accuracy: removed the "split in half / twenty questions" section. The 124-try
  result comes from 4,091-password batches plus offline checking, not halving.
- Title no longer overclaims (1 in 5, not every password).
- Hook: "4,091" lands at 0.2 s (was 6 s).
- Text kept inside the Shorts/Reels safe zone (x 40–1040, y 250–1540); captions
  auto-shrink to fit.
- No flicker or empty screens (checked automatically); stats rows show from
  the start of the line.
- Loudness normalised to −14 LUFS; stereo 48 kHz; square pixels; 9:16.
- End tail cut to 1.4 s; Mina's expressions are friendlier (smirk on the twist).

## Lines
| # | Who | Line |
|---|-----|------|
| 1 | Mina | 4,091 passwords… in one try. Want to see how? |
| 2 | Rio | Online? No way. That's one guess per try. |
| 3 | Mina | Picture a proxy server, kind of like a VPN. You and the server share a password, and it becomes the secret key that encrypts your traffic. Send a packet locked with the wrong password… and it says nothing. No error. Just silence. |
| 4 | Rio | So I can't even tell if I'm close. |
| 5 | Mina | But send the right one, and the server quietly opens a door to wait for a reply. You can see that door from outside. That's a leak. A simple yes or no. |
| 6 | Mina | Now the twist. Some encryption, like AES-GCM, lets you build one message that unlocks with thousands of passwords. |
| 7 | Rio | Wait. One message… thousands of passwords? |
| 8 | Mina | 4,091 of them. Door stays shut? All 4,091 are wrong. Crossed off in one go. Door opens? The password is in that batch, and the attacker finds it offline. |
| 8b | Mina | And it works because people pick guessable passwords. The attacker tests the most common ones first. |
| 9 | Rio | Does that actually work? |
| 10 | Mina | In simulations with real leaked passwords, one in five was cracked in just 124 tries. Normal guessing? Around 60,000. |
| 11 | Mina | It's called a partitioning oracle attack. Researchers found it in a real proxy tool, Shadowsocks, and helped fix it. |
| 12 | Rio | Follow 0xLore for more hidden gems. |

## QA results (v3)
- Pre-render checks passed: safe zone, captions fit, no flicker, no empty
  screens, hook within 1.5 s, end tail ≤ 1.8 s, under 90 s.
- Post-render: 1080×1920, SAR 1:1, DAR 9:16, 30 fps, H.264 yuv420p; AAC 48 kHz
  stereo; −14.2 LUFS integrated, −3.2 dBFS peak; 64.9 s.
- Reviewed one frame per second: no overlaps or clipping.

## YouTube metadata (v3)
- **Title:** 1 in 5 Passwords Cracked in 124 Tries 🔓
- **Description:**
  The server never says "wrong password". It doesn't need to. 🤫

  Shadowsocks, a VPN-like proxy, encrypts traffic with a key made from a shared
  password. It stays silent when the password is wrong, but quietly opens a door
  (a network port) when it's right. With AES-GCM, one message can test 4,091
  passwords at once. In simulations with real leaked passwords, 1 in 5 were
  cracked in just 124 tries. Normal guessing needed ~60,000.

  📄 Source
  • Len, Grubbs, Ristenpart. "Partitioning Oracle Attacks", USENIX Security 2021

  Follow 0xLore for more hidden gems of cybersecurity.
  #cybersecurity #infosec #passwords #encryption #shorts
- **Tags:** cybersecurity, partitioning oracle, passwords, AES-GCM, shadowsocks,
  encryption, infosec, hacking explained
- **Settings:** type short, madeForKids false, category SCIENCE_TECHNOLOGY,
  cover = cover.jpg

---
(older versions kept below for reference)

# Partitioning Oracle Attacks: script v2 (beginner-friendly, rendered)

Simplified after feedback: no ciphertext/oracle theory up front. The port is a
"door", and the halving is "twenty questions". Facts unchanged, all from
Len, Grubbs, Ristenpart, USENIX Security 2021.

| # | Who | Line | Source |
|---|-----|------|--------|
| 1 | Rio | Guessing a password online is slow. One guess… one try. | general |
| 2 | Mina | What if one try could test 4,091 passwords at once? | §4: k = 4,091 (UDP size limit) |
| 3 | Mina | Server hides behind a password; wrong one → says nothing. No error. Just silence. | §4: "If decryption fails, no error message is sent back" |
| 4 | Rio | So I can't even tell if I'm close. | — |
| 5 | Mina | Right one → server opens a door (network port) to wait for a reply; visible from outside; a yes/no leak. | §4: opens "an ephemeral UDP port in response to a valid request (and does not otherwise)" |
| 6 | Mina | Some encryption, like AES-GCM, lets you build one message that unlocks with thousands of passwords. | Abstract and §3: key multi-collisions for AES-GCM |
| 7 | Rio | One message, thousands of passwords? | — |
| 8 | Mina | 4,091 of them. Door shut → all wrong. Door opens → password in group, split in half, try again. | §2 and §4: iterate on the remaining passwords |
| 9 | Mina | Like twenty questions: every answer cuts the list in half. | §2: "a simple adaptive binary search" |
| 10 | Mina | Simulations with real leaked passwords: 1 in 5 cracked in 124 tries; normal guessing ~60,000. | §1 |
| 11 | Mina | Called a partitioning oracle attack. Found in Shadowsocks, and the researchers helped fix it. | Title; §1: "responsibly disclosed … worked with them to help mitigate" |
| 12 | Rio | Follow 0xLore for more hidden gems. | — |

---
(v1, kept for reference)

# Partitioning Oracle Attacks: script v1 (for review)

**Style:** a mix of the two looks. Cartoon scenes with Rio and Mina carry the
story; glowing diagram panels explain the mechanism. 0xLore watermark.
**Target length:** about 80 s. **Voices:** Rio = male, Mina = female.

`[C]` = cartoon scene (rooftop / server room) · `[D]` = diagram overlay
Every fact cites the paper in the Sources section below (§ = section).

| # | Who | Line | Visual | Source |
|---|-----|------|--------|--------|
| 1 | RIO `[C]` | "Guessing someone's password over the network? That's one guess per try. Thousands of tries." | Rio slumped, a counter ticking "1… 2… 3…" | general |
| 2 | MINA `[C]` | "Unless… every try tests *four thousand* passwords at once." | Mina smirks. **BOOM**, title flash | §4: k = 4,091 |
| 3 | MINA `[D]` | "Meet Shadowsocks: an encrypted proxy built to get around censorship. Your password becomes the key, and AES-GCM locks every packet." | Shadowsocks box; "password → hash → key"; packet with padlock | §1, §4 "Background" |
| 4 | MINA `[D]` | "Send a packet with the wrong key… and the server says nothing. No error. Silence." | Packet bounces into darkness, "…" | §4: "If decryption fails, no error message is sent back"; silent drop is an anti-probing countermeasure |
| 5 | RIO `[C]` | "So there's nothing to learn." | Rio shrugs | — |
| 6 | MINA `[D]` | "Almost. When decryption *works*, the server opens a port to wait for a reply. And an attacker can spot that port. A yes-or-no signal like that is called an *oracle*." | Port icon lights up; label "ORACLE = a yes/no leak" | §4: server "opens an ephemeral UDP port in response to a valid request (and does not otherwise)"; attacker scans for it |
| 7 | MINA `[C]` | "Now the twist. AES-GCM isn't key-committing. One ciphertext can be valid under *many* keys at once." | Callback card: "remember the invisible salamanders?" | Abstract: partitioning oracles "arise when encryption schemes are not committing"; key multi-collisions for AES-GCM |
| 8 | RIO `[C]` | "How many?" | Rio leans in | — |
| 9 | MINA `[D]` | "For Shadowsocks? *Four thousand ninety-one* passwords in one packet. Built in *thirty-two seconds*." | 1 packet → grid of 4,091 key icons; timer "32 s" | §4: UDP limit 65,507 bytes → "k = 4,091"; "took 32 seconds … offline pre-computation" |
| 10 | MINA `[D]` | "Port stays closed? All four thousand are wrong, gone in one shot. Port opens? The password is in that group, so split it again… and again." | Key grid turns red ✘ / one group splits in half repeatedly | §2: oracle says whether the key is in a subset; §4: "focusing iteratively on the set of remaining passwords" |
| 11 | MINA `[D]` | "That's a *partitioning oracle attack*. Every answer cuts the haystack." | Banner: PARTITIONING ORACLE ATTACK | paper title / §1 |
| 12 | RIO `[C]` | "Okay, but does it work for real?" | — | — |
| 13 | MINA `[D]` | "In simulations with real leaked passwords, one in five fell after just *124* packets. Plain guessing needed around *sixty thousand*." | Bar chart 124 vs ~60,000 | §1: "20% of the time the attacker recovers the user's password by sending 124 ciphertexts … ∼60,000 required by a standard remote guessing attack" |
| 14 | MINA `[C]` | "The Cornell Tech researchers disclosed it and helped the Shadowsocks community fix it." | Handshake / patch icon | §1: "responsibly disclosed our attacks to the Shadowsocks community, and worked with them to help mitigate" |
| 15 | MINA `[C]` | "The fix? Once again: *key-committing* encryption." | ✔ key-committing AEAD | Abstract: "standardize and make widely available key-committing AEAD" |
| 16 | RIO `[C]` | "Follow 0xLore for more hidden gems." | End card | — |

## What I left out
- The OPAQUE part of the paper. It's true: a majority of the surveyed prototype
  OPAQUE implementations used non-committing AEAD. But it would push the
  video past 90 s and needs its own explanation of PAKE.
- Port-scan details: the ephemeral range 49,152–65,535 and the port staying
  open five minutes. Accurate (§4), but too much detail for a Short.

## Sources
1. Julia Len, Paul Grubbs, Thomas Ristenpart (Cornell Tech). *Partitioning
   Oracle Attacks.* USENIX Security 2021.
   https://www.usenix.org/system/files/sec21-len.pdf
2. Background on key commitment: Albertini et al., USENIX Security 2022,
   https://www.usenix.org/system/files/sec22-albertini.pdf (see previous video)

## Draft packaging
- **Title:** 124 Packets to Crack a Password 🔓
- **Cover:** "4,091 PASSWORDS. ONE PACKET." with Rio looking shocked, a
  packet icon fanning out into keys, and the 0xLore brand.
- **Description hook:** "The server never says 'wrong password'. It doesn't
  need to." Then sources and hashtags.

## Final YouTube metadata (v1 render)
- **Title:** 124 Tries to Crack a Password 🔓
- **Description:**
  The server never says "wrong password". It doesn't need to. 🤫

  Shadowsocks silently drops bad packets, but it opens a port when decryption
  works. Because AES-GCM isn't key-committing, one packet can be valid for
  4,091 passwords at once. Each answer cuts the haystack. In simulations with
  real leaked passwords, 1 in 5 were cracked in just 124 tries.

  📄 Source
  • Len, Grubbs, Ristenpart. "Partitioning Oracle Attacks", USENIX Security 2021

  Follow 0xLore for more hidden gems of cybersecurity.
  #cybersecurity #cryptography #infosec #passwords #shorts
- **Tags:** cybersecurity, cryptography, partitioning oracle, AES-GCM,
  shadowsocks, password cracking, key commitment, infosec
- **Settings:** type short, madeForKids false, category SCIENCE_TECHNOLOGY,
  cover = cover.jpg
