# Day 08 — Memory & personalization v1

## Goal
Improve relevance using preferences and feedback.

## Deliverables
- Feedback capture (click/like/dislike)
- Ranking uses feedback + preferences

## TODO
- [ ] Feedback endpoint + storage
- [ ] Update ranking weights (preferred domains/sources/topics)
- [ ] Add diversity constraint (avoid same-domain overload)

## Acceptance checks
- Disliked domains decrease in future selections
- Output is more diverse across sources/domains
