# ADR 0008: Run automations synchronously with a thread-local loop guard

Status: Accepted  
Date: 2026-10-22 (written after the decision, see README)  
Related commits: `c4076e9`

## Context

Users can create automation rules: "when X happens to a task, do Y". The
actions of a rule can trigger other rules. For example: "when a task moves
to Done, set priority to low" and "when priority is set to low, move the
task to Done". Without protection, rules can trigger each other forever.

This was found during development: a rule moved a task, and the move
triggered the same rule again.

## Decision

- Rules run **synchronously** inside the request, through Django signals
  (`automations_api/receivers.py`).
- `engine.py` keeps a thread-local set of `(rule, task)` pairs that are
  running at the moment. Before a rule runs for a task, the engine checks
  this set. If the pair is already in it, the rule is skipped.
- Because everything is synchronous, a whole chain of rules runs nested in
  one call stack. So the guard also stops longer cycles, like
  A triggers B, B triggers A.

## Consequences

- No endless loops, without a fixed depth limit and without extra
  infrastructure.
- Each rule runs at most once per task in one chain. If someone really
  wants a rule to fire twice in one chain, that is not possible.
- Automations make the request slower, because they run before the
  response is sent.
- The guard only works inside one thread. If automations move to Celery
  later, follow-up signals run in other workers, and the guard does not
  see them. Then it must be replaced, for example with a guard in Redis.
  A comment in `receivers.py` warns about this.

## Alternatives considered

- **Run rules in Celery tasks:** faster responses, but needs a distributed
  loop guard. Too complex for the current size.
- **Maximum depth (for example 5 nested rules):** simple, but rules still
  run several times before they stop, which can create confusing results.
