#!/usr/bin/python

from flask import Flask, render_template, request, redirect, url_for
import os
import conf

init = False

app = Flask(__name__)

files = []

@app.route('/update')
def update():
    global files
    if init:
        files = []
    # Get the absolute path to the application directory
    app_directory = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the 'static/flash' directory
    flash_directory = os.path.join(app_directory, 'static', 'flash')
    # walk /flash for all .swf files, store basename in files array
    for root, dirs, filenames in os.walk(flash_directory):
        for filename in filenames:
            if filename.endswith('.swf'):
                files.append(os.path.splitext(filename)[0])
    if init:
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
    return render_template('index.html', gameslist = "<br>".join(gamesList))

@app.route('/game/<game>')
def game(game):
    if not prevent_traversal(game, True):
        return redirect(url_for('index'))
    if game in files:
        return render_template('games.html', gameName = beautify(game), swf_path = f'/flash/{game}.swf')
    else:
        return redirect(url_for('index'))

@app.route('/flash/<path:game>')
def flash(game):
    if not prevent_traversal(game, False):
        return redirect(url_for('index'))
    print(game)
    if not game.endswith('.swf'):
        #404
        return '404'
    # return swf file
    return app.send_static_file(f'flash/{game}')

@app.route('/ruffle/<path:text>')
def ruffle(text):
    if not prevent_traversal(text, False):
        return redirect(url_for('index'))
    return app.send_static_file(f'ruffle/{text}')

@app.route('/random')
def random():
    import random
    return redirect(url_for('game', game=random.choice(files)))

@app.route('/request', methods=['GET', 'POST'])
def newgame():
    # if POST log request to file
    # if GET return template request.html
    if request.method == 'POST':
        print(request.form)
        with open('requests.txt', 'a') as f:
            f.write(f"{request.form['gameName']} at {request.form['source']}\n")
            print("Request logged")
        return redirect(url_for('index'))
    else:
        return render_template('request.html')

#enable redirect from the update function
init = True

if __name__ == '__main__':
    # print url to index page
    print(f"URL: http://{conf.host}:{conf.port}")
    app.run(host=conf.host, port=conf.port, debug=conf.debug)