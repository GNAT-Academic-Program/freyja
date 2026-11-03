# Freyja repository guidance

Read [README.md](README.md), [kicad/README.md](kicad/README.md), the current
section of [findings.md](findings.md), and the single detailed workflow:
[ref/ide-agent-prompt.md](ref/ide-agent-prompt.md).

The live KiCad PCB owns manual placement and routing. Preserve existing work
and protected hardware hashes when the task is organizational or documentary.
Never run `tools/gen_pcb.py` without `--rules-only` on an existing board;
even `--rules-only` intentionally changes rules/stackup. Inspect every writer
before using it. The workflow documents checks, generator side effects and
the recurring cleanup checkpoint.

`archive/` contains historical inputs, evidence and superseded instructions.
Do not execute its task lists as current work. Imported `EasyEDA:` libraries
remain active dependencies; retain their paths and qualified identifiers.
