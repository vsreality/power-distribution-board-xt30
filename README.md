# PD-XT30-5 v1.0

VSReality Robotics five-port XT30 power distribution board. All five ports share a passive parallel bus; the intended arrangement is one supply and four loads.

## Board

- 18 x 52 mm, 1.6 mm FR4, two copper layers with 70 um (2 oz) copper per side.
- Two 3.2 mm non-plated M3 mounting holes, 42 mm centre-to-centre.
- Five centred XT30UPB connectors, spaced 7 mm apart and numbered 1-5.
- Port 1: XT30UPB-F; ports 2-5: XT30UPB-M. Confirm connector gender against the intended harness.
- Positive copper occupies the left strip when viewed from the front. Ground fills the remaining available area on both layers; mounting keepouts remain copper-free.
- Branding, model name and v1.0 are printed on the back.

| Front | Back |
| --- | --- |
| ![Front](preview-top-assembled.png) | ![Back](preview-bottom.png) |

[Angled 3D view](preview-3d-assembled.png)

## Files

Open `xt30-distribution.kicad_pro` in KiCad 9. The PCB, schematic and project-relative connector STEP models are included.

- `production/`: Gerbers, separate PTH/NPTH drills, IPC-D-356 netlist, fabrication instructions and SHA-256 manifest.
- `PD-XT30-5-v1.0-Production.zip`: verified bare-board manufacturing package.
- `fabrication/`: matching fabrication files and drill maps.
- `DESIGN-NOTES.txt`: mechanical, electrical and fabrication details.
- `drc-report.txt`, `erc-report.txt`, `production-verification.txt`: validation results.
- `models/MODEL-SOURCES.txt`: third-party model provenance; no additional license is asserted for those models.

**Design notes:** DRC/ERC checks pass. Current rating and thermal performance have not been validated. No onboard fusing or reverse-polarity protection.

See [DESIGN-NOTES.txt](DESIGN-NOTES.txt) for detailed validation and rebuild instructions.
