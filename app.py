# -*-coding:utf-8-*-
from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask_sqlalchemy import SQLAlchemy
import os
import json
import time
# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')

@app.route('/')
def index():
    from_id = request.args.get('from')
    to_id = request.args.get('to')
    room_id = request.args.get('room')
    print from_id, to_id, room_id

    if from_id and to_id and room_id:
        from_id = int(from_id)
        to_id = int(to_id)
        room_id = int(room_id)
    else:
        return '参数错误'

    #从数据库获取聊天记录
    messages = Message.query.order_by(Message.createtime).all()
    msg_result = []
    for m in messages:
        if (m.fromid == from_id and m.toid == to_id) or (m.toid == from_id and m.fromid == to_id):
            msg_result.append(m.to_json())
    data = {
        'fromid':from_id,
        'toid':to_id,
        'roomid':room_id,
        'historymsg':msg_result
    }
    print data
    return render_template('chatroom.html', data=json.dumps(data))

@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    print 'join room'
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])

@socketio.on('my_room_event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    #保存到数据库
    msg = Message()
    msg.fromid = message['from']
    msg.toid = message['to']
    msg.messagecontent = message['data']
    msg.createtime = time.strftime('%Y%m%d%H%M%S')
    msg.roomid = message['room']
    db.session.add(msg)
    db.session.commit()

    emit('my_response',
         {'data': message['data'], 'count': session['receive_count'], 'fromid':message['from']},
         room=message['room'])

@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


class Message(db.Model):
    __tablename__ = 'message'
    def __init__(self):
        self.i = 1
    messageid = db.Column(db.Integer, primary_key=True)
    messagecontent = db.Column(db.String(255))
    fromid = db.Column(db.Integer)
    toid = db.Column(db.Integer)
    roomid = db.Column(db.Integer)
    createtime = db.Column(db.String(20))

    def to_json(self):
        json_post = {
            'messageid':self.messagecontent,
            'fromid':self.fromid,
            'toid':self.toid,
            'roomid':self.roomid,
            'messagecontent':self.messagecontent,
            'createtime':self.createtime
        }
        return json_post

    def __repr__(self):
        return '< %r>' % self.messagecontent

if __name__ == '__main__':
    socketio.run(app, debug=True)
