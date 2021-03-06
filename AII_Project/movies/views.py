import re, os, shutil
from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import csv
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup

# Create your views here.
def imdb_scrape(request):
    if request.method == "POST":
        webiste_url = 'https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250'

        list_of_titles = []
        list_of_years = []
        user_ratings = []

        source = requests.get(webiste_url).text
        soup = BeautifulSoup(source, 'lxml')

        print(soup.title.text)

        tbody = soup.tbody
        table_rows = tbody.find_all('tr')

        for td in table_rows:
            titles_column = td.find_all('td', class_="titleColumn")
            imdb_ratings = td.find_all('td', class_="ratingColumn imdbRating")

            for information in titles_column:
                title = information.a.text
                list_of_titles.append(title)
                year = information.span.text
                list_of_years.append(year)

            for rating in imdb_ratings:
                user_rating = rating.text.strip()
                user_ratings.append(user_rating)

        csv_file = open('tv_shows.csv', 'w', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Title', 'Year of Release', 'User Rating'])

        for i in range(len(user_ratings)):
            print(list_of_titles[i], "Year", list_of_years[i], "| Rating:", user_ratings[i])
            csv_writer.writerow([list_of_titles[i], list_of_years[i], user_ratings[i]])

        csv_file.close()

        return render(request, 'bs.html', {'result':'The database has been loaded successfully!'})
    
    return render(request, 'bs.html')

def imdb_search(request):
    almacenar_datos()
    return render(request, 'whoosh.html')

def imdb_search_title(request):
    if request.method == "POST":
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = QueryParser("title", ix.schema).parse(str(request.POST.get('title')))
            results = searcher.search(query, limit=25) # Solo devuelve los 25 primeros
            result = str()
            for r in results:
                result = result + 'Title: '+r['title'] + ', Year: '+str(r['year']) + ', Rating: '+str(r['rating']) + '|'
            res = result.split("|")
            res = res[:-1]
        return render(request, 'whoosh.html', {'result':res})
    return render(request, 'whoosh.html')

def imdb_search_year(request):
    if request.method == "POST":
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = QueryParser("year", ix.schema).parse(str(request.POST.get('year')))
            results = searcher.search(query, limit=25) # Solo devuelve los 25 primeros
            result = str()
            for r in results:
                result = result + 'Title: '+r['title'] + ', Year: '+str(r['year']) + ', Rating: '+str(r['rating']) + '|'
            res = result.split("|")
            res = res[:-1]
        return render(request, 'whoosh.html', {'result':res})
    return render(request, 'whoosh.html')

def imdb_search_rating(request):
    if request.method == "POST":
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = QueryParser("rating", ix.schema).parse(str(request.POST.get('rating')))
            results = searcher.search(query, limit=25) # Solo devuelve los 25 primeros
            result = str()
            for r in results:
                result = result + 'Title: '+r['title'] + ', Year: '+str(r['year']) + ', Rating: '+str(r['rating']) + '|'
            res = result.split("|")
            res = res[:-1]
        return render(request, 'whoosh.html', {'result':res})
    return render(request, 'whoosh.html')

def imdb_search_all(request):
    if request.method == "POST":
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = MultifieldParser(["title","year","rating"], ix.schema, group=OrGroup).parse(str(request.POST.get('all')))
            results = searcher.search(query, limit=25) # Solo devuelve los 25 primeros
            result = str()
            for r in results:
                result = result + 'Title: '+r['title'] + ', Year: '+str(r['year']) + ', Rating: '+str(r['rating']) + '|'
            res = result.split("|")
            res = res[:-1]
        return render(request, 'whoosh.html', {'result':res})
    return render(request, 'whoosh.html')

def almacenar_datos():
    # Define el esquema de la información
    schem = Schema(title=TEXT(stored=True), year=NUMERIC(stored=True), rating=TEXT(stored=True))
    # Eliminamos el directorio del Indice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    # Creamos el Indice
    ix = create_in("Index", schema=schem)
    # Creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    i=0
    lista=extraer_peliculas()
    for pelicula in lista:
        # Añade cada pelicula de la lista al índice
        writer.add_document(title=str(pelicula['title']), year=int(pelicula['year']), rating=str(pelicula['rating']))    
        i+=1
    writer.commit()
    print('Fin de indexado.', 'Se han indexado ' + str(i) + ' peli­culas')

def extraer_peliculas():
    result = []
    with open("tv_shows.csv",'r') as csvfile:
        reader = csv.reader(csvfile,delimiter=',')
        next(reader, None)
        for row in reader:
            year = row[1].replace("(","").replace(")","") # Mapear el año porque viene entre parentesis
            result.append({'title':row[0],'year':year,'rating':row[2]})
    return result
