#!/usr/bin/python

from flask import Flask, render_template, request, redirect, url_for
import os
import conf

init = False

app = Flask(__name__)

files = []

app_directory = os.path.dirname(os.path.abspath(__file__))

@app.route('/update')
def update():
    global files, app_directory
    
    if init:
        files = []
    # Construct the absolute path to the 'static/flash' directory
    flash_directory = os.path.join(app_directory, 'static', 'flash')
    # walk /flash for all .swf files, store basename in files array
    for root, dirs, filenames in os.walk(flash_directory):
        for filename in filenames:
            if filename.endswith('.swf'):
                files.append(os.path.splitext(filename)[0])
    if init:
        if conf.access_log:
            with open(conf.access_log, 'a') as f:
                if request.headers.get('X-Forwarded-For'):
                    f.write(f"{request.headers.get('X-Forwarded-For')} requested update\n")
                else:
                    f.write(f"{request.remote_addr} requested update\n")
        return redirect(url_for('index'))

update()

def prevent_traversal(path, isStrict):
    if isStrict:
        if path.count('/') > 1:
            print(f"traversal blocked on {path}")
            return False
    else:
        if path.count('..') > 0:
            print(f"traversal blocked on {path}")
            return False
        elif path.count('~') > 0:
            print(f"traversal blocked on {path}")
            return False
    return True

def beautify(string):
    return string.replace('-', ' ').replace('_', ' ').title()

def log_request(request, message):
    if conf.access_log:
        with open(conf.access_log, 'a') as f:
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            f.write(f"{ip} {message}\n")


@app.route('/')
def index():
    gamesList = []
    for file in files:
        # create anchor tag for each file
        # link text is beutified filename
        link = f"<a href='/game/{file}'>{beautify(file)}</a>"
        gamesList.append(link)
    gamesList.sort()
    gamesList.append(f"<a href='/random'>Random</a>")
    gamesList.append(f"<a href='/request'>Request</a>")
    log_request(request, "requested index")
    return render_template('index.html', gameslist = "<br>".join(gamesList))

@app.route('/game/<game>')
def game(game):
    if not prevent_traversal(game, True):
        return redirect(url_for('index'))
    if game in files:
        log_request(request, f"requested {game}")
        return render_template('games.html', gameName = beautify(game), swf_path = f'/flash/{game}.swf')
    else:
        log_request(request, f"requested {game}, game does not exist")
        return redirect(url_for('index'))

@app.route('/flash/<path:game>')
def flash(game):
    if not prevent_traversal(game, False):
        return redirect(url_for('index'))
    if not game.endswith('.swf'):
        #404
        log_request(request, f"requested {game}, which is not an swf")
        return '404'
    # return swf file
    log_request(request, f"requested flash for {game}")
    return app.send_static_file(f'flash/{game}')

@app.route('/ruffle/<path:text>')
def ruffle(text):
    if not prevent_traversal(text, False):
        return redirect(url_for('index'))
    log_request(request, f"requested ruffle for {text}")
    return app.send_static_file(f'ruffle/{text}')

@app.route('/random')
def random():
    import random
    log_request(request, "requested a random game")
    return redirect(url_for('game', game=random.choice(files)))

@app.route('/request', methods=['GET', 'POST'])
def newgame():
    # if POST log request to file
    # if GET return template request.html
    if request.method == 'POST':
        print(request.form)
        with open(f'{app_directory}/{conf.request_log}', 'a') as f:
            f.write(f"{request.form['gameName']} at {request.form['source']}\n")
            print("Request logged")
        log_request(request, "submitted a game request")
        return redirect(url_for('index'))
    else:
        log_request(request, "requested request page")
        return render_template('request.html')
    
@app.route('/request/list')
def listrequests():
    log_request(request, "requested the request list")
    with open(f'{app_directory}/requests.txt', 'r') as f:
        return f.read()

#enable redirect from the update function
init = True

if __name__ == '__main__':
    # print url to index page
    print(f"URL: http://{conf.flask['host']}:{conf.flask['port']}")
    app.run(conf.flask)