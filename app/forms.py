from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, DataRequired, Email, EqualTo, Length

from app.models import User, Game


class DeleteForm(FlaskForm):
    submit11 = SubmitField('Delete')

class JoinForm(FlaskForm):
    group = StringField('Group Code', validators=[DataRequired()])
    submit1 = SubmitField('Join')

    def validate_group(self, group):
        game = Game.query.filter_by(group=group.data).first()
        if game is None:
            raise(ValidationError('Game does not exist'))

class JoinFormPOC(FlaskForm):
    group = StringField('Group Code', validators=[DataRequired()])
    submit10 = SubmitField('Join')

    def validate_group(self, group):
        game = Game.query.filter_by(group=group.data).first()
        if game is None:
            raise(ValidationError('Game does not exist'))

class CreateForm(FlaskForm):
    group = StringField('Group Code', validators=[DataRequired()])
    submit2 = SubmitField('Create')

    def validate_group(self, group):
        game = Game.query.filter_by(group=group.data).first()
        if game is not None:
            raise ValidationError('Game already exists')


class NextForm(FlaskForm):
    submit3 = SubmitField('Next')


class RefreshForm(FlaskForm):
    submit4 = SubmitField('Refresh')


class Advance16(FlaskForm):
    submit5 = SubmitField('Advance')
