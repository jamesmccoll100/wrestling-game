import os
import pty
import select
import struct
import fcntl
import termios
import signal
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wrestling-arena-2026'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

GAME_COMMAND = ['python3', '-u', 'WrestlingMenu.py']
COLS = 90
ROWS = 30

sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    sid = request.sid
    pid, fd = pty.fork()
    if pid == 0:
        winsize = struct.pack('HHHH', ROWS, COLS, 0, 0)
        fcntl.ioctl(pty.STDOUT_FILENO, termios.TIOCSWINSZ, winsize)
        os.execvp(GAME_COMMAND[0], GAME_COMMAND)
    else:
        sessions[sid] = (pid, fd)
        socketio.start_background_task(read_loop, sid, fd)

def read_loop(sid, fd):
    while True:
        try:
            r, _, _ = select.select([fd], [], [], 0.04)
            if r:
                data = os.read(fd, 4096)
                if not data:
                    break
                socketio.emit('output',
                              data.decode('utf-8', errors='replace'),
                              room=sid)
        except OSError:
            break
    socketio.emit('game_ended', room=sid)

@socketio.on('input')
def on_input(data):
    sid = request.sid
    if sid in sessions:
        _, fd = sessions[sid]
        try:
            os.write(fd, data.encode())
        except OSError:
            pass

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in sessions:
        pid, fd = sessions.pop(sid)
        try:
            os.close(fd)
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except OSError:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)