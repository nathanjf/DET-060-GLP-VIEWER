import os
import sys
import string

from app import create_app, db

from app import db
from app.models import User
from app.models import Game
from app.models import Encounter

from json import load
from pprint import pprint

def loadEncounters():
    encDict = {}

    with open(sys.path[0] + os.sep + 'app' + os.sep + 'static' + os.sep + 'text' + os.sep + 'encounters.json', 'r', encoding="utf8") as f:
        encDict = load(f) 
        f.close()

    pprint(encDict, indent=4)

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
