# Two-Screen Guided UI Patch

This patch changes only `interface/gui.py` and supplies the matching `interface/cpu_visualizer.py` and `integration/controller.py` from the prior history-enabled update for compatibility.

## Installation (Windows)

1. Back up the existing `interface/` and `integration/controller.py`.
2. Copy the patch's `interface/` folder into the project folder containing `main.py` (merge/replace).
3. Copy `integration/controller.py` into the project's `integration/` folder (replace).
4. Run `python main.py`. No additional dependencies beyond the existing project requirements.
5. Run `python -m pytest -q` and `python main.py --selftest` from the project root.

## Workflow

1. Setup screen: select Factorial (n only) or nCr (n and r; optional algorithm), then Next.
2. Simulation screen: read the result only when the program halts successfully; Step, Back, Run, Pause and Reset are available.
3. Enable `Show technical details` for assembly and register inspection.
4. Change Inputs returns to setup. Theme toggle works on both screens.

## Caveats

- `Back` records up to 500 manually stepped CPU states. `Run` clears that history.
- CPU diagram shows functional data flow, not pipelined clock stages.
- The original simulator and assembly files remain unchanged.
