from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from Utils.database import get_incidents, delete_incident

app = Flask(__name__)
socketio = SocketIO(app)

# WebSocket connection
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    emit('update_messages', {'messages': get_incidents()})

@app.route('/')
def home():
    messages = get_incidents()
    print(messages)
    return render_template('index.html', title='Página de incidentes Perigosos', messages=messages)

@app.route('/update')
def update():
    socketio.emit('update_messages', {'messages': get_incidents()})
    return 'Updated!', 200

@app.route('/delete/<id>', methods=['DELETE'])
def delete(id):
    delete_incident(id)
    return 'deleted!', 204

if __name__ == '__main__':
    socketio.run(app, debug=True)
    