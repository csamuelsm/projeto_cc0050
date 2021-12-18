import flask
from flask import Flask, render_template, request
from flask import url_for, redirect, flash, make_response
from waitress import serve
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask import session
from formUsuario import UsuarioForm
from formLogin import LoginForm
from Usuarios import Usuario
from Mangas import Manga
from Favorito import Favorito
import requests
import logging
import hashlib
import os
import json

app = Flask(__name__)
CSRFProtect(app)
CSV_DIR = '/flask/'

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['WTF_CSRF_SSL_STRICT'] = False
Session(app)

logging.basicConfig(filename=CSV_DIR + 'app.log', filemode='w', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + CSV_DIR + 'bd.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

from database import db
db.init_app(app)

base_url = 'https://api.mangadex.org/'
uploads_url = 'https://uploads.mangadex.org/'

@app.before_first_request
def inicializar_bd():
    #db.drop_all()
    db.create_all()

def emoji_lingua(lingua):
    if lingua == 'pt-br':
        return '🇧🇷'
    elif lingua == 'en':
        return '🇬🇧 🇺🇸'
    elif lingua == 'fr':
        return '🇫🇷'
    elif lingua == 'zh' or lingua == 'zh-hk' or lingua == 'zh-ro':
        return '🇨🇳'
    elif lingua == 'es' or lingua == 'es-la':
        return '🇪🇸 🇦🇷'
    elif lingua == 'ja' or lingua == 'ja-ro':
        return '🇯🇵'
    elif lingua == 'ko' or lingua == 'ko-ro':
        return '🇰🇷'
    else:
        return lingua

@app.route('/', methods=('GET', 'POST'))
def root():
    form = LoginForm()
    if form.validate_on_submit():     
        user = request.form['username']
        password = request.form['senha']
        passwordhash = hashlib.sha1(password.encode('utf8')).hexdigest()
        linha = Usuario.query.filter(Usuario.username==user,Usuario.senha==passwordhash).all()
        if (len(linha)>0):
            session['autenticado'] = True
            session['usuario'] = linha[0].id
            return redirect(url_for("manga"))
        else:
            flash(u'Usuário e/ou senha não conferem!')
    return render_template('index.html', form = form, session=session, action=url_for('root'))

@app.route('/logout',methods=['POST','GET'])
def logout():
    session.clear()
    return(redirect(url_for('root')))

@app.route('/mangas', methods=('GET', 'POST'))
def manga():
    recents_payload = {
        'publicationDemographic[]': ['shounen'],
        }
    recents = requests.get(base_url+'manga', params=recents_payload)
    manga_data = recents.json()['data']
    manga_names = []
    manga_covers = []
    manga_tags = []
    manga_descriptions=[]
    manga_ids = []
    for manga in manga_data:
        desc = None
        manga_names.append(manga['attributes']['title'][next(iter(manga['attributes']['title']))])
        manga_descs = manga['attributes']['description']
        if 'pt' in manga_descs:
            desc = manga_descs['pt']
        else:
            desc = manga_descs[next(iter(manga_descs))]
        if len(desc) > 150:
            desc = desc[:150] + '...'
        manga_descriptions.append(desc)
        manga_id = manga['id']
        manga_ids.append(manga_id)
        rel = manga['relationships']
        cover_id = None
        tags = []
        for r in rel:
            if r['type'] == 'cover_art':
                cover_id = r['id']

        for t in manga['attributes']['tags']:
            tags.append(t['attributes']['name']['en'])

        manga_tags.append(tags)
        
        if cover_id != None:
            cover = requests.get(f'{base_url}cover/{cover_id}')
            cover_data = cover.json()['data']['attributes']['fileName']
            cover256 = f'{uploads_url}covers/{manga_id}/{cover_data}.256.jpg'
            manga_covers.append(cover256)

    for i in range(len(manga_names)):
        if len(manga_names[i]) >= 35:
            manga_names[i] = manga_names[i][:35] + '...'
    return render_template('mangas.html', manga_names=manga_names, covers=manga_covers, tags=manga_tags, descriptions=manga_descriptions, ids=manga_ids)

@app.route('/manga/<id>')
def get_manga(id):
    recents_payload = {
        'ids[]': [id],
        }
    recents = requests.get(base_url+'manga', params=recents_payload)
    manga_data = recents.json()['data']
    manga_names = []
    manga_covers = []
    manga_tags = []
    manga_descriptions=[]
    manga_ids = []
    for manga in manga_data:
        desc = None
        manga_names.append(manga['attributes']['title'][next(iter(manga['attributes']['title']))])
        manga_descs = manga['attributes']['description']
        if 'pt' in manga_descs:
            desc = manga_descs['pt']
        else:
            desc = manga_descs[next(iter(manga_descs))]
        manga_descriptions.append(desc)
        manga_id = manga['id']
        manga_ids.append(manga_id)
        rel = manga['relationships']
        cover_id = None
        tags = []
        for r in rel:
            if r['type'] == 'cover_art':
                cover_id = r['id']

        for t in manga['attributes']['tags']:
            tags.append(t['attributes']['name']['en'])

        manga_tags.append(tags)
        
        if cover_id != None:
            cover = requests.get(f'{base_url}cover/{cover_id}')
            cover_data = cover.json()['data']['attributes']['fileName']
            cover256 = f'{uploads_url}covers/{manga_id}/{cover_data}.256.jpg'
            manga_covers.append(cover256)

    '''
    parte em que pego os capitulos abaixo
    '''

    chaps_payload = {
        'manga': id,
        'limit': 100
    }
    capitulos = requests.get(base_url+'chapter', params=chaps_payload)
    capitulos_data = capitulos.json()['data']
    capitulos_id = []
    capitulos_titulo = []
    capitulos_lingua = []
    capitulos_volume = []
    capitulos_capitulo = []
    for capitulo in capitulos_data:
        capitulos_id.append(capitulo['id'])
        titulo = capitulo['attributes']['title']
        capitulos_titulo.append(titulo)
        lingua = capitulo['attributes']['translatedLanguage']
        capitulos_lingua.append(emoji_lingua(lingua))
        volume = capitulo['attributes']['volume']
        capitulos_volume.append(volume)
        chapter = capitulo['attributes']['chapter']
        capitulos_capitulo.append(chapter)

    return render_template('manga.html', session=session, manga_names=manga_names, covers=manga_covers, tags=manga_tags, descriptions=manga_descriptions, ids=manga_ids,
                            capitulos_id = capitulos_id, capitulos_titulo=capitulos_titulo, capitulos_lingua=capitulos_lingua,
                            capitulos_volume=capitulos_volume, capitulos_capitulo=capitulos_capitulo)

@app.route('/capitulo/<id>')
def capitulo(id):
    capitulos = requests.get(base_url+'chapter/'+id)
    hash = capitulos.json()['data']['attributes']['hash']
    manga_id = None
    for r in capitulos.json()['data']['relationships']:
        if r['type'] == 'manga':
            manga_id = r['id']
    capitulos_data = capitulos.json()['data']['attributes']['data']
    chapters_img_hash = []
    for img in capitulos_data:
        chapters_img_hash.append(img)

    base = requests.get(base_url+'at-home/server/'+id)
    uploadsUrl = base.json()['baseUrl']

    capitulo = capitulos.json()['data']['attributes']['chapter']
    volume = capitulos.json()['data']['attributes']['volume']
    titulo = capitulos.json()['data']['attributes']['title']

    manga_data = requests.get(base_url+'manga/'+manga_id)
    manga = manga_data.json()['data']['attributes']['title'][next(iter(manga_data.json()['data']['attributes']['title']))]

    pages = []
    for img in chapters_img_hash:
        pages.append(uploadsUrl+'/data/'+hash+'/'+img)

    return render_template('chapter.html', session=session, pages=pages, manga=manga, capitulo=capitulo, volume=volume, titulo=titulo)

@app.route('/cadastrar', methods=['POST','GET'])
def cadastrar():
    form = UsuarioForm()
    if form.validate_on_submit():
        #PROCESSAMENTO DOS DADOS RECEBIDOS
        name = request.form['nome']
        username = request.form['username']
        email = request.form['email']
        password = request.form['senha']
        passwordhash = hashlib.sha1(password.encode('utf8')).hexdigest()
        novoUsuario = Usuario(nome=name,username=username,email=email,senha=passwordhash)
        db.session.add(novoUsuario)
        db.session.commit()
        flash(u'Usuário cadastrado com sucesso!')
        return(redirect(url_for('root')))
    return (render_template('cadastro.html', form=form, session=session, action=url_for('cadastrar')))

'''
@app.route('/manga/<id>/favoritar')
'''

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=80, url_prefix='/app')