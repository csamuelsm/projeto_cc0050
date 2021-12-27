from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired

class PesquisaForm(FlaskForm):
    pesquisa = StringField(u'Pesquisar mangá ', validators=[DataRequired()])
    enviar = SubmitField('Pesquisar')