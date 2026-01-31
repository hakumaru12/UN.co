"""
Lightweight web UI for Steer RC Controller using Flask + SocketIO.
- Serves a single-page app that mirrors the GUI controls and shows live controller status.
- Allows Start/Stop, Rescan, Test UDP, Save config from browser.
"""
from threading import Thread, Event
import queue
import time
import json
import os

from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit

# Reuse functions from Win_gui.py
from Win_gui import load_config, save_config, controller_thread

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

cfg = load_config()
log_queue = queue.Queue()
status = {'steer':0.0,'throttle':0.0,'brake':0.0,'direction':1,'joystick_name':''}
stop_event = Event()
worker = None

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Steer RC - Web UI</title>
  <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
  <style>body{font-family:Arial;padding:20px;} .row{margin-bottom:10px;} label{display:inline-block;width:140px}</style>
</head>
<body>
  <h2>Steer RC - Web UI</h2>
  <div class="row"><label>UDP IP</label><input id="UDP_IP" size=15></div>
  <div class="row"><label>UDP Port</label><input id="UDP_PORT" size=6></div>
  <div class="row"><label>Steer range</label><input id="Steer_val_range" type=range min=0 max=45><span id="steer_val">23</span></div>
  <div class="row"><label>Throttle range</label><input id="Throttle_range" type=range min=0 max=200><span id="throttle_val">50</span></div>
  <div class="row"><label>Brake range</label><input id="Brake_range" type=range min=0 max=200><span id="brake_val">50</span></div>
  <div class="row"><label>Deadzone (%)</label><input id="deadzone" type=range min=0 max=20><span id="deadzone_val">2%</span></div>
  <div class="row"><label>Steering sensitivity</label><input id="steering_sensitivity" type=range min=50 max=200 step=5><span id="sens_val">1.00</span></div>

  <div class="row">
    <button id="start">Start</button>
    <button id="stop" disabled>Stop</button>
    <button id="save">Save</button>
    <button id="rescan">Rescan Joystick</button>
    <button id="testudp">Test UDP</button>
  </div>

  <h3>Current</h3>
  <div id="current">Steer: 0.00 | Throttle: 0.0 | Brake: 0.0 | Dir: F</div>

  <h3>Logs</h3>
  <pre id="logs" style="background:#f0f0f0;padding:10px;height:240px;overflow:auto"></pre>

<script>
  const socket = io();
  function $(id){return document.getElementById(id)}
  // initialize from server cfg
  fetch('/api/config').then(r=>r.json()).then(c=>{
    $('UDP_IP').value = c.UDP_IP
    $('UDP_PORT').value = c.UDP_PORT
    $('Steer_val_range').value = c.Steer_val_range; $('steer_val').innerText = c.Steer_val_range
    $('Throttle_range').value = c.Throttle_range; $('throttle_val').innerText = c.Throttle_range
    $('Brake_range').value = c.Brake_range; $('brake_val').innerText = c.Brake_range
    $('deadzone').value = Math.round((c.deadzone||0.02)*100); $('deadzone_val').innerText = $('deadzone').value + '%'
    $('steering_sensitivity').value = Math.round((c.steering_sensitivity||1.0)*100); $('sens_val').innerText = ( $('steering_sensitivity').value /100).toFixed(2)
  })

  // UI interactions
  $('Steer_val_range').addEventListener('input',e=>$('steer_val').innerText=e.target.value)
  $('Throttle_range').addEventListener('input',e=>$('throttle_val').innerText=e.target.value)
  $('Brake_range').addEventListener('input',e=>$('brake_val').innerText=e.target.value)
  $('deadzone').addEventListener('input',e=>$('deadzone_val').innerText=e.target.value+'%')
  $('steering_sensitivity').addEventListener('input',e=>$('sens_val').innerText=(e.target.value/100).toFixed(2))

  $('save').addEventListener('click',()=>{
    const body={
      UDP_IP: $('UDP_IP').value, UDP_PORT: $('UDP_PORT').value,
      Steer_val_range: $('Steer_val_range').value, Throttle_range: $('Throttle_range').value, Brake_range: $('Brake_range').value,
      deadzone: $('deadzone').value/100.0, steering_sensitivity: $('steering_sensitivity').value/100.0
    }
    fetch('/api/save',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}).then(()=>appendLog('Config saved'))
  })

  $('start').addEventListener('click',()=>{ socket.emit('start'); $('start').disabled=true; $('stop').disabled=false })
  $('stop').addEventListener('click',()=>{ socket.emit('stop'); $('start').disabled=false; $('stop').disabled=true })
  $('rescan').addEventListener('click',()=>{ socket.emit('rescan'); })
  $('testudp').addEventListener('click',()=>{ socket.emit('testudp'); })

  socket.on('log',msg=>appendLog(msg))
  socket.on('status',s=>{
    $('current').innerText = `Steer: ${s.steer.toFixed(2)} | Throttle: ${s.throttle.toFixed(1)} | Brake: ${s.brake.toFixed(1)} | Dir: ${s.direction===1?'F':'R'}`
  })

  function appendLog(msg){ const el=$('logs'); el.innerText = msg + '\n' + el.innerText }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/config')
def api_config():
    return jsonify(cfg)

@app.route('/api/save', methods=['POST'])
def api_save():
    data = request.get_json() or {}
    # merge limited fields
    for k in ['UDP_IP','UDP_PORT','Steer_val_range','Throttle_range','Brake_range','deadzone','steering_sensitivity']:
        if k in data:
            cfg[k] = data[k]
    save_config(cfg)
    return ('',204)

@socketio.on('connect')
def on_connect():
    emit('log', 'Web UI connected')

@socketio.on('start')
def on_start():
    global worker, stop_event
    stop_event.clear()
    if worker is None or not worker.is_alive():
        worker = Thread(target=controller_thread, args=(cfg, log_queue, stop_event, status), daemon=True)
        worker.start()
        emit('log', 'Started controller thread')

@socketio.on('stop')
def on_stop():
    global worker, stop_event
    stop_event.set()
    emit('log', 'Stopping controller thread')

@socketio.on('rescan')
def on_rescan():
    try:
        import pygame
        pygame.joystick.quit(); pygame.joystick.init(); cnt = pygame.joystick.get_count()
        if cnt == 0:
            emit('log', 'No joystick detected')
        else:
            js = pygame.joystick.Joystick(0); js.init(); status['joystick_name']=js.get_name(); emit('log', f'Rescanned: {cnt} found. Using: {status["joystick_name"]}')
    except Exception as e:
        emit('log', 'Rescan failed: '+str(e))

@socketio.on('testudp')
def on_testudp():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pkt = struct.pack('ffi', 0.0, 0.0, 1)
        s.sendto(pkt, (cfg['UDP_IP'], int(cfg['UDP_PORT'])))
        s.close()
        emit('log', 'Test UDP packet sent')
    except Exception as e:
        emit('log', 'Test UDP failed: '+str(e))

# background broadcaster that emits logs and status frequently

def broadcaster_loop():
    while True:
        try:
            while not log_queue.empty():
                msg = log_queue.get_nowait()
                socketio.emit('log', msg)
        except Exception:
            pass
        socketio.emit('status', status)
        socketio.sleep(0.2)

if __name__ == '__main__':
    # start broadcaster
    socketio.start_background_task(broadcaster_loop)
    print('Starting web UI on http://0.0.0.0:5000 - open in your browser')
    socketio.run(app, host='0.0.0.0', port=5000)
