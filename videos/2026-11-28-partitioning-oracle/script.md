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
