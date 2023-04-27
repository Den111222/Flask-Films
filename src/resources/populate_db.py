import datetime
import threading
import bs4
import requests
from flask_restful import Resource
from src import db
from src.services.film_service import FilmService
from concurrent.futures.process import ProcessPoolExecutor as PoolExecutor


class PopulateDB(Resource):
    url = 'https://www.metacritic.com/'

    def post(self):
        t0 = datetime.datetime.now()
        films_urls = self.get_films_urls()
        for film_url in films_urls:
            films = self.parse_films(film_url)

        created_films = self.populate_db_with_films(films)
        dt = datetime.datetime.now() - t0
        print(f'Done in {dt.total_seconds():.2f} sec.')
        return {'message': f'Database were populated with {created_films} films\n'
                           f'Done in {dt.total_seconds():.2f} sec.'}, 201

    def get_films_urls(self):
        print('Getting film urls', flush=True)
        url = self.url + 'browse/movies/score/userscore/year/filtered/'
        headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text
        soup = bs4.BeautifulSoup(html, features='html.parser')
        movie_containers = soup.find_all('a', class_='title')
        movie_links = [movie['href'] for movie in movie_containers][:100]
        return movie_links

    def parse_films(self, film_url, films_to_create = []):
        url = self.url + film_url
        print(f'Getting a detailed info about the film - {url}')
        headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
        }
        film_content = requests.get(url, headers=headers)
        film_content.raise_for_status()
        html = film_content.text
        soup = bs4.BeautifulSoup(html, features="html.parser")
        title = soup.find('div', class_='product_page_title oswald').text.split('\n')[1]
        if soup.find('span', class_='metascore_w user larger movie positive') is not None:
            rating = float(soup.find('span', class_='metascore_w user larger movie positive').text)
        elif soup.find('span', class_='metascore_w user larger movie mixed') is not None:
            rating = float(soup.find('span', class_='metascore_w user larger movie mixed').text)
        else:
            rating = float(soup.find('span', class_='metascore_w user larger movie negative').text)
        description_bar = soup.find('div', class_='summary_deck details_section')
        if description_bar.find('span', class_='blurb blurb_expanded') is not None:
            description = description_bar.find('span', class_='blurb blurb_expanded').text
        elif soup.find('div', class_='summary_deck details_section') is not None:
            description = soup.find('div', class_='summary_deck details_section').text
        else:
            description = ''
        title_bar = soup.find('span', class_='release_date').text.strip('\n')
        title_content = title_bar.split('\n')
        release_date = title_content[-1]
        release_date = datetime.datetime.strptime(release_date, '%B %d, %Y')
        try:
            length = float(soup.find('div', class_='runtime').text.split('\n')[2].split(' ')[0])
        except:
            length = float()
        print(f'Received information about - {title}', flush=True)
        films_to_create.append(
            {
                'title': title,
                'rating': rating,
                'description': description,
                'release_date': release_date,
                'length': length,
                'distributed_by': 'Warner Bros. Pictures',
            }
        )
        return films_to_create

    @staticmethod
    def populate_db_with_films(films):
        return FilmService.bulk_create_films(db.session, films)

class PopulateDBThreaded(PopulateDB):

    def post(self):
        threads = []
        films_to_create = []
        t0 = datetime.datetime.now()
        film_urls = self.get_films_urls()
        for film_url in film_urls:
            threads.append(threading.Thread(target=self.parse_films, args=(film_url, films_to_create), daemon=True))
        [t.start() for t in threads]
        [t.join() for t in threads]
        created_films = self.populate_db_with_films(films_to_create)
        dt = datetime.datetime.now() - t0
        print(f"Done in {dt.total_seconds():.2f} sec.")
        return {'message': f'Database were populated with {created_films} films.\n'
                           f'Done in {dt.total_seconds():.2f} sec.'}, 201

class PopulateDBThreadPoolExecutor(PopulateDB):

    def post(self):
        t0 = datetime.datetime.now()
        film_urls = self.get_films_urls()
        work = []
        with PoolExecutor() as executor:
            for film_url in film_urls:
                f = executor.submit(self.parse_films, film_url)
                work.append(f)
        films_to_create = [f.result()[0] for f in work]
        created_films = self.populate_db_with_films(films_to_create)
        dt = datetime.datetime.now() - t0
        print(f"Done in {dt.total_seconds():.2f} sec.")
        return {'message': f'Database were populated with {created_films} films. \n'
                           f'Done in {dt.total_seconds():.2f} sec.'}, 201


