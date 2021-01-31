from random import randint
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask.globals import current_app
from flask_login import current_user, login_user, logout_user, login_required
from flask_migrate import current
from werkzeug.urls import url_parse

import app
from app import create_app
from app import db
from app.models import User, Game, Encounter
from app.forms import JoinForm, CreateForm, NextForm, RefreshForm, Advance16
from app import sched

from flask_apscheduler import APScheduler
import os
from os import listdir

main = Blueprint('main', __name__)

#app = create_app()

MAP_PATH = os.sep + 'app' + os.sep + 'static' + os.sep + 'images' + os.sep + 'maps'
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
    'DEER',
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

@sched.task('interval', id='do_job_1', seconds=60, misfire_grace_time=900)
def job1():
    with db.app.app_context(): 
        print("Running job")
        games = Game.query.all()
        for game in games:
            if User.query.filter_by(group=game.group).first() == None:
                print("Removed Game", game.group)
                db.session.delete(game)
                db.session.commit()

@main.route('/')
@main.route('/index')
def index():
    return redirect(url_for('main.login'))

@main.route('/game/<group>/status', methods=['GET'])
def gameStatus(group):
    user = current_user
    game = Game.query.filter_by(group=user.group).first()
    return jsonify({'compEnc' : game.compEnc})

@main.route('/game/<group>', methods=['GET', 'POST'])
def game(group):
    user = current_user
    game = Game.query.filter_by(group=user.group).first()
    encounter = Encounter.query.filter_by(number=game.curEnc).first()

    user.compEnc = game.compEnc
    db.session.commit()

    # If the game isnt there log them out
    if game is None:
        return redirect(url_for('main.logout'))

    refreshForm = RefreshForm()
    nextForm = NextForm()

    # If refresh is hit
    if refreshForm.submit4.data and refreshForm.validate():
        return redirect(url_for('main.index'))

    # If next is hit by POC
    if nextForm.submit3.data and nextForm.validate():
        encounter = None

        if int(game.compEnc) < int(game.goalEnc):
            game.selectEncounter()
            game.selectMarch()

            game.completedEncounter()

            db.session.commit()

            encounter = Encounter.query.filter_by(number=game.curEnc).first()
        
        elif int(game.compEnc) >= int(game.goalEnc):
            game.victory()
            game.completedEncounter()
            
            db.session.commit()

            '''
                Some sort of redirect to a game specific victory screen that has a quit button on it.  When a user quits manually destroy their user model
            '''
    
    if game.mode == "VICTORY":
        return redirect(url_for('main.logout'))

    map = listdir(os.getcwd() + MAP_PATH)
    if len(map) == 0:
        map = 'DEFAULTTOERRORIMAGE'
    else:
        map = map[int(game.curMap)]

    data = {'group' : game.group}

    return render_template(['game.html', 'base.html'], user=user, game=game, map=map, encounter=encounter, nextForm=nextForm, refreshForm=refreshForm, data=data)

@main.route('/login', methods=['GET', 'POST'])
def login():

    # If the user is already logged in, move them to their game instead
    if current_user.is_authenticated:
        return redirect(url_for('main.game', group=current_user.group))
    
    joinForm = JoinForm()
    createForm = CreateForm()

    if joinForm.submit1.data and joinForm.validate():
        user = User(group=joinForm.group.data, permission='1')
        flash('Joined game ' + user.group)
        db.session.add(user)
        db.session.commit()

        login_user(user)

        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.game', group=current_user.group)

        return redirect(next_page)

    if createForm.submit2.data and createForm.validate():
        user = User(group=createForm.group.data, permission='2')
        db.session.add(user)
        db.session.commit()

        # Count amount of encounters and count amount of images in the map folder
        encounters = Encounter.query.all()

        game = Game(group=createForm.group.data, compEnc='1', mode='GAME')
        
        game.generateFrequency()
        game.applyCallsign(CALLSIGN_LIST[randint(0,len(CALLSIGN_LIST)-1)] + ' ' + str(randint(0,20)))

        game.setGoalEnc(5)
        game.setQRandUpper(len(encounters) - 1)
        game.setMRandUpper(len(listdir(os.getcwd() + MAP_PATH)) - 1)
        
        print(len(encounters))
        print(len(listdir(os.getcwd() + MAP_PATH)))

        game.selectMarch()
        game.selectEncounter()

        db.session.add(game)
        db.session.commit()

        login_user(user)

        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.game', group=current_user.group)

        return redirect(next_page)

    return render_template(['joinCreate.html', 'base.html'], joinForm=joinForm, createForm=createForm)

@main.route('/logout')
def logout():
    #if current_user.permission == '2':
        #game = Game.query.filter_by(group=current_user.group).first()
        #db.session.delete(game)
        #db.session.commit()

        #users = User.query.filter_by(group=current_user.group)
        #for user in users:
        #    db.session.delete(user)
        #    db.session.commit()

    user = User.query.filter_by(id=current_user.id).first()

    logout_user()

    db.session.delete(user)
    db.session.commit()
    
    return redirect(url_for('main.index'))
