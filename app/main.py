from random import randint
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from datetime import datetime

from app import db
from app.models import User, Game, Encounter, Prompt
from app.forms import JoinForm, CreateForm, NextForm, JoinFormPOC, DeleteForm
from app import sched

import os

main = Blueprint('main', __name__)

'''
    Relative path to the maps
'''
MAP_PATH = os.sep + 'static' + os.sep + 'images' + os.sep + 'maps'

'''
    List of all the possible callsign prefix's for team information it will have a number concatenated to it
    If desired change all the names to be something that would suit your scenarios
'''
CALLSIGN_LIST = [
    'SALAMANDER',
    'FROG',
    'TURTLE',
    'LIZARD',
    'ALLIGATOR',
    'CONDOR',
    'GOOSE',
    'BIRD',
    'IBIS',
    'SHOEBILL',
    'OWL',
    'PIGEON',
    'CRAB',
    'CATERPILLAR',
    'CAMEL',
    'KIWI',
    'GOAT',
    'PLATYPUS',
    'ANTELOPE',
    'ZEBRA',
    'BOAR',
    'MONKEY',
    'FRUIT BAT',
    'WOMBAT',
    'OCTOPUS',
    'SHARK',
    'ANGLERFISH',
    'DOLPHIN',
    'SHRIMP'
]

'''
    List of all the locations to show up in the team information section
    If desired change all the names to be something that would suit your scenario
'''
LOCATION_LIST = [
    'C/JORDAN\'S BARBEQUE',
    'SHAPIRO FOUNTAIN',
    'WILSON PLAZA',
    'DRAKE STADIUM',
    'DICKSON COURT',
    'DODD HALL',
    'BUNCHE HALL',
    'ROSENFELD LIBRARY'
]

'''
    This job will remove all users that are older than whatever xTime is set to.  By default it is set to 35 seconds
'''
@sched.task('interval', id='do_job_1', seconds=120, misfire_grace_time=30)
def job1():
    print('job1 Triggered')
    with db.app.app_context(): 
        
        curTime = datetime.now()
        xTime = 35.0

        users = User.query.all()
        if len(users) > 0:
            for user in users:
                userTime = datetime.strptime(user.timeStamp, "%d/%m/%Y %H:%M:%S")
                deltaTime = (curTime - userTime)
                deltaTime = deltaTime.total_seconds()/60;
                if deltaTime >= xTime:
                    print('Deleting User: ' + user.group)
                    db.session.delete(user)
                    db.session.commit()
    
        games = Game.query.all()
        if len(games) > 0:
            for game in games:
                gameTime = datetime.strptime(game.timeStamp, "%d/%m/%Y %H:%M:%S")
                deltaTime = (curTime - gameTime)
                deltaTime = deltaTime.total_seconds()/60;
                if deltaTime >= xTime:
                    print('Deleting Game: ' + game.group)
                    db.session.delete(game)
                    db.session.commit()

'''
    This job will remove any users or games that are marked for deletion or victory
'''
@sched.task('interval', id='do_job_2', seconds=30, misfire_grace_time=30)
def job2():
    print('job2 Triggered')
    with db.app.app_context():
        
        games = Game.query.all()
        if games is not None:
            for game in games:
                if game.mode == 'VICTORY' or game.mode == 'MARKDEL':
                    users = User.query.filter_by(group=game.group)
                    if users is not None:
                        for user in users:
                            print('Deleting User: ' + user.group)
                            db.session.delete(user)
                            db.session.commit()
                    print('Deleting Game: ' + game.group)
                    db.session.delete(game)
                    db.session.commit()

'''
    Route for the index.  It will always redirect to the login screen
'''
@main.route('/')
@main.route('/index')
def index():
    return redirect(url_for('main.login'))

'''
    Route for the game status.  This route is not meant to be accessed by a user.
    It will only be accessed by the javascript on the client end.
'''
@main.route('/game/<group>/status', methods=['GET'])
@login_required
def gameStatus(group):
    user = current_user
    age = (datetime.now() - datetime.strptime(user.timeStamp, "%d/%m/%Y %H:%M:%S"))
    age = age.total_seconds()
    age = round(age/60, 1)

    game = Game.query.filter_by(group=user.group).first()
    
    return jsonify({'compEnc' : game.compEnc, 'age': str(age)})

'''
    The browser will list all the active games and their statuses.  All the game statuses are listed for debug purposes
'''
@main.route('/browser', methods=['GET', 'POST'])
def browser():
    games = Game.query.all()
    lenGames = len(games)

    return render_template(['browser.html', 'base.html'], games=games, lenGames=lenGames)

'''
    The game view will show all the game information and will show the progressing buttons for any hosts
'''
@main.route('/game/<group>', methods=['GET', 'POST'])
@login_required
def game(group):
    # Get user session data
    user = current_user
    game = Game.query.filter_by(group=user.group).first()
    prompt = Prompt.query.all()[0]
    encounter = Encounter.query.filter_by(number=game.curEnc).first()

    # Update the user and the game time whenever this view is accessed
    user.updateTime()
    game.updateTime()
    user.compEnc = game.compEnc
    db.session.commit()

    # If the game isnt there log them out
    if game is None:
        return redirect(url_for('main.logout'))

    # If the game is marked for deletion, log out the user
    if game.mode == "VICTORY" or game.mode == "MARKDEL":
        return redirect(url_for('main.logout'))

    # Instance all the forms
    nextForm = NextForm()
    delForm = DeleteForm()

    # If the delete button has been pressed, mark the game for deletion
    if delForm.submit11.data and delForm.validate():
        game.mode = 'MARKDEL'
        game.completedEncounter()
        db.session.commit()
        return redirect(url_for('main.logout'))

    # If next is hit by POC progress the game status
    if nextForm.submit3.data and nextForm.validate():
        encounter = None
        
        # Update the game time
        game.updateTime()
        db.session.commit()

        # If the game isnt completed
        if int(game.compEnc) < int(game.goalEnc):
            game.selectEncounter()
            game.selectMarch()
            game.completedEncounter()
            
            # Get a random location from the list
            game.location = LOCATION_LIST[randint(0, len(LOCATION_LIST) - 1)]

            db.session.commit()
            
            # Get the next encounter
            encounter = Encounter.query.filter_by(number=game.curEnc).first()
        
        # If the game is completed, complete it
        elif int(game.compEnc) >= int(game.goalEnc):
            game.victory()
            game.completedEncounter()
            db.session.commit()
    
    # If the game is deleted at this point, logout
    if game.mode == "VICTORY" or game.mode == "MARKDEL":
        return redirect(url_for('main.logout'))

    # Get a random map
    if game.randMUpper == '0':
        map = 'DEFAULTTOERRORIMAGE'
    else:
        map = game.curMap + '.PNG'

    # Render the template
    return render_template(['game.html', 'base.html'], prompt=prompt, user=user, game=game, map=map, encounter=encounter, nextForm=nextForm, delForm=delForm)

'''
    Login form
'''
@main.route('/login', methods=['GET', 'POST'])
def login():

    # If the user is already logged in, move them to their game instead
    if current_user.is_authenticated:
        return redirect(url_for('main.game', group=current_user.group))
    
    # Instance all the forms
    joinForm = JoinForm()
    joinFormPOC = JoinFormPOC()
    createForm = CreateForm()

    # If they have joined
    if joinForm.submit1.data and joinForm.validate():
        user = User(group=joinForm.group.data, permission='1')
        db.session.add(user)
        db.session.commit()

        login_user(user)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.game', group=current_user.group)
        return redirect(next_page)

    # If they have joined as host
    if joinFormPOC.submit10.data and joinFormPOC.validate():
        user = User(group=joinForm.group.data, permission='2')
        db.session.add(user)
        db.session.commit()

        login_user(user)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.game', group=current_user.group)
        return redirect(next_page)

    # If they have created a game
    if createForm.submit2.data and createForm.validate():
        user = User(group=createForm.group.data, permission='2')
        db.session.add(user)
        db.session.commit()
        encounters = Encounter.query.all()
        game = Game(group=createForm.group.data, compEnc='1', mode='GAME', curEnc='0')
        game.generateFrequency()
        game.applyCallsign(CALLSIGN_LIST[randint(0,len(CALLSIGN_LIST)-1)] + ' ' + str(randint(1,9)))
        game.location = LOCATION_LIST[randint(0, len(LOCATION_LIST)-1)]
        game.setGoalEnc(20)
        game.setQRandUpper(len(encounters) - 1)
        game.setMRandUpper(19)
        game.selectMarch()
        game.updateTime()
        db.session.add(game)
        db.session.commit()

        login_user(user)
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.game', group=current_user.group)
        return redirect(next_page)

    prompt = Prompt.query.all()[0]

    return render_template(['joinCreate.html', 'base.html'],prompt=prompt, joinForm=joinForm, createForm=createForm, joinFormPOC=joinFormPOC)

'''
    Logout and redirect to main
'''
@main.route('/logout')
def logout():
    logout_user()    
    return redirect(url_for('main.index'))
