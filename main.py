from symbol import parameters

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from forms import MovieEditForm, MovieAddForm
import os
from dotenv import load_dotenv

load_dotenv(".env")
MOVIE_DB_URL = "https://api.themoviedb.org/3/search/movie"
SELECT_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
bearer_token = os.getenv("movie_db_read_access_token")


'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
movie_api_key = os.getenv('movie_db_api_key')
# CREATE DB
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)
# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)



with app.app_context():
    db.create_all()



# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
#
# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
#
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.add(second_movie)
#     db.session.commit()




@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))

    all_movies= result.scalars().all()

    for i in range(len(all_movies)):

        all_movies[i].ranking=len(all_movies)-i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    edit_form = MovieEditForm()

    if edit_form.validate_on_submit():
        # print(edit_form.review.data)
        movie_selected.rating=float(edit_form.rating.data)
        movie_selected.review=edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    edit_form.rating.data=movie_selected.rating
    edit_form.review.data=movie_selected.review
    return render_template('edit.html', form=edit_form ,movie=movie_selected)

@app.route("/delete")
def delete_movie():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=["GET", "POST"])
def add_movie():

    add_form = MovieAddForm()
    movie_list = []
    if add_form.validate_on_submit():

        params = {
            "api_key" : movie_api_key,
            "query" : add_form.title.data
        }
        response = requests.get(url=MOVIE_DB_URL, params=params).json()

        movie_list = response['results']

        return  render_template('select.html', list=movie_list)
    return render_template('add.html', form=add_form)

@app.route("/select")
def select_movie():
    movie_id = request.args.get('id')

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    params = {
        "api_key": movie_api_key,
    }
    edit_form=MovieEditForm()
    data = requests.get(url=f"{SELECT_URL}/{movie_id}", params=params).json()

    movie_to_add = Movie(
        title = data['title'],
        year = data['release_date'].split('-')[0],
        description = data['overview'],
        rating = 0,
        review = "To be reviewed",
        img_url= f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}"

    )
    db.session.add(movie_to_add)
    db.session.commit()
    print(movie_to_add.id)
    return redirect(url_for('edit',form= edit_form, id=movie_to_add.id))

if __name__ == '__main__':
    app.run(debug=True)
