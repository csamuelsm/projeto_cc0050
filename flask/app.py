from flask import Flask, render_template
import requests
import json
#from waitress import serve

app = Flask(__name__)

base_url = 'https://api.mangadex.org/'
uploads_url = 'https://uploads.mangadex.org/'

@app.route('/')
def root():
    recents_payload = {
        'availableTranslatedLanguage[]': ['pt-br'],
        'publicationDemographic[]': ['shounen']
        }
    recents = requests.get(base_url+'manga', params=recents_payload)
    manga_data = recents.json()['data']
    manga_names = []
    manga_covers = []
    manga_tags = []
    for manga in manga_data:
        manga_names.append(manga['attributes']['title']['en'])
        manga_id = manga['id']
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
                   
    return render_template('index.html', mangas=manga_names, covers=manga_covers, tags=manga_tags, title='CC0026 - Manga Web')

if __name__ == "__main__":
    app.run(debug=True)