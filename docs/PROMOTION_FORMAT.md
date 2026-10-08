# Projector → Harness promotion format (v1)

This closes the open question in Harness Conceptual Contract §11 ("exact file format for
promotion payload"). A future Harness for AREA512 reads these files. Every field maps onto the
contract's Live Goal Data Model (§4) without translation.

## Why a line format, not JSON

AREA512's MicroPython has no `json` module and no `import`. The format is plain ASCII lines that
`str.split` can parse:
- `key: value` lines (split once on `": "`)
- `KIND|field|field...` record lines (split on `|`)

Projector never writes `|` or a newline inside a value: it replaces `|` with `/`, and its text
entry can't type a newline. Money is in **whole currency units** (integers). Durations are in months
and estimates in minutes.

## Where

    /Area512_data/data/harness/inbox/goal-<projector id>.txt

Harness should treat the inbox as **arrivals**. On start-up, if a file is there, it shows the
charter, asks "Ready to begin execution?", and then moves the file into its own state. Projector
never writes to Harness's state directly, and never edits a goal after promoting it.

## Goal file

    HARNESS-GOAL 1
    source: projector
    source_id: 3
    title: Corner cafe
    wish: Open a small coffee shop in my town                 # Charter: Wish
    outcome: 200 regulars a week and I pay myself 3k a month  # Charter: Outcome / Proof
    obstacle: I lose nerve when money gets tight              # Charter: Main Internal Obstacle
    ifthen: When the balance drops below 1k, I will call ...  # Charter: If-Then Plan
    why: I want a place people come back to                   # motivation, for the WOOP ritual
    window_months: 36                                         # Charter: success window
    money_baseline: 5000                                      # Money: starting figure
    money_projected: 31400                                    # Money: likely-case end of the projection
    TASK|next|Call 3 landlords about rent|3 quotes written down||45|||
    TASK|inbox|Build||||||6 months, -$2.0k a month
    ASSUME|unchecked|People here will pay $5 for coffee
    IFTHEN|Cash runs out in month 6, likely case|cut hours and sell beans online
    JUDGE|3|2|3|a place I'm proud of

### `key: value` lines

| Key | Required | Contract field |
|---|---|---|
| `wish`, `outcome`, `obstacle`, `ifthen` | yes | §4.1 Charter |
| `window_months` | no | §4.1 optional target window (months, not a date: AREA512 has no clock) |
| `money_baseline` | no | §4.3 current balance / runway |
| `money_projected` | no | §4.3 optional target. This is the user's own projection, so Harness should label it "projected", not "target", until the user accepts it |
| `why`, `title`, `source`, `source_id` | no | context |

### `TASK|status|title|done_when|est_low|est_base|est_high|money|note`

These are §4.2 Tasks. Projector writes:
- exactly one `next` task: the first action, with its Definition of Done and a base estimate in minutes;
- optionally one `inbox` task per stage (seed tasks), with no Definition of Done. Harness plans them in Plan mode.

Empty fields are empty strings. Projector never invents an estimate.

### `ASSUME|checked|text` / `ASSUME|unchecked|text`

These are the key assumptions for Review (§7, optional payload). Unchecked ones are the ones Review should bring back.

### `IFTHEN|crack|response`

Each crack the user *faced* rather than fixed, with their own response. They are extra implementation
intentions next to the charter's main If-Then. Harness can show them at the moment named
(for example, when the money crack's condition is true).

### `JUDGE|fruitful 1-5|feel 1-3|effort 1-3|worth it, in words`

This is the user's own judgment at promotion time. `feel` is 1 quick / 2 moderate / 3 dragged out;
`effort` is 1 easy / 2 medium / 3 hard. Empty if the user skipped it.

## Versioning

The first line names the version. A reader should ignore unknown keys and unknown record kinds,
and refuse a higher major version.

## Idea file (Projector's own, for reference)

`/Area512_data/data/projector/ideas/<id>.txt` uses the same conventions:

    PROJECTOR-IDEA 1
    title / status / touched / wish / picture / why / window / cash / obstacle / ifthen /
    note / fruit / feel / effort / worth / task / done / minutes      (key: value)
    S|name|months|net per month|conf 1-3|diff 1-3                     stage
    A|0 or 1 (checked)|text                                          assumption
    F|crack key|response                                             a faced crack

`touched` is a session number, not a date (`meta.txt` counts launches).
`library.txt` holds one line per idea, `id|status|touched|title`.
