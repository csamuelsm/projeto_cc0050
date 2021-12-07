import flask
from flask import Flask, render_template, request
import requests
import json
#from waitress import serve

app = Flask(__name__)

base_url = 'https://api.mangadex.org/'
uploads_url = 'https://uploads.mangadex.org/'

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
    if request.method == 'POST':     
        user = request.form['user']
        password = request.form['password']
        if user == 'testing' and password == 'testing':
            return flask.redirect('/mangas')
    return render_template('index.html')

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

    return render_template('manga.html', manga_names=manga_names, covers=manga_covers, tags=manga_tags, descriptions=manga_descriptions, ids=manga_ids,
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

    return render_template('chapter.html', pages=pages, manga=manga, capitulo=capitulo, volume=volume, titulo=titulo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)