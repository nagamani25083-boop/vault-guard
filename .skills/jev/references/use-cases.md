# Worked Examples

## The lesson that shapes every Jev integration

The first attempt at a real Jev product was a "coach" that would tell the user what to say next.
It failed for a structural reason: **Jev cannot generate strings.** Asking it to write a reply is
asking for the one thing it does not do.

The same feature worked immediately once it was turned around. Instead of writing the reply, Jev
**judges the reply the user already wrote**:

| Turned into a judge | Result |
| --- | --- |
| Draft: *"just tell your boss you can't finish it"* | score **28/100**, emotion-fit 21, hit *"gives advice before acknowledging the feeling"* at 0.94 |
| Draft: *"getting handed work right at quitting time would set anyone off"* | score **75/100**, emotion-fit 93, no hits |

Same model, same conversation, same rubric — the only change was which side of the decision Jev
sits on. **Generate with an LLM if you need text; decide with Jev.** Every example below is a
variation on that.

## Case study: a conversation-analysis pipeline

An app watches a chat and annotates it live. Four layers, all built from named questions.

### Layer 1 — read one incoming message (5 questions, one request)

```json
{
  "state": {
    "relationship": "getting to know each other",
    "messages": [
      { "id": "0", "sender": "self", "text": "how was your day" },
      { "id": "1", "sender": "other", "text": "honestly pretty rough, my manager dumped work on me right before I left" }
    ]
  },
  "questions": {
    "emotions": {
      "type": "choice",
      "instructions": "Message ID 1, sender=other. Which emotion does it mainly express? Consider sarcasm and multi-meaning; return a distribution, do not rate intensity.",
      "criteria": {
        "sad": "sad, low, grieving",
        "annoyed": "fed up, wants it to stop",
        "disappointed": "expectation not met, let down",
        "teasing": "joking, ribbing, playing",
        "calm": "neutral statement, no clear emotion",
        "unknown": "cannot judge from this text"
      }
    },
    "intents": {
      "type": "choice",
      "instructions": "Message ID 1, sender=other. What is the main communicative intent? Treat the labels as competing readings of one message, not as simultaneous components. Everyday answering and sharing are valid intents; only pick a hidden motive when there is specific evidence.",
      "criteria": {
        "vent": "releasing frustration, not asking for a solution",
        "comfort_seek": "showing vulnerability to get emotional support",
        "share": "reporting their own day",
        "ask": "requesting information",
        "unknown": "cannot judge"
      }
    },
    "openQuestion": {
      "type": "noul",
      "instructions": "Message ID 1. Does it contain a specific, still-unanswered question or expectation that deserves a real answer? Small talk and statements that need no reply are false.",
      "criteria": { "true": "an unanswered question or expectation", "false": "nothing to answer" }
    }
  }
}
```

Returns: `emotions` → *sad 0.59 / annoyed 0.40*, `intents` → *vent 0.82 / comfort_seek 0.15*,
`openQuestion` → `0.36`.

Note the shape of the asks: **competing labels**, an explicit escape hatch, an instruction about
sarcasm, and a probability rather than a verdict. All four matter — drop any one and the answer
gets worse, not shorter.

### Layer 2 — the whole-conversation state (17 questions, still one request)

Six dimensions, each asked twice — once as a rubric and once as "is there enough evidence here?":

```json
{
  "engagement": {
    "type": "score",
    "instructions": "Did the other person engage with the specific things self said? Terse replies and slow replies are not by themselves negative.",
    "criteria": [
      "ignored or belittled what self said",
      "repeatedly dodged the point or answered perfunctorily",
      "answered normally, kept the thread going",
      "picked up details, caught the joke, or developed self's topic",
      "consistently worked at understanding self and followed up on earlier specifics"
    ]
  },
  "engagement_enough": {
    "type": "choice",
    "instructions": "Was there enough evidence to judge engagement? A scene that never came up is not negative evidence.",
    "criteria": {
      "sufficient": "clear evidence either way",
      "limited": "a rough read is possible but ambiguity remains",
      "insufficient": "not enough text"
    }
  }
}
```

The `_enough` twin is what makes the score safe to display. Without it, "no evidence" and "evidence
of a problem" render identically. With it, the UI can show *insufficient* instead of a fake number —
in practice roughly half the dimensions read `insufficient` on a short conversation, and that is the
correct output, not a bug.

The same request also carries the gates and the recommendation:

```json
{
  "boundary": {
    "type": "noul",
    "instructions": "Has the other person stated a refusal to be pursued that is still in effect? A withdrawal of an earlier refusal does not count; being busy once does not count as refusing a relationship."
  },
  "pending": {
    "type": "noul",
    "instructions": "Is the last message from self, still unanswered, so that waiting is better than sending again?"
  },
  "action": {
    "type": "choice",
    "instructions": "At the end of this conversation, what should self do next?",
    "criteria": {
      "continue": "keep the current thread going",
      "empathize": "respond to the feeling before anything else",
      "ask": "ask one specific, light question",
      "wait": "the ball is with the other person, do not send again",
      "respect": "a boundary was expressed; stop pushing",
      "insufficient": "not enough context to advise"
    }
  }
}
```

Measured cost of this layer: **17 questions, ~379 ms, ~6k input tokens** in a single call. Batching
the dimensions into one request is the whole reason this is affordable.

**Application-side rules that came out of this layer:**

- `boundary >= 0.8` **caps the aggregate score**, so a warm earlier conversation can never mask a
  current, explicit refusal. A hard gate on a soft number; check it before displaying anything.
- `pending >= 0.75` **overrides the recommended action to "wait"**, no matter what the other options
  scored. Timing beats content.
- `confidence < 0.35` on the action question is rendered as *"not enough context"* rather than being
  snapped to the highest-scoring branch.

### Layer 3 — judge what the user already sent

The same five "hit" checks used in Layer 4, plus how the message actually landed:

```json
{
  "effect": {
    "type": "choice",
    "instructions": "What did the last self message actually do? Judge from visible replies only; if the other person has not replied yet, pick the most likely effect and do not assume an unseen response.",
    "criteria": {
      "landed": "caught what the other person just said or felt",
      "extended": "added something that gives the conversation a next step",
      "flat": "safe but generic, no movement",
      "closed": "the thread ends here, nothing to pick up",
      "diverted": "changed the subject without catching what was said",
      "pressured": "rushed, interrogated, or demanded a response",
      "overstepped": "ignored a boundary the other person expressed"
    }
  }
}
```

### Layer 4 — check a draft *before* it is sent

The five reusable hit checks, each a `noul` over the same state with the draft attached:

| Question name | Asks |
| --- | --- |
| `ignoresTopic` | does the draft avoid what the other person just said? |
| `mismatchedHeat` | is the draft much hotter or much colder than the other person's energy? |
| `closesTopic` | does it end the thread with nothing to reply to? |
| `pressure` | does it push for a meeting, an answer, or someone's whereabouts without the ground for it? |
| `adviceFirst` | when the other person is venting, does it give advice before acknowledging the feeling? |

Report these as a checklist with probabilities, not as a single score. And keep the verdict
**separate** from the decision to send:

```json
{
  "score": { "type": "score", "criteria": ["...5 quality levels..."] },
  "sendNow": {
    "type": "noul",
    "instructions": "Is now a good moment to send this? Timing only — do not judge how well it is written. It is usually fine when the other person just spoke; it is usually not fine when self sent the last message and it is still unanswered, or the other person is winding down and wants to rest."
  }
}
```

A well-written message at the wrong moment shows **high quality + low `sendNow`**. That is two facts,
and the UI must show two facts.

## Two application bugs worth not repeating

1. **Folding two judgments into one number.** `if (sendNow < 0.85) score = min(score, 55)` made every
   good draft score exactly 55. See
   [question-types.md](question-types.md#one-score-can-only-carry-one-meaning).
2. **A stale verdict outliving its input.** A result that came back after the input was edited was
   written back unconditionally, so the new text kept an old verdict forever. Fix by comparing the
   input against what was sent before writing the answer back.

## Smaller patterns

### Route, don't classify twice

One `choice` whose labels are the branches beats a chain of yes/no questions: one request, one
distribution, and the runner-up branch is visible for free.

```json
{
  "route": {
    "type": "choice",
    "instructions": "Which handler should process this request?",
    "criteria": {
      "refund": "a payment that must be reversed",
      "billing_question": "asks about a charge but wants no action",
      "technical": "a product defect or how-to",
      "other": "none of the handlers fit"
    }
  }
}
```

Branch on `route`, and treat `confidence < 0.5` as the `other` branch.

### Extraction without generation

Ask for a `choice` over candidate values rather than free text. To pull a date out of a sentence,
either enumerate the plausible values you can already see, or ask one `noul` per candidate:

```json
{
  "is_this_week": { "type": "noul", "instructions": "Does the message refer to a date within this week?" }
}
```

### Guardrail before an irreversible action

Score the action itself, then gate on the low end of the rubric:

```json
{
  "safety": {
    "type": "score",
    "instructions": "Would sending this message violate something the other person asked for?",
    "criteria": [
      "explicitly violates a stated request",
      "likely crosses a line the other person drew",
      "unclear whether it crosses a line",
      "respects everything the other person has said",
      "actively protects the other person's stated boundary"
    ]
  }
}
```

Act only above 3, ask the user between 2 and 3, refuse below 2. Never auto-resolve a boundary
question on a low-confidence answer.
