# MIPS Simulator UX Refinement (only modified folders)

Copy `interface/gui.py`, `interface/cpu_visualizer.py`, and `integration/controller.py` into the corresponding folders of your existing MIPS Visual CPU Simulator project. Back up the originals first. No other project files need replacing.

Changes:
- Header shows mathematical expression and independently calculated **expected/reference answer** in a prominent colored badge. This is not the simulated output; the separate simulated result appears only after successful HALT.
- Smaller CPU status cards and compact five-block functional CPU diagram.
- Execution controls are visible immediately below the diagram.
- Automatic Run starts at a human-readable speed (1 instruction per 500 ms). Select 2x, 5x, 20x, or Turbo to accelerate. Turbo sacrifices Back snapshots to avoid extreme memory usage.
- Draggable lower execution-history pane with scrollable instruction trace and per-step register-change inspection. Show/hide optional assembly and registers. The CPU trace keeps its latest 5,000 instructions; the Back snapshot history keeps 500 states. This is not an unlimited all-instruction archive for runs with millions of instructions.

Run: `python main.py` and `python -m pytest -q` from the project root.

Notes: The CPU is a functional instruction-level model, not a clock-accurate pipeline. The theme and guided two-screen setup are preserved.
