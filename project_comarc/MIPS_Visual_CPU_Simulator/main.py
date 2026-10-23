# NEW: entry point for GUI and headless selftest
import sys
if __name__=='__main__':
 if '--selftest' in sys.argv:
  from integration.selftest import run_selftest
  sys.exit(0 if run_selftest() else 1)
 from interface.gui import App
 App().mainloop()
