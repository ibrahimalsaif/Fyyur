#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime, date

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:7654321@localhost:5432/fyyur'
db = SQLAlchemy(app)
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(200))
    genres = db.Column(db.ARRAY(db.String(120)))
    shows = db.relationship("Shows",  backref='venue')

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(200))
    genres = db.Column(db.ARRAY(db.String(120)))
    shows = db.relationship("Shows",  backref='artist')

class Shows(db.Model):
    __tablename__ = 'Shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#----------------------------------------------------------------------------#
#  Venues
#----------------------------------------------------------------------------#

@app.route('/venues')
def venues():
  venues =  Venue.query.order_by(Venue.city,Venue.state).all()
  return render_template('pages/venues.html', areas=venues)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  response = Venue.query.filter(Venue.name.ilike('%'+ search_term +'%')).all()
  search_term_count = len(response)
  return render_template('pages/search_venues.html', results=response, search_term=search_term, search_count=search_term_count)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  past_shows_list = db.session.query(Shows).join(Artist).filter(Shows.venue_id==venue_id).filter(Shows.start_time<datetime.now()).all()
  past_shows = []

  upcoming_shows_list = db.session.query(Shows).join(Artist).filter(Shows.venue_id==venue_id).filter(Shows.start_time>datetime.now()).all()
  upcoming_shows = []

  for show in past_shows_list:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  past_shows_count = len(past_shows)

  for show in upcoming_shows_list:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
    })

  upcoming_shows_count = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=venue, past_shows=past_shows, upcoming_shows=upcoming_shows,
   past_shows_count=past_shows_count, upcoming_shows_count=upcoming_shows_count)

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_description =request.form['seeking_description']
    venue = Venue(name=name,city=city,state=state,address=address,phone=phone,genres=genres,facebook_link=facebook_link,
    image_link=image_link,website_link=website_link,seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    delete_venue = Venue.query.get(venue_id)
    db.session.delete(delete_venue)
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()

  return redirect(url_for('venues'))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website_link = request.form['website_link']
    venue.seeking_description =request.form['seeking_description']
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully Modified!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be Modified.')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#----------------------------------------------------------------------------#
#  Artists
#----------------------------------------------------------------------------#

@app.route('/artists')
def artists():
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  response = Artist.query.filter(Artist.name.ilike('%'+ search_term +'%')).all()
  search_term_count = len(response)
  return render_template('pages/search_artists.html', results=response, search_term=search_term, search_term_count=search_term_count)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)
  
  past_shows_list = db.session.query(Shows).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time<datetime.now()).all()
  past_shows = []

  upcoming_shows_list = db.session.query(Shows).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time>datetime.now()).all()
  upcoming_shows = []

  for show in past_shows_list:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  past_shows_count = len(past_shows)

  for show in upcoming_shows_list:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
    })

  upcoming_shows_count = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=artist, past_shows=past_shows, upcoming_shows=upcoming_shows,
   past_shows_count=past_shows_count, upcoming_shows_count=upcoming_shows_count)

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website_link = request.form['website_link']
    artist.seeking_description =request.form['seeking_description']
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully Modified!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be Modified.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_description =request.form['seeking_description']
    artist = Artist(name=name,city=city,state=state,phone=phone,genres=genres,facebook_link=facebook_link,
    image_link=image_link,website_link=website_link,seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#

@app.route('/shows')
def shows():

  shows_list = db.session.query(Shows).join(Venue).join(Artist).filter(Shows.artist_id==Artist.id).filter(Shows.venue_id==Venue.id).all()
  shows = []

  for show in shows_list:
    shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    venue_id = request.form['venue_id']
    artist_id = request.form['artist_id']
    start_time = request.form['start_time']
    show = Shows(venue_id=venue_id,artist_id=artist_id,start_time=start_time)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

if __name__ == '__main__':
    app.run()
