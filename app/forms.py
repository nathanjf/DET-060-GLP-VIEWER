from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError, DataRequired
from wtforms_validators import AlphaNumeric

from app.models import Game

class DeleteForm(FlaskForm):
    submit11 = SubmitField('Delete')

class JoinForm(FlaskForm):
    group = StringField('Group Code', validators=[DataRequired(), AlphaNumeric()])
    submit1 = SubmitField('Join')

    def validate_group(self, group):
        game = Game.query.filter_by(group=group.data).first()
        if game is None:
            raise(ValidationError('Game does not exist'))

class JoinFormPOC(FlaskForm):
    group = StringField('Group Code', validators=[DataRequired(), AlphaNumeric()])
    submit10 = SubmitField('Join')

    def validate_group(self, group):
        game = Game.query.filter_by(group=group.data).first()
        if game is None:
            raise(ValidationError('Game does not exist'))

class CreateForm(FlaskForm):
    group = StringField('Group Code', validators=[DataRequired(), AlphaNumeric()])
    submit2 = SubmitField('Create')

    def validate_group(self, group):
        game = Game.query.filter_by(group=group.data).first()
        if game is not None:
            raise ValidationError('Game already exists')

class NextForm(FlaskForm):
    submit3 = SubmitField('Next')


