# AUX coupled inductor: C54563336

The EasyEDA import failed. L10 therefore uses a **locally generated** symbol
and footprint, not a claimed successful import. No PCB placement is changed
by generating this library asset.

Source: PROD's [PSSCAQ7048–1285 series specification, revision A3.0,
2026-05-08](https://atta.szlcsc.com/upload/public/pdf/source/20260512/7FA59B182872D8AEF44988AEFC20E605.pdf).
Page 3 gives the winding diagram; page 6 gives the PSSCAQ1285 dual-inductor
recommended land pattern. Do not use the alternative series/parallel lands.

| Pad | Centre X (mm) | Centre Y (mm) | Winding terminal | SEPIC net |
|---|---:|---:|---|---|
| 1 | -1.75 | -4.975 | first winding, dotted | VSYS |
| 2 | +1.75 | -4.975 | second winding, dotted | GND |
| 3 | +1.75 | +4.975 | first winding, undotted | AUX_SW |
| 4 | -1.75 | +4.975 | second winding, undotted | AUX_SEPIC |

All four lands are 2.50 × 3.85 mm. The drawing's 3.50 and 9.95 mm dimensions
are **centre pitches**, not the gaps between lands or the overall land span.
The body is at most 12.5 × 12.5 × 8.5 mm; the courtyard also encloses the
lands, whose overall Y span is 13.8 mm. Silkscreen is interrupted over pads.

The two windings are 1–3 and 2–4, with dots at 1 and 2. In the SEPIC on-state,
both dotted-to-undotted winding voltages are positive: VSYS−AUX_SW and
GND−AUX_SEPIC. Connecting the second dotted end to AUX_SEPIC instead would
reverse the coupling.

The 4R7MP row specifies 4.7 µH ±20%, 97.6% typical coupling, 26 mΩ maximum
DCR, 5 A temperature-rise current and 15 A saturation current. These are
component ratings, **not verification of the complete 12 W converter**.
Current ripple, operating frequency, source limits, loop stability and board
temperature still require the complete converter checks.

[JLC's exact part listing](https://jlcpcb.com/partdetail/PRODTech-PSSCAQ12854R7MP/C54563336)
lists Extended, wave-solder assembly, and Economic/Standard PCBA support.
Confirm the assembly process at order time; no 3D model is invented here.

Generator: `tools/gen_kicad.py`, `gen_aux_symbols()` / `gen_aux_footprints()`.
Check: `/usr/bin/python3 tools/check_aux_magnetics.py`.
