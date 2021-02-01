import os
import sys
import string

from app import create_app, db

from app import db
from app.models import User
from app.models import Game
from app.models import Encounter
from app.models import Prompt

from json import load
from pprint import pprint

def loadEncounters():
    encDict = {}
    promptDict = {}

    with open(sys.path[0] + os.sep + 'app' + os.sep + 'static' + os.sep + 'text' + os.sep + 'encounters.json', 'r', encoding="utf8") as f:
        encDict = load(f) 
        f.close()

    with open(sys.path[0] + os.sep + 'app' + os.sep + 'static' + os.sep + 'text' + os.sep + 'prompt.json', 'r', encoding="utf8") as f:
        promptDict = load(f)
        f.close()

    prompt = Prompt(longText=promptDict['prompt'])
    db.session.add(prompt)
    db.session.commit()

    # Delete all games
    db.session.query(Game).delete()
    db.session.query(User).delete()
    db.session.query(Encounter).delete()
    db.session.commit()

    # Add current things to SQL
    for key in encDict:
        encounter = Encounter(number=key, problem=encDict[key]['problem'], solution=encDict[key]['solution'])
        db.session.add(encounter)

    db.session.commit()

app = create_app()
app.app_context().push()
loadEncounters()
