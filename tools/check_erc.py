#!/usr/bin/env python3
"""Run ERC, allowing exactly the intentional warnings in kicad/README.md.

    python3 tools/check_erc.py              # run KiCad and validate
    python3 tools/check_erc.py report.json  # validate an existing report

The allowlist matches severity, rule and item identity; it does not suppress
any KiCad rule or exclude any violation in the project.
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = Counter({
    ('warning', 'global_label_dangling', ("Global Label 'FPGA_DXP'",)): 1,
    ('warning', 'global_label_dangling', ("Global Label 'FPGA_DXN'",)): 1,
})


def signature(violation):
    return (violation['severity'], violation['type'],
            tuple(sorted(item['description'] for item in violation['items'])))


def check(report):
    actual = Counter(signature(v) for sheet in report['sheets']
                     for v in sheet['violations'])
    unexpected, missing = actual - EXPECTED, EXPECTED - actual
    for sig, count in unexpected.items():
        print(f'Unexpected ERC finding ({count}): {sig}', file=sys.stderr)
    for sig, count in missing.items():
        print(f'Expected warning absent ({count}); review documentation/allowlist: {sig}', file=sys.stderr)
    return not unexpected and not missing


def main():
    if len(sys.argv) > 2:
        print(__doc__, file=sys.stderr)
        return 2
    if len(sys.argv) == 2:
        report = json.loads(Path(sys.argv[1]).read_text())
    else:
        with tempfile.TemporaryDirectory(prefix='freyja-erc-') as tmp:
            path = Path(tmp) / 'erc.json'
            subprocess.run(['kicad-cli', 'sch', 'erc', '--severity-all',
                            '--format', 'json', '-o', str(path),
                            str(ROOT / 'kicad/odin.kicad_sch')],
                           cwd=ROOT, check=True)
            report = json.loads(path.read_text())
    if not check(report):
        return 1
    print('ERC PASS: zero errors; only FPGA_DXP and FPGA_DXN dangling-label warnings')
    return 0


if __name__ == '__main__':
    sys.exit(main())
