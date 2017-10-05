import mpd
import datetime
import json
from socketIO_client import SocketIO, LoggingNamespace
import threading

socketIO = SocketIO('https://avery.caltech.edu')

def create_mpd_client():
    client = mpd.MPDClient()
    client.connect('localhost', 6600)
    return client

def on_connect():
    print('connect')

def on_disconnect():
    print('disconnect')

def on_reconnect():
    print('reconnect')

def on_new_tracks(tracks):
    print('on_new_tracks', tracks)
    client = create_mpd_client()
    starting_playlist_length = client.status()['playlistlength']
    for track in tracks:
        add = False
        if 'soundcloud.com' in track:
            mpd_uri = 'sc:' + track
            add = True
        elif 'youtube.com' in track:
            mpd_uri = 'yt:' + track
            add = True
        if add:
            print('Adding {}'.format(mpd_uri))
            try:
                client.add(mpd_uri)
            except mpd.CommandError as e:
                print(e)
    ending_playlist_length = client.status()['playlistlength']
    stopped = client.status()['state'] == 'stop'

    if stopped and ending_playlist_length > starting_playlist_length:
        client.play(starting_playlist_length)

    client.close()
    client.disconnect()

socketIO.on('connect', on_connect)
socketIO.on('disconnect', on_disconnect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('new_tracks', on_new_tracks)

def socketio_wait():
    socketIO.wait()

def mpd_wait():
    while True:
        client = create_mpd_client()
        client.idle()
        print('Updating')
        playlist = client.playlistinfo()
        dump = json.dumps(playlist)
        print('Dumped: {}'.format(dump))
        socketIO.emit('playlist', dump)

        song = client.status()['song'] if 'song' in client.status() else -1
        socketIO.emit('pos', song)

        client.close()
        client.disconnect()

socketio_thread = threading.Thread(target=socketio_wait)
mpd_thread = threading.Thread(target=mpd_wait)
socketio_thread.start()
mpd_thread.start()
