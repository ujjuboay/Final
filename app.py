from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
import pickle
import gunicorn

with open('sent.pkl', 'rb') as pickle_in:
     unpickled_sent = pickle.load(pickle_in)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

socketio = SocketIO(app, manage_session=False)

arr = []
y_new = []

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if(request.method=='POST'):
        username = request.form['username']
        room = request.form['room']
        #Store the data in session
        session['username'] = username
        session['room'] = room
        return render_template('chat.html', session = session)
    else:
        if(session.get('username') is not None):
            return render_template('chat.html', session = session)
        else:
            return redirect(url_for('index'))

@socketio.on('join', namespace='/chat')
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg':  session.get('username') + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    room = session.get('room')
    emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)
    arr.append(message['msg'])
    #print(arr)
    if(len(arr) > 9):
        for i in arr:
          y_prob = unpickled_sent.predict([i])
          if (y_prob[0] == 50):
            #y_prob[0] = 1
            y_new.append(int(y_prob[0]))
          elif(y_prob[0] == 100):
            #y_prob[0] = 2
            y_new.append(int(y_prob[0]))
          else:
            #y_prob[0] = 0
            y_new.append(int(y_prob[0]))

        print(y_new)
        avg = sum(y_new)/len(y_new)
        print(avg)
        if (avg > 49.99):
          print("Malicious activity detected")
        else:
          print("No Malicious activity detected")
        del arr[:]
        del y_new[:]

@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)


if __name__ == '__main__':
    socketio.run(app)
