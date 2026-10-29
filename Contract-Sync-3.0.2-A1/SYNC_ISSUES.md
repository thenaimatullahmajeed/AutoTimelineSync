# Proposed sync corrections — shared A text retained verbatim

The supplied V5.2.2, V5.2.3 patch and final RICH JSON were read. This is a correction list for the master-prompt owner, not an edit to the shared block. Code wins over a mislabeled hard rule.

| Where | Master prompt/patch says | Verified code behavior | Proposed fix | Owner |
|---|---|---|---|---|
| 00A A; shared 7 | frames legal only on non-cuts | Integer 4 to 30 is validated even on a cut; renderer then ignores cut frames | Keep non-cut-only authoring as HOUSE RULE | ChatGPT |
| 00A A | Only three generic presets accept animation | Off also accepts valid animation values; only the six creator presets reject field presence | Correct the accepted list; Off renders nothing | ChatGPT |
| 00A A | PHOTO_NOTE corners must be TL/TR/BR/BL | Exactly four convex perimeter corners in either orientation pass; named corner order is not inspected | Fixed TL/TR/BR/BL order is HOUSE RULE | ChatGPT |
| 00A B | word range outside the scene causes a moment skip | Scene containment applies to CIRCLE; DATE_CARD has no scene field or per-scene containment check | Specify CIRCLE for that skip condition | ChatGPT |
| V5.2.2 33 frame formula, retained by the patch | Default frames ROUND_HALF_UP; explicit available frames include floor of 0.55 times fps | Nominal transition defaults use Python round; explicit fitting uses 45 percent of shorter neighbor and incoming length minus one, without that 0.55-second cap | Correct formula; scene/word timeline frame conversion still uses decimal half-up | ChatGPT |
| Shared 7; 00A A seed | Wider parse-only seed range and later error without a path | Installed baseline behaves that way; candidate D3 rejects early at $.style.seed with the newly approved exact message | B and the new error are active in the final portable app; mirror them in the master chat | Codex and ChatGPT |
| 00A G motion aliases | IMPACT_PUNCH_IN, SLOW_PULL_OUT, STATIC_HOLD undocumented; SUBTLE_PARALLAX forbidden | Aliases resolve to TINY_PUNCH_IN, SLOW_ZOOM_OUT, STATIC; parallax falls back to 2D push with warnings | Document accepted aliases; prefer canonical names. Parallax omission is HOUSE RULE, not a schema rejection | ChatGPT |
| 00A E fonts | Specific accepted fonts cannot cover scripts generally | Native sample glyph coverage was tested; fallback can display characters. Layout certification is separate | State native tested coverage/fallback distinction; keep creator RTL warning and uncertified RTL status | ChatGPT |
| Shared 5 classification | no repeated type on consecutive non-cuts | New classifier needs a precise sequence interpretation | Proposed: adjacent timeline boundaries that are both non-cuts; an intervening cut breaks the sequence | Codex and ChatGPT |
| Shared 5 classification | STANDARD/RICH/MAX thresholds with no precedence for overlapping small counts | The original app had no classifier. The B portable build checks MAX, then RICH, then STANDARD; zero boundaries means NONE | Mirror precedence in both chats; it is diagnostic policy, not renderer behavior | Codex and ChatGPT |
| Character-fit request | Maximum characters per line implied | No code limit; shaping, preset, font size, wrapping and automatic shrink determine fit | Use the explicitly measured advisory table and inspect actual captions, not a universal guaranteed maximum | Codex and ChatGPT |
| RICH acceptance sample vs every-spoken-year HOUSE RULE | Three date cards expected; every spoken date/year up to cap also requested | Final words include 1840, 1879, 1930 and 1895; cards cover the first three. Parser accepts this | Report the omitted 1895 as an authoring-policy discrepancy; retain supplied JSON unchanged for C2 | ChatGPT |
| DATE_CARD with caption position Center | Date cards should remain readable alongside centered captions | Actual exported 1840, 1879 and 1930 cards overlap centered Hindi captions; the 1879 card is heavily obscured | Author Bottom captions for such a package, or approve a separate renderer collision-avoidance plan. D6 forbids silently changing rendering | ChatGPT or Codex after separate approval |

Exact exchange syntax:

`SYNC ISSUE | where | what the master prompt says | what the tool does | proposed fix | owner`

Fancy and subtle enum sets exactly match the shared A lists. RICH/MAX budgets are creative rules and never become rejection rules. Copy text first two lines are unchanged. Universal Arabic/Urdu rendering, dynamic error-template completeness, GPU and Android remain UNKNOWN.
