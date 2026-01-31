# Windows GUI wrapper for Win_copy.py controller sender
import threading
import queue
import socket
import struct
import time
import json
import os
import traceback

# Import pygame lazily (some environments may not have it installed)
# This prevents ModuleNotFoundError when running --preview or --nogui
# Delay importing PySimpleGUI until after a virtual display is started (if needed)
sg = None  # will be imported later in main() when a display is available


def import_pygame_or_error(log_queue=None):
    try:
        import pygame  # type: ignore
        return pygame
    except ModuleNotFoundError:
        msg = "ERROR: pygame is not installed. Install with: python -m pip install pygame"
        if log_queue is not None:
            log_queue.put(msg)
        else:
            print(msg)
        return None
    except Exception as e:
        msg = f"ERROR importing pygame: {e}"
        if log_queue is not None:
            log_queue.put(msg)
        else:
            print(msg)
        return None

CONFIG_FILE = "controller_config.json"
DEFAULT_CONFIG = {
    "UDP_IP": "192.168.11.2",
    "UDP_PORT": 5005,
    "Steer_val_range": 23,
    "Throttle_range": 50,
    "Brake_range": 50,
    "THROTTLE_STEP": 5,
    "THROTTLE_MIN": 30,
    "THROTTLE_MAX": 100,
    "BUTTON_THROTTLE_UP": 4,
    "BUTTON_THROTTLE_DOWN": 5,
    "BUTTON_DIRECTION_TOGGLE": 19,
    "apply_throttle_curve": True,
    "send_interval": 0.02,
    "deadzone": 0.02,
    "steering_sensitivity": 1.0
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


# small helpers

def apply_deadzone(value, deadzone=0.02):
    if abs(value) < deadzone:
        return 0
    return value


def map_range(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def apply_throttle_curve(value):
    return (value / 100) ** 2 * 100


# Threaded run loop
def controller_thread(cfg, log_queue, stop_event, status=None):
    if status is None:
        status = {}
    status.setdefault('steer', 0.0)
    status.setdefault('throttle', 0.0)
    status.setdefault('brake', 0.0)
    status.setdefault('direction', 1)
    status.setdefault('joystick_name', '')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        pygame = import_pygame_or_error(log_queue)
        if not pygame:
            return
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            log_queue.put("ERROR: Joystick not connected")
            return

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        status['joystick_name'] = joystick.get_name()
        log_queue.put(f"Controller connected: {status['joystick_name']}")

        current_direction = 1
        button_up_pressed = False
        button_down_pressed = False

        while not stop_event.is_set():
            try:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        log_queue.put(f"Button {event.button} pressed")
                        if event.button == int(cfg["BUTTON_DIRECTION_TOGGLE"]):
                            current_direction = -current_direction
                            dir_str = "Forward" if current_direction == 1 else "Reverse"
                            status['direction'] = current_direction
                            log_queue.put(f"Direction: {dir_str}")
                        elif event.button == int(cfg["BUTTON_THROTTLE_UP"]):
                            cfg["Throttle_range"] = min(int(cfg["Throttle_range"]) + int(cfg["THROTTLE_STEP"]), int(cfg["THROTTLE_MAX"]))
                            log_queue.put(f"Throttle range -> {cfg['Throttle_range']}")
                        elif event.button == int(cfg["BUTTON_THROTTLE_DOWN"]):
                            cfg["Throttle_range"] = max(int(cfg["Throttle_range"]) - int(cfg["THROTTLE_STEP"]), int(cfg["THROTTLE_MIN"]))
                            log_queue.put(f"Throttle range -> {cfg['Throttle_range']}")

                steering = joystick.get_axis(0)
                raw_throttle = -joystick.get_axis(1)
                raw_brake = -joystick.get_axis(2)

                deadzone = float(cfg.get('deadzone', 0.02))
                steering = apply_deadzone(steering, deadzone)
                throttle = apply_deadzone(raw_throttle, deadzone)
                brake = apply_deadzone(raw_brake, deadzone)

                sensitivity = float(cfg.get('steering_sensitivity', 1.0))
                steering_angle = map_range(steering * sensitivity, -1.0, 1.0, -float(cfg["Steer_val_range"]), float(cfg["Steer_val_range"]))

                if raw_brake > -0.99:
                    throttle_value = 0
                    direction = current_direction
                elif raw_throttle > -0.99:
                    raw_throttle_value = map_range(throttle, -0.99, 1.0, 0, float(cfg["Throttle_range"]))
                    throttle_value = apply_throttle_curve(raw_throttle_value) if cfg.get("apply_throttle_curve", True) else raw_throttle_value
                    direction = current_direction
                else:
                    throttle_value = 0
                    direction = current_direction

                status['steer'] = steering_angle
                status['throttle'] = throttle_value
                status['brake'] = map_range(brake, -0.99, 1.0, 0, float(cfg.get('Brake_range', 0)))
                status['direction'] = direction

                data = struct.pack('ffi', float(steering_angle), float(throttle_value), int(direction))
                sock.sendto(data, (cfg["UDP_IP"], int(cfg["UDP_PORT"])))

                log_queue.put(f"S:{steering_angle:.1f}  T:{throttle_value:.1f}  D:{direction}")

                time.sleep(float(cfg.get("send_interval", 0.02)))
            except Exception as e:
                tb = traceback.format_exc()
                log_queue.put("ERROR: " + str(e))
                log_queue.put(tb)
                stop_event.set()
                break
    except Exception as e:
        tb = traceback.format_exc()
        log_queue.put("ERROR: " + str(e))
        log_queue.put(tb)
    finally:
        try:
            sock.close()
            pygame.quit()
        except Exception:
            pass
        log_queue.put("Thread stopped")


def render_preview_html(cfg, out_path="ui_preview.html"):
    html = f"""
    <html><head><meta charset='utf-8'><title>Steer RC UI Preview</title></head>
    <body style='font-family: Arial; padding:20px;'>
    <h2>Steer RC Controller - UI Preview</h2>
    <table>
      <tr><td><b>UDP IP</b></td><td>{cfg['UDP_IP']}</td></tr>
      <tr><td><b>UDP Port</b></td><td>{cfg['UDP_PORT']}</td></tr>
      <tr><td><b>Steer range</b></td><td>{cfg['Steer_val_range']}</td></tr>
      <tr><td><b>Throttle range</b></td><td>{cfg['Throttle_range']}</td></tr>
      <tr><td><b>Brake range</b></td><td>{cfg['Brake_range']}</td></tr>
      <tr><td><b>Throttle step</b></td><td>{cfg['THROTTLE_STEP']}</td></tr>
      <tr><td><b>THROTTLE MIN</b></td><td>{cfg['THROTTLE_MIN']}</td></tr>
      <tr><td><b>THROTTLE MAX</b></td><td>{cfg['THROTTLE_MAX']}</td></tr>
      <tr><td><b>Button Throttle +</b></td><td>{cfg['BUTTON_THROTTLE_UP']}</td></tr>
      <tr><td><b>Button Throttle -</b></td><td>{cfg['BUTTON_THROTTLE_DOWN']}</td></tr>
      <tr><td><b>Button Dir Toggle</b></td><td>{cfg['BUTTON_DIRECTION_TOGGLE']}</td></tr>
      <tr><td><b>Apply throttle curve</b></td><td>{cfg.get('apply_throttle_curve', True)}</td></tr>
      <tr><td><b>Send interval</b></td><td>{cfg.get('send_interval',0.02)}</td></tr>
      <tr><td><b>Deadzone (%)</b></td><td>{cfg.get('deadzone',0.02)*100:.1f}</td></tr>
      <tr><td><b>Steering sensitivity</b></td><td>{cfg.get('steering_sensitivity',1.0):.2f}</td></tr>
    </table>
    <p>Note: This is a static preview. To run the actual GUI, run <code>python Win_gui.py</code> on a machine with a display (or use Xvfb/pyvirtualdisplay).</p>
    </body></html>
    """
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Wrote preview HTML to {out_path}")


def main():
    cfg = load_config()

    # Quick static preview for headless environments
    import sys
    if "--preview" in sys.argv:
        render_preview_html(cfg)
        return

    # Allow shared status for UI to display live values
    status = {'steer':0.0,'throttle':0.0,'brake':0.0,'direction':1,'joystick_name':''}

    # Allow headless / test mode: run without GUI using --nogui
    if "--nogui" in sys.argv:
        print("Running in --nogui mode (console). Start controller thread and print logs to stdout.")
        log_queue = queue.Queue()
        stop_event = threading.Event()
        worker = threading.Thread(target=controller_thread, args=(cfg, log_queue, stop_event, status), daemon=True)
        worker.start()
        try:
            while worker.is_alive():
                try:
                    msg = log_queue.get(timeout=0.5)
                    print(msg)
                except queue.Empty:
                    # optionally print status updates
                    continue
        except KeyboardInterrupt:
            print("Stopping (KeyboardInterrupt)")
            stop_event.set()
            worker.join(timeout=2)
        return

    # If there's no DISPLAY on non-Windows systems, try to start a virtual display (pyvirtualdisplay/Xvfb)
    import platform
    started_virtual_display = False
    if platform.system() != "Windows" and not os.environ.get("DISPLAY"):
        try:
            from pyvirtualdisplay import Display
            disp = Display(visible=0, size=(1024, 768))
            disp.start()
            started_virtual_display = True
            print("Started virtual display via pyvirtualdisplay (Xvfb). Continuing with GUI creation.")
        except Exception as e:
            print("Could not start virtual display automatically: " + str(e))
            print("To view GUI on headless Linux, install Xvfb and pyvirtualdisplay, then run:\n  sudo apt-get install -y xvfb\n  python -m pip install pyvirtualdisplay\nOr run with xvfb-run: 'xvfb-run python Win_gui.py'")
            # Fall back to headless controller behavior
            log_queue = queue.Queue()
            stop_event = threading.Event()
            worker = threading.Thread(target=controller_thread, args=(cfg, log_queue, stop_event, status), daemon=True)
            worker.start()
            try:
                while worker.is_alive():
                    try:
                        msg = log_queue.get(timeout=0.5)
                        print(msg)
                    except queue.Empty:
                        continue
            except KeyboardInterrupt:
                print("Stopping (KeyboardInterrupt)")
                stop_event.set()
                worker.join(timeout=2)
            return

    # Import PySimpleGUI now that a display may be available (importing it earlier can create a Tk root immediately)
    try:
        import PySimpleGUI as sg
    except Exception as e:
        print("ERROR: Failed to import PySimpleGUI: " + str(e))
        print("If running headless, install Xvfb and pyvirtualdisplay or run with --nogui. See README.md.")
        # fallback to headless controller behavior
        log_queue = queue.Queue()
        stop_event = threading.Event()
        worker = threading.Thread(target=controller_thread, args=(cfg, log_queue, stop_event, status), daemon=True)
        worker.start()
        try:
            while worker.is_alive():
                try:
                    msg = log_queue.get(timeout=0.5)
                    print(msg)
                except queue.Empty:
                    continue
        except KeyboardInterrupt:
            print("Stopping (KeyboardInterrupt)")
            stop_event.set()
            worker.join(timeout=2)
        return

    # Theme compatibility: some PySimpleGUI builds use different API names.
    try:
        if hasattr(sg, "theme"):
            sg.theme("DarkBlue3")
        elif hasattr(sg, "ChangeLookAndFeel"):
            sg.ChangeLookAndFeel("DarkBlue3")
        else:
            # fallback: do nothing, but inform the user
            print("Note: PySimpleGUI theme API not available in this installation. If you see layout issues, reinstall PySimpleGUI following README instructions.")
    except Exception:
        # Don't crash on theme setting problems
        print("Warning: Failed to set GUI theme (non-fatal)")

    # Verify that PySimpleGUI provides required elements. If not, provide clear guidance and exit.
    required = ["Text", "Input", "Button", "Window", "Multiline", "Checkbox", "Slider"]
    missing = [name for name in required if not hasattr(sg, name)]
    if missing:
        msg = (
            "PySimpleGUI installation appears incomplete or incompatible (missing: {})\n"
            "Please reinstall using the commands in README.md. Example:\n"
            "python -m pip uninstall PySimpleGUI && python -m pip cache purge && "
            "python -m pip install --upgrade --extra-index-url https://PySimpleGUI.net/install PySimpleGUI"
        ).format(", ".join(missing))
        print("ERROR: " + msg)
        # also append to README for easy copy/paste (already added), then exit
        sys.exit(1)

    layout = [
        [sg.Text("UDP IP:"), sg.Input(cfg["UDP_IP"], key="UDP_IP", size=(15,1)), sg.Text("Port:"), sg.Input(cfg["UDP_PORT"], key="UDP_PORT", size=(6,1))],
        [sg.Text("Current:"), sg.Text("Steer: 0.0", key='-CUR_STEER-', size=(18,1)), sg.Text("Throttle: 0.0", key='-CUR_THROTTLE-', size=(20,1)), sg.Text("Brake: 0.0", key='-CUR_BRAKE-', size=(12,1)), sg.Text("Dir: F", key='-CUR_DIR-', size=(6,1))],
        [sg.Text("Steer range:"), sg.Slider(range=(0,45), orientation='h', default_value=int(cfg["Steer_val_range"]), resolution=1, key="Steer_val_range", size=(40,15)), sg.Text('', key='-STEER_VAL-', size=(6,1))],
        [sg.Text("Throttle range:"), sg.Slider(range=(0,200), orientation='h', default_value=int(cfg["Throttle_range"]), resolution=1, key="Throttle_range", size=(40,15)), sg.Text('', key='-THROTTLE_VAL-', size=(6,1))],
        [sg.Text("Brake range:"), sg.Slider(range=(0,200), orientation='h', default_value=int(cfg["Brake_range"]), resolution=1, key="Brake_range", size=(40,15)), sg.Text('', key='-BRAKE_VAL-', size=(6,1))],
        [sg.Text("Deadzone:"), sg.Slider(range=(0,20), orientation='h', default_value=int(cfg.get('deadzone',0.02)*100), resolution=1, key='deadzone', size=(40,15)), sg.Text('', key='-DEADZONE_VAL-', size=(6,1))],
        [sg.Text("Steering sensitivity:"), sg.Slider(range=(50,200), orientation='h', default_value=int(cfg.get('steering_sensitivity',1.0)*100), resolution=5, key='steering_sensitivity', size=(40,15)), sg.Text('', key='-SENS_VAL-', size=(6,1))],
        [sg.Text("Throttle step:"), sg.Input(cfg["THROTTLE_STEP"], key="THROTTLE_STEP", size=(6,1)),
         sg.Text("Min:"), sg.Input(cfg["THROTTLE_MIN"], key="THROTTLE_MIN", size=(6,1)),
         sg.Text("Max:"), sg.Input(cfg["THROTTLE_MAX"], key="THROTTLE_MAX", size=(6,1))],
        [sg.Text("Btn Throttle +:"), sg.Input(cfg["BUTTON_THROTTLE_UP"], key="BUTTON_THROTTLE_UP", size=(6,1)),
         sg.Text("Btn Throttle -:"), sg.Input(cfg["BUTTON_THROTTLE_DOWN"], key="BUTTON_THROTTLE_DOWN", size=(6,1)),
         sg.Text("Btn Dir Toggle:"), sg.Input(cfg["BUTTON_DIRECTION_TOGGLE"], key="BUTTON_DIRECTION_TOGGLE", size=(6,1))],
        [sg.Checkbox("Apply throttle curve", default=cfg.get("apply_throttle_curve", True), key="apply_throttle_curve"),
         sg.Text("Send interval (s):"), sg.Input(cfg.get("send_interval",0.02), key="send_interval", size=(6,1))],
        [sg.Button("Start", key="-START-", button_color=("white","green")), sg.Button("Stop", key="-STOP-", disabled=True, button_color=("white","firebrick")), sg.Button("Save", key="-SAVE-"), sg.Button("Rescan Joystick", key='-RESCAN-'), sg.Button('Test UDP', key='-TESTUDP-')],
        [sg.HorizontalSeparator()],
        [sg.Multiline('', size=(80,14), key='-LOG-', autoscroll=True, disabled=True)],
    ]

    # Create window, but handle failures from tkinter (no DISPLAY).
    try:
        window = sg.Window("Steer RC Controller", layout, finalize=True)
    except Exception as e:
        # Try to detect Tkinter 'no display' error and fall back to headless
        err_str = str(e)
        if "no display name" in err_str.lower() or "no display" in err_str.lower() or "tclerror" in err_str.lower():
            print("ERROR: GUI cannot be created because no display was found (no $DISPLAY).\nFalling back to headless mode. Use 'xvfb-run python Win_gui.py' to run GUI on headless Linux.")
            log_queue = queue.Queue()
            stop_event = threading.Event()
            worker = threading.Thread(target=controller_thread, args=(cfg, log_queue, stop_event, status), daemon=True)
            worker.start()
            try:
                while worker.is_alive():
                    try:
                        msg = log_queue.get(timeout=0.5)
                        print(msg)
                    except queue.Empty:
                        continue
            except KeyboardInterrupt:
                print("Stopping (KeyboardInterrupt)")
                stop_event.set()
                worker.join(timeout=2)
            return
        else:
            raise

    # If user asked for a quick screenshot of the UI (useful in headless environments), capture it and exit.
    import sys
    if "--screenshot" in sys.argv:
        try:
            from PIL import ImageGrab
            # give the GUI a moment to render
            import time as _t
            _t.sleep(0.5)
            img = ImageGrab.grab()
            out = "ui_screenshot.png"
            img.save(out)
            print(f"Saved UI screenshot to {out}")
        except Exception as e:
            print("Screenshot failed: " + str(e))
            print("Ensure Pillow is installed and DISPLAY is available (or use a virtual display).")
        finally:
            try:
                window.close()
            except Exception:
                pass
        return

    log_queue = queue.Queue()
    stop_event = threading.Event()
    worker = None

    def append_log(msg):
        current = window['-LOG-'].get()
        new = current + msg + "\n"
        window['-LOG-'].update(new)

    try:
        while True:
            event, values = window.read(timeout=100)
            # update slider displays
            try:
                window['-STEER_VAL-'].update(str(int(values.get('Steer_val_range', cfg['Steer_val_range']))))
                window['-THROTTLE_VAL-'].update(str(int(values.get('Throttle_range', cfg['Throttle_range']))))
                window['-BRAKE_VAL-'].update(str(int(values.get('Brake_range', cfg['Brake_range']))))
                dz_pct = int(values.get('deadzone', int(cfg.get('deadzone',0.02)*100)))
                window['-DEADZONE_VAL-'].update(f"{dz_pct}%")
                sens = values.get('steering_sensitivity', int(cfg.get('steering_sensitivity',1.0)*100))
                window['-SENS_VAL-'].update(f"{sens/100:.2f}")
            except Exception:
                pass

            # handle log queue
            while not log_queue.empty():
                try:
                    msg = log_queue.get_nowait()
                    append_log(msg)
                    if msg.startswith("ERROR:"):
                        sg.popup_error(msg, title="Error")
                except queue.Empty:
                    break

            # update live values from status
            try:
                window['-CUR_STEER-'].update(f"Steer: {status.get('steer',0.0):.2f}")
                window['-CUR_THROTTLE-'].update(f"Throttle: {status.get('throttle',0.0):.1f}")
                window['-CUR_BRAKE-'].update(f"Brake: {status.get('brake',0.0):.1f}")
                dir_label = 'F' if status.get('direction',1)==1 else 'R'
                window['-CUR_DIR-'].update(f"Dir: {dir_label}")
            except Exception:
                pass

            if event == sg.WIN_CLOSED:
                if worker and worker.is_alive():
                    stop_event.set()
                    worker.join(timeout=1)
                break

            if event == '-SAVE-':
                # coerce and save values
                for k in ['UDP_IP','UDP_PORT','THROTTLE_STEP','THROTTLE_MIN','THROTTLE_MAX','BUTTON_THROTTLE_UP','BUTTON_THROTTLE_DOWN','BUTTON_DIRECTION_TOGGLE','apply_throttle_curve','send_interval']:
                    cfg[k] = values[k]
                # numeric fields from sliders
                cfg['Steer_val_range'] = int(values.get('Steer_val_range', cfg['Steer_val_range']))
                cfg['Throttle_range'] = int(values.get('Throttle_range', cfg['Throttle_range']))
                cfg['Brake_range'] = int(values.get('Brake_range', cfg['Brake_range']))
                cfg['deadzone'] = float(values.get('deadzone', int(cfg.get('deadzone',0.02)*100))) / 100.0
                cfg['steering_sensitivity'] = float(values.get('steering_sensitivity', int(cfg.get('steering_sensitivity',1.0)*100))) / 100.0
                save_config(cfg)
                append_log('Config saved')

            if event == '-START-':
                # update cfg from UI (same as save)
                for k in ['UDP_IP','UDP_PORT','THROTTLE_STEP','THROTTLE_MIN','THROTTLE_MAX','BUTTON_THROTTLE_UP','BUTTON_THROTTLE_DOWN','BUTTON_DIRECTION_TOGGLE','apply_throttle_curve','send_interval']:
                    cfg[k] = values[k]
                cfg['Steer_val_range'] = int(values.get('Steer_val_range', cfg['Steer_val_range']))
                cfg['Throttle_range'] = int(values.get('Throttle_range', cfg['Throttle_range']))
                cfg['Brake_range'] = int(values.get('Brake_range', cfg['Brake_range']))
                cfg['deadzone'] = float(values.get('deadzone', int(cfg.get('deadzone',0.02)*100))) / 100.0
                cfg['steering_sensitivity'] = float(values.get('steering_sensitivity', int(cfg.get('steering_sensitivity',1.0)*100))) / 100.0
                save_config(cfg)
                stop_event.clear()
                worker = threading.Thread(target=controller_thread, args=(cfg, log_queue, stop_event, status), daemon=True)
                worker.start()
                window['-START-'].update(disabled=True)
                window['-STOP-'].update(disabled=False)
                append_log('Started controller thread')

            if event == '-STOP-':
                stop_event.set()
                if worker:
                    worker.join(timeout=2)
                window['-START-'].update(disabled=False)
                window['-STOP-'].update(disabled=True)
                append_log('Stopped controller thread')

            if event == '-RESCAN-':
                # attempt to re-scan connected joysticks
                try:
                    try:
                        import pygame  # type: ignore
                    except ModuleNotFoundError:
                        append_log('Rescan failed: pygame is not installed. Install with: python -m pip install pygame')
                        continue
                    pygame.joystick.quit()
                    pygame.joystick.init()
                    cnt = pygame.joystick.get_count()
                    if cnt == 0:
                        append_log('No joystick detected')
                    else:
                        js = pygame.joystick.Joystick(0)
                        js.init()
                        status['joystick_name'] = js.get_name()
                        append_log(f'Rescanned joysticks: {cnt} found. Using: {status["joystick_name"]}')
                except Exception as e:
                    append_log('Rescan failed: ' + str(e))

            if event == '-TESTUDP-':
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    pkt = struct.pack('ffi', 0.0, 0.0, 1)
                    s.sendto(pkt, (cfg['UDP_IP'], int(cfg['UDP_PORT'])))
                    s.close()
                    append_log('Test UDP packet sent')
                except Exception as e:
                    append_log('Test UDP failed: ' + str(e))


    finally:
        try:
            stop_event.set()
            if worker and worker.is_alive():
                worker.join(timeout=1)
            window.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
