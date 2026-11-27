# Invisible Salamanders: v2 script, fact-checked

Every line below has been checked against the original sources (papers read
in full on 2026-11-27).

| Line (voiceover) | Verified by |
|---|---|
| One encrypted file, two keys, two different files, both "genuine" | [1] §3: "decrypts to an abusive attachment via one key and an innocuous attachment via another" |
| AES-GCM is in TLS (behind HTTPS) | [3] slide 5: AE is the "core of protocols like TLS, IPSec, SSH" (GCM, ChaCha20/Poly1305) |
| Tag = seal only the key holder can make; one flipped bit breaks it | [3] slide 11: with a hidden random key you "can't change contents (integrity)" |
| Seal only stops outsiders; never promised one key → "key commitment" | [2] abstract: "AE schemes do not guarantee key commitment as it is not part of AE's design goal" |
| Attacker picks both keys → one ciphertext valid under A and B | [1] §3, Collide-GCM: "computing the tags for the two keys then solving a linear equation to find the value of the last ciphertext block" |
| 2022 tool: PDFs, Windows programs, medical images | [2] abstract: "a tool that constructs AES-GCM ciphertext which can be decrypted to two plaintexts valid under … PDF, Windows executables, and DICOM" |
| 2018, Facebook Messenger, abusive image couldn't be reported | [1] §1: "the report will only include the non-abusive image" |
| Facebook paid a bug bounty | [1] §1: "led them to patch their (server-side) systems and to award us a bug bounty" |
| Fix: key-committing encryption | [1] §3 and [2] (generic and AES-GCM-specific commitment fixes) |

## Extra verified facts (optional for a v3)
- **Where the name comes from:** "messages in Secret Conversations are called
  'salamanders' by Facebook … ensuring Facebook does not see a message
  essentially makes it an invisible salamander." [1] §3
- **The proof-of-concept images:** the recipient saw an axolotl
  (salamander) image, but the abuse report showed **a kitten** instead.
  [1] Fig. 3
- **How Facebook fixed it:** a server-side patch so reports containing
  attachments are no longer deduplicated by attachment ID. The client still
  uses GCM. [1] §3
- **The 2022 authors:** Google Security Engineering Research, plus Shay Gueron
  (University of Haifa and Amazon). [2]

## Sources
1. Dodis, Grubbs, Ristenpart, Woodage. *Fast Message Franking: From Invisible
   Salamanders to Encryptment.* CRYPTO 2018. Full version from the author's own
   page: https://cs.nyu.edu/~dodis/ps/encryptment.pdf (also
   https://eprint.iacr.org/2019/016)
2. Albertini, Duong, Gueron, Kölbl, Luykx, Schmieg. *How to Abuse and Fix
   Authenticated Encryption Without Key Commitment.* USENIX Security 2022.
   https://www.usenix.org/system/files/sec22-albertini.pdf
3. P. Grubbs. *Hunting Invisible Salamanders.* Black Hat USA 2020 slides.
   https://i.blackhat.com/USA-20/Thursday/us-20-Grubbs-Hunting-Invisible-Salamanders-Cryptographic-Insecurity-With-Attacker-Controlled-Keys.pdf

## v3 changes (all verified, see "Extra verified facts" above)
- Payoff scene: "In their demo, the recipient got a picture of a salamander…
  but the abuse report showed a kitten. Facebook called its secret chat
  messages salamanders. So this one became… an invisible salamander. Facebook
  patched it, and paid a bug bounty." [1] §1, §3, Fig. 3
- Brand watermark "◆ 0xLore" (top right) and cover.jpg.

## YouTube metadata (v3)
- **Title:** One Encrypted File. Two Secrets. 🦎
- **Description:**
  The recipient saw a salamander. Facebook's abuse report saw a kitten.
  Same encrypted file. 🤯

  AES-GCM, the encryption inside TLS, never promised that a ciphertext
  belongs to just one key. Researchers used that gap to make Facebook
  Messenger attachments that couldn't be reported. It's called "Invisible
  Salamanders".

  📄 Sources
  • Dodis, Grubbs, Ristenpart, Woodage. "Fast Message Franking: From Invisible
    Salamanders to Encryptment", CRYPTO 2018
  • Albertini et al. "How to Abuse and Fix Authenticated Encryption Without
    Key Commitment", USENIX Security 2022

  Follow 0xLore for more hidden gems of cybersecurity.
  #cybersecurity #cryptography #infosec #encryption #shorts
- **Tags:** cybersecurity, cryptography, AES-GCM, encryption, infosec,
  key commitment, invisible salamanders, facebook messenger
- **Settings:** type short, madeForKids false, category SCIENCE_TECHNOLOGY,
  cover = cover.jpg
