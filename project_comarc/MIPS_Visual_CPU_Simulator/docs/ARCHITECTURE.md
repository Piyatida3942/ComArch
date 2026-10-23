# Architecture

`main.py` → `interface.gui.App` → `integration.controller.Controller` → `simulator.assembler.assemble_file` + `simulator.cpu.CPU` → `simulator.memory.Memory`.

MIPS programs are the only source of displayed numerical results. `reference.reference` is used to check correctness, not compute the simulator result. GUI uses Tkinter `after()` to avoid a blocking execution loop.
