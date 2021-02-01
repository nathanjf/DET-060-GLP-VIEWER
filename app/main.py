from random import randint
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask.globals import current_app
from flask_login import current_user, login_user, logout_user, login_required
from flask_migrate import current
from werkzeug.urls import url_parse

from datetime import datetime

import app
from app import create_app
from app import db
from app.models import User, Game, Encounter, Prompt
from app.forms import JoinForm, CreateForm, NextForm, RefreshForm, Advance16, JoinFormPOC, DeleteForm
from app import sched

from flask_apscheduler import APScheduler
import os
from os import listdir

main = Blueprint('main', __name__)

MAP_PATH = os.sep + 'static' + os.sep + 'images' + os.sep + 'maps'

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

# Purge all users and games that are older than xTime
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

# Purge all games and users that are currently in a victory state
@sched.task('interval', id='do_job_2', seconds=30, misfire_grace_time=30)
def job2():
    print('job2 Triggered')
    with db.app.app_context():
        games = Game.query.all()
        for game in games:
            if game.mode == 'VICTORY' or game.mode == 'MARKDEL':
                users = User.query.filter_by(group=game.group)
                for user in users:
                    print('Deleting User: ' + user.group)
                    db.session.delete(user)
                    db.session.commit()
                print('Deleting Game: ' + game.group)
                db.session.delete(game)
                db.session.commit()

@main.route('/')
@main.route('/index')
def index():
    return redirect(url_for('main.login'))

@main.route('/game/<group>/status', methods=['GET'])
@login_required
def gameStatus(group):
    user = current_user
    age = (datetime.now() - datetime.strptime(user.timeStamp, "%d/%m/%Y %H:%M:%S"))
    age = age.total_seconds()
    age = round(age/60, 1)
    game = Game.query.filter_by(group=user.group).first()
 
    return jsonify({'compEnc' : game.compEnc, 'age': str(age)})

@main.route('/browser', methods=['GET', 'POST'])
def browser():
    games = Game.query.all()
    lenGames = len(games)

    return render_template(['browser.html', 'base.html'], games=games, lenGames=lenGames)

@main.route('/game/<group>', methods=['GET', 'POST'])
@login_required
def game(group):
    user = current_user
    game = Game.query.filter_by(group=user.group).first()
    prompt = Prompt.query.all()[0]
    encounter = Encounter.query.filter_by(number=game.curEnc).first()

    user.updateTime()
    game.updateTime()

    user.compEnc = game.compEnc
    db.session.commit()

    # If the game isnt there log them out
    if game is None:
        return redirect(url_for('main.logout'))

    if game.mode == "VICTORY" or game.mode == "MARKDEL":
        return redirect(url_for('main.logout'))

    refreshForm = RefreshForm()
    nextForm = NextForm()
    delForm = DeleteForm()

    if delForm.submit11.data and delForm.validate():
        game.mode = 'MARKDEL'
        game.completedEncounter()
        db.session.commit()
        return redirect(url_for('main.logout'))

    # If refresh is hit
    if refreshForm.submit4.data and refreshForm.validate():
        return redirect(url_for('main.index'))

    # If next is hit by POC
    if nextForm.submit3.data and nextForm.validate():
        encounter = None
        
        game.updateTime()
        db.session.commit()

        if int(game.compEnc) < int(game.goalEnc):
            game.selectEncounter()
            game.selectMarch()

            game.completedEncounter()
            
            game.location = LOCATION_LIST[randint(0, len(LOCATION_LIST) - 1)]

            db.session.commit()

            encounter = Encounter.query.filter_by(number=game.curEnc).first()
        
        elif int(game.compEnc) >= int(game.goalEnc):
            game.victory()
            game.completedEncounter()
            
            db.session.commit()
    
    if game.mode == "VICTORY" or game.mode == "MARKDEL":
        return redirect(url_for('main.logout'))

    if game.randMUpper == '0':
        map = 'DEFAULTTOERRORIMAGE'
    else:
        map = game.curMap + '.PNG'

    return render_template(['game.html', 'base.html'], prompt=prompt, user=user, game=game, map=map, encounter=encounter, nextForm=nextForm, refreshForm=refreshForm, delForm=delForm)

@main.route('/login', methods=['GET', 'POST'])
def login():

    # If the user is already logged in, move them to their game instead
    if current_user.is_authenticated:
        return redirect(url_for('main.game', group=current_user.group))
    
    joinForm = JoinForm()
    joinFormPOC = JoinFormPOC()
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

    if joinFormPOC.submit10.data and joinFormPOC.validate():
        user = User(group=joinForm.group.data, permission='2')
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

@main.route('/logout')
def logout():

    # Just really bad code

    #if current_user.permission == '2':
        #game = Game.query.filter_by(group=current_user.group).first()
        #db.session.delete(game)
        #db.session.commit()

        #users = User.query.filter_by(group=current_user.group)
        #for user in users:
        #    db.session.delete(user)
        #    db.session.commit()

    logout_user()    
    return redirect(url_for('main.index'))
