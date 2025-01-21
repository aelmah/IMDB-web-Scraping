import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import io
import matplotlib.pyplot as plt
import seaborn as sns

def scrape_movies(base_url, min_imdb=7.0, genre=None, actor=None, director=None, country=None, duration=None, release_year=None):
    page = 1

    while True:
        url = base_url if page == 1 else f'{base_url}page/{page}/'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            movie_boxes = soup.find_all('div', {'class': 'card h-100 border-0 shadow'})

            if not movie_boxes:
                break

            for movie in tqdm(movie_boxes, desc=f"Scraping page {page}", unit="movie"):
                try:
                    title = movie.find('h2', class_='card-title text-light fs-6 m-0').get_text(strip=True)
                    link = movie.find('a', class_='rounded poster')['href']
                   
                    movie_response = requests.get(link)

                    if movie_response.status_code == 200:
                        
                        movie_soup = BeautifulSoup(movie_response.content, 'lxml')
                        moviee = movie_soup.find('div', {'class': 'col-12 col-lg-7 border-sm-end'})
                        
                        description = moviee.contents[1].get_text(strip=True)

                        genre_temp = moviee.contents[2].get_text(strip=True).split("Actor")[0]
                        movie_genre = genre_temp.split(":")[1].strip()

                        actor_temp = moviee.contents[2].get_text(strip=True).split("Director")[0]
                        movie_actor = actor_temp.split(":")[2].strip()

                        director_temp = moviee.contents[2].get_text(strip=True).split("Director:")[1]
                        movie_director = director_temp.split("Country:")[0].strip()

                        country_temp = moviee.contents[2].get_text(strip=True).split("Country:")[1]
                        movie_country = country_temp.split("Quality")[0].strip()

                        duration_temp = moviee.contents[2].get_text(strip=True).split("Duration:")[1]
                        movie_duration = duration_temp.split("Release:")[0].strip()

                        release_temp = moviee.contents[2].get_text(strip=True).split("Release:")[1]
                        movie_release = release_temp.split("IMDb:")[0].strip()

                        imdb_temp = moviee.contents[2].get_text(strip=True).split("IMDb:")[1]
                        movie_imdb = imdb_temp.split("/")[0].strip()

                        if((genre is None or genre.lower() in movie_genre.lower()) and 
                            (actor is None or actor.lower() in movie_actor.lower()) and 
                            (director is None or director.lower() in movie_director.lower()) and 
                            (country is None or country.lower() in movie_country.lower()) and
                            (duration is None or duration.lower() in movie_duration.lower()) and 
                            (release_year is None or release_year in movie_release) and 
                            (movie_imdb != '-' and float(movie_imdb) >= min_imdb)):
                               
                               
                           st.session_state.movies_data.append([title, link, description, movie_genre, movie_actor, movie_director, movie_country, movie_duration, movie_release, movie_imdb])
                except Exception as e:
                    st.error(f"Error processing a movie: {e}")

            page += 1
        else:
            print(f"Error retrieving page {page}. Status code: {response.status_code}")
            break

def convert_to_minutes(duration):
    if isinstance(duration, str):
        if 'h' in duration:
            parts = duration.split('h') 
            hours = parts[0].strip()  
            minutes = parts[1].strip().replace('m', '') if len(parts) > 1 else '0'  
            return int(hours) * 60 + int(minutes)  
        else:
            return int(duration.replace('m', ''))  
    else:
        return 0  

st.set_page_config(page_title="Movie Scraper", layout="wide")
st.title("🎬 Movie Scraper Tool")
st.divider()
st.markdown("Scrape movie data from 123Movies based on your preferences.")
if 'movies_data' not in st.session_state:
    st.session_state.movies_data = []  
if 'stop_scraping' not in st.session_state:
    st.session_state.stop_scraping = False 

with st.sidebar:
    st.header("🔍 Filter Options")
    min_imdb = st.slider("Minimum IMDb Rating", 0.0, 10.0, 7.0, 0.1)
    genre = st.text_input("Genre")
    actor = st.text_input("Actor")
    director = st.text_input("Director")
    country = st.text_input("Country")
    duration = st.text_input("Duration (e.g., 120 min)")
    release_year = st.text_input("Release Year")
    start_scraping = st.button("🚀 Start Scraping")
    stop_scraping = st.button("⛔ Stop Scraping")


if stop_scraping:
    st.session_state.stop_scraping = True

if start_scraping:
    st.session_state.stop_scraping = False
    st.session_state.movies_data = []   
    st.info("Scraping in progress...")
    base_url = 'https://ww4.123moviesfree.net/movies/'
    scrape_movies(base_url, min_imdb, genre, actor, director, country, duration, release_year)

if st.session_state.movies_data:
    df = pd.DataFrame(st.session_state.movies_data, columns=[
                      'Title', 'Link', 'Description', 'Genre', 'Actors', 'Director', 'Country', 'Duration', 'Release', 'IMDb'])
    st.success(f"Scraping completed or stopped! Found {len(st.session_state.movies_data)} movies.")
    st.dataframe(df)
    
    csv_file = io.StringIO()
    df.to_csv(csv_file, index=False)
    csv_bytes = csv_file.getvalue().encode()
    st.download_button("📥 Download CSV", data=csv_bytes, file_name="movies_list.csv", mime='text/csv')

    if st.button("📊 Show statistics",help="show statistics"):
        # st.balloons()
        st.subheader("Movie Statistics")
        #1. imdb rating 
        st.subheader("1. IMDb Rating Distribution")
        plt.figure(figsize=(12, 7))
        bins = [i for i in range(0, 11)]
        sns.histplot(df['IMDb'].astype(float), bins=bins, kde=True, color='skyblue', edgecolor='black', alpha=0.8, linewidth=1.5)
        kde_curve = sns.kdeplot(df['IMDb'].astype(float), color='darkblue', linewidth=2, label='Courbe KDE')
        plt.title('Distribution des notes IMDb', fontsize=18, pad=20)
        plt.xlabel('Note IMDb', fontsize=14)
        plt.ylabel('Nombre de films', fontsize=14)
        plt.xticks(bins)
        mean_rating = df['IMDb'].astype(float).mean()
        plt.axvline(mean_rating, color='red', linestyle='--', linewidth=2, label=f'Moyenne : {mean_rating:.2f}')
        plt.legend()
        st.pyplot(plt) 
        
        #2. top 10 most popular genres
        st.subheader("2. Number of Movies by Genre (Top 10)")
        plt.figure(figsize=(12, 7))
        genre_counts = df['Genre'].value_counts().nlargest(10)
        barplot = sns.barplot(
            x=genre_counts.values,  
            y=genre_counts.index,  
            orient='h',             
            palette='viridis',      
            alpha=0.9,              
            edgecolor='black'      
        )
        i = 0  
        for value in genre_counts.values:
            barplot.text(value + 0.1,i,f'{int(value)}',va='center',fontsize=12,color='black')
            i += 1
        plt.title('Top 10 Most Popular Genres', fontsize=18, pad=20)  
        plt.xlabel('Number of Movies', fontsize=14)                  
        plt.ylabel('Genre', fontsize=14)                            
        plt.xticks([])         
        st.pyplot(plt)
        
        # 3. release year distribution
        st.subheader("3. Distribution of Movie Release Years")
        df['Release'] = pd.to_numeric(df['Release'], errors='coerce').dropna()
        min_year = int(df['Release'].min())
        max_year = int(df['Release'].max())
        bins = range(min_year, max_year + 1)
        plt.figure(figsize=(12, 7))
        sns.histplot(df['Release'], bins=bins,kde=True, color='skyblue',edgecolor='black', alpha=0.8,linewidth=1.5) 
        plt.title('Distribution of Movie Release Years', fontsize=18, pad=20)  
        plt.ylabel('Number of Movies', fontsize=14)
        plt.xticks(range(min_year, max_year + 1, 5))  
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        st.pyplot(plt)
        
        # 4. Most Frequent Actors Chart
        st.subheader("4. Top 10 Most Frequent Actors")
        plt.figure(figsize=(12, 7))
        df_actors = df[df['Actors'].notna() & (df['Actors'].str.strip() != '')]
        actors_series = df_actors['Actors'].str.split(r',\s*', expand=True).stack()
        actors_series = actors_series[actors_series != "-"]
        actors_counts = actors_series.value_counts().head(10)
        sns.barplot(
            x=actors_counts.values, 
            y=actors_counts.index,   
            orient='h',             
            palette='viridis',       
            alpha=0.9,              
            edgecolor='black'        
        )  
        i = 0
        for value in actors_counts.values:
            plt.text(value + 0.05, i, f'{int(value)}', va='center', fontsize=12,color='black')
            i+=1
        plt.title('Top 10 Most Frequent Actors', fontsize=18, pad=20)
        plt.xlabel('Number of Movies', fontsize=14)
        plt.ylabel('Actor', fontsize=14)
        plt.xticks([])
        st.pyplot(plt)
        
        # 5. Most Frequent Director 
        st.subheader("5. Top 10 Most Frequent Directos")
        plt.figure(figsize=(12, 7))
        df_actors = df[df['Director'].notna() & (df['Director'].str.strip() != '')]
        director_series = df_actors['Director'].str.split(r',\s*', expand=True).stack()
        director_series = director_series[director_series != "-"]
        director_counts = director_series.value_counts().head(10)
        sns.barplot(
            x=director_counts.values, 
            y=director_counts.index,   
            orient='h',              
            palette='viridis',       
            alpha=0.9,               
            edgecolor='black'       
        )
        i=0
        for value in director_counts.values:
            plt.text(value + 0.05, i, f'{int(value)}', va='center', fontsize=12,color='black')
            i+=1
        plt.title('Top 10 Most Frequent Directors', fontsize=18, pad=20)
        plt.xlabel('Number of Movies', fontsize=14)
        plt.ylabel('Director', fontsize=14)
        plt.xticks([])
        st.pyplot(plt)  
        
        # # 6. Movie Duration Distribution 
        st.subheader("6. Movie Duration Distribution")
        plt.figure(figsize=(12, 7))
        df['Duration_min'] = df['Duration'].apply(convert_to_minutes)
        df = df[df['Duration_min'] > 0]
        sns.histplot(df['Duration_min'], kde=True, color='skyblue', edgecolor='black', alpha=0.8, linewidth=1.5)
        plt.title('Distribution of Movie Durations', fontsize=18, pad=20)
        plt.xlabel('Duration (minutes)', fontsize=14)
        plt.ylabel('Number of Movies', fontsize=14)
        st.pyplot(plt)
        
        # 7. Top 10 Countries with Most Movies
        st.subheader("7. Top 10 Countries with Most Movies")
        plt.figure(figsize=(12, 7))
        df_countries = df[df['Country'].notna() & (df['Country'].str.strip() != '')]
        countries_series = df_countries['Country'].str.split(r',\s*', expand=True).stack()
        countries_counts = countries_series.value_counts().head(10)
        barplot = sns.barplot(
            x=countries_counts.values,  
            y=countries_counts.index,   
            orient='h',                
            palette='viridis',          
            alpha=0.9,                 
            edgecolor='black'           
        )
        i=0
        for value in countries_counts.values:
            plt.text(value + 0.1, i,f'{int(value)}', va='center',fontsize=12, color='black')
            i+=1
        plt.xticks([]) 
        plt.xlabel('Number of Movies', fontsize=14)
        plt.title('Top 10 Countries with Most Movies', fontsize=18, pad=20)
        plt.ylabel('Country', fontsize=14)
        st.pyplot(plt)
        
        # 8. Correlation Between Movie Duration and IMDb Rating
        st.subheader("8. Correlation Between Movie Duration and IMDb Rating")
        df['IMDb'] = pd.to_numeric(df['IMDb'], errors='coerce')
        df['Duration_min'] = df['Duration'].apply(convert_to_minutes)
        df = df.dropna(subset=['Duration_min', 'IMDb'])
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=df['Duration_min'], y=df['IMDb'], color='skyblue', alpha=0.8)
        sns.regplot(x=df['Duration_min'], y=df['IMDb'], scatter=False, color='red') 
        plt.title('Correlation Between Movie Duration and IMDb Rating', fontsize=18, pad=20)
        plt.xlabel('Duration (minutes)', fontsize=14)
        plt.ylabel('IMDb Rating', fontsize=14)
        st.pyplot(plt)
        
elif start_scraping and not st.session_state.movies_data:
    st.warning("No movies found with the selected filters.")