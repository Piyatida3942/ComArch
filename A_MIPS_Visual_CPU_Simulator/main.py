# NEW: ตัวเปิดโปรแกรม GUI แบบใหม่ -- บอกสถานะทีละขั้น, ถ้าพังจะลองโหมดปลอดภัยให้เอง
#   python main.py             -> เปิดตามปกติ (ถ้าพัง จะลองโหมดปลอดภัยต่ออัตโนมัติ)
#   python main.py --safe      -> โหมดปลอดภัย: ไม่เรียกโหมดจอความละเอียดสูง และไม่มีแอนิเมชันหน้าแรก
import os
import platform
import sys
import traceback

try:
    import faulthandler
    faulthandler.enable()          # ถ้า Tk ล่มแบบไม่มีข้อความ Python ก็จะพิมพ์ร่องรอยให้
except Exception:                  # noqa: BLE001
    pass


def say(msg):
    print(f'[main] {msg}', flush=True)


def _prepare(safe):
    from interface import gui
    if safe:
        gui._enable_dpi_awareness = lambda: None      # ไม่เรียกโหมดจอความละเอียดสูง
        gui.HomeHero.start = lambda self: None        # ไม่เล่นแอนิเมชันหน้าแรก
    return gui


def _reset_tk():
    import tkinter
    root = getattr(tkinter, '_default_root', None)
    if root is not None:
        try:
            root.destroy()
        except Exception:          # noqa: BLE001
            pass
        tkinter._default_root = None


def _bring_to_front(app):
    say('STEP 1: entering _bring_to_front')

    try:
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        say(f'STEP 2: screen size = {sw}x{sh}')

        width = min(1100, sw - 80)
        height = min(780, sh - 120)

        app.geometry(f'{width}x{height}+40+40')
        say('STEP 3: geometry set')

        app.deiconify()
        say('STEP 4: deiconify OK')

        app.lift()
        say('STEP 5: lift OK')

        app.focus_force()
        say('STEP 6: focus OK')

    except Exception:
        traceback.print_exc()

    say('STEP 7: finished')


def start(safe):
    gui = _prepare(safe)
    say('creating the window ...')
    app = gui.App()
    say(f'window created: {app.winfo_width()}x{app.winfo_height()} at +{app.winfo_x()}+{app.winfo_y()}'
        f'  (display scale {app.scale:.2f})')
    _bring_to_front(app)
    say('the window should be on your screen now. Close it to exit.')
    app.mainloop()
    say('window closed normally.')


def main():
    safe = '--safe' in sys.argv
    say(f'Python {platform.python_version()} on {platform.system()} | folder: {os.getcwd()}')
    try:
        import tkinter
        say(f'tkinter OK (Tk {tkinter.TkVersion})')
    except Exception:              # noqa: BLE001
        traceback.print_exc()
        say('tkinter is missing. Re-install Python from python.org and tick "tcl/tk and IDLE".')
        return 1
    if not os.path.isdir('interface') and not os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interface')):
        say('folder "interface" not found next to main.py -> unzip the update into the same folder as main.py')
        return 1
    try:
        start(safe)
        return 0
    except Exception:              # noqa: BLE001
        traceback.print_exc()
        if safe:
            say('FAILED even in safe mode.')
        else:
            say('FAILED. Retrying in SAFE mode (no high-DPI call, no animation) ...')
            _reset_tk()
            try:
                start(True)
                return 0
            except Exception:      # noqa: BLE001
                traceback.print_exc()
        try:
            with open('gui_error.log', 'w', encoding='utf-8') as f:
                traceback.print_exc(file=f)
        except Exception:          # noqa: BLE001
            pass
        say('Still failing. Please send everything printed above (also saved in gui_error.log).')
        return 1


if __name__ == '__main__':
    sys.exit(main())
