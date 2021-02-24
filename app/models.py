from flask_login import UserMixin
from datetime import datetime

from random import randint

from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    timeStamp = db.Column(db.String(120), index=True)

    group = db.Column(db.String(120), index=True)
    compEnc = db.Column(db.String(120), index=True)
    permission = db.Column(db.String(120), index=True)

    def updateTime(self):
        self.timeStamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def __repr__(self):
        return '<User {}>'.format(self.group)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    timeStamp = db.Column(db.String(120), index=True)

    mode = db.Column(db.String(120), index=True, default='GAME')

    group = db.Column(db.String(120), index=True)

    location = db.Column(db.String(120), index=True)
    frequency = db.Column(db.String(120), index=True)
    callsign = db.Column(db.String(120), index=True)

    goalEnc = db.Column(db.String(120), index=True)
    compEnc = db.Column(db.String(120), index=True)

    randQUpper = db.Column(db.String(120), index=True)
    randMUpper = db.Column(db.String(120), index=True)

    curEnc = db.Column(db.String(120), index=True)
    curMap = db.Column(db.String(120), index=True)

    def updateTime(self):
        self.timeStamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def victory(self):
        self.mode = 'VICTORY'

    def generateFrequency(self):
        self.frequency = str(randint(0,9)) + str(randint(0,9)) + str(randint(0,9)) + '.' + str(randint(0,9))

    def applyCallsign(self, string):
        self.callsign = string

    def completedEncounter(self):
        self.compEnc = str(int(self.compEnc) + 1)

    def setGoalEnc(self, i):
        self.goalEnc = str(i)

    def setQRandUpper(self, i):
        self.randQUpper = str(i)

    def setMRandUpper(self, i):
        self.randMUpper = str(i)

    def selectEncounter(self):
        if int(self.randQUpper) <= 0:
            self.curEnc = str(0)
        else:
            self.curEnc = str(int(self.curEnc) + 1)
            if self.curEnc == self.randQUpper:
                self.curEnc = str(0)

    def selectMarch(self):
        if int(self.randMUpper) <= 0:
            self.curMap = str(0)
        else:
            self.curMap = str(randint(0, int(self.randMUpper)))

    def __repr__(self):
        return '<Game {}>'.format(self.group)

class Encounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    number = db.Column(db.String(120), index=True)
    problem = db.Column(db.String(120), index=True)
    solution = db.Column(db.String(120), index=True)

    def __repr__(self):
        return '<Encounter {}>'.format(self.group + ' ' + self.problem + ' ' + self.solution)

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    longText = db.Column(db.String(1000), index=True)

    def setText(self, text):
        self.longText = text

    def __repr__(self):
        return '<Prompt {}>'.format(self.longText)