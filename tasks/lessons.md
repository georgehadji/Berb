# Lessons

## Run CI gates with CI's exact flags (2026-11-25)

`python scripts/check_reachability.py` with no flags prints `[OK]` whatever
the unreachable LOC: `--max-unreachable-loc` defaults to 0, meaning "never
fail". Waves 5 and 6 were "verified" that way while GitHub CI was
billing-blocked, and wave 5 pushed the ratchet from 686 to 1866 unnoticed.

Rule: when CI cannot run, copy each gate's command from
`.github/workflows/ci.yml` verbatim, flags included. A gate that cannot fail
is not a gate.
