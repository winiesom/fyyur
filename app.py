#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
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

# import Models
from models import db, Artist, Venue, Show


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    artists = db.session.query(Artist).order_by(
        Artist.time_created.desc()).limit(10)
    venues = db.session.query(Venue).order_by(
        Venue.time_created.desc()).limit(10)
    return render_template('pages/home.html', artists=artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
    data = []
    # get venues
    venues = Venue.query.order_by(Venue.city, Venue.state).all()
    # loop each venue
    for venue in venues:
        venue_data = []

        # filter venues by city state
        results = Venue.query.filter_by(
            city=venue.city, state=venue.state).all()

        # loop each filtered result
        for res in results:

            venue_data.append({
                'id': res.id,
                'name': res.name,
                'num_upcoming_shows': len(list(filter(lambda x: x.start_time > datetime.now(), res.shows)))
            })

        data.append({
            'city': venue.city,
            'state': venue.state,
            'venues': venue_data
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    try:
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=",".join(form.genres.data),
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] +
              ' was successfully listed!')

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')

    finally:
        db.session.close()

        return redirect(url_for("index"))


@app.route('/venues/<venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue.genres = venue.genres.split(",")

    past_shows = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()

    past_shows_data = []
    for show in past_shows:
        tmp = {}
        tmp["artist_name"] = show.artists.name
        tmp["artist_id"] = show.artists.id
        tmp["artist_image_link"] = show.artists.image_link
        tmp["start_time"] = str(show.start_time)
        past_shows_data.append(tmp)

    venue.past_shows = past_shows_data
    venue.past_shows_count = len(past_shows_data)

    upcoming_shows = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show. start_time > datetime.now()).all()

    upcoming_shows_data = []
    for show in upcoming_shows:
        tmp = {}
        tmp["artist_name"] = show.artists.name
        tmp["artist_id"] = show.artists.id
        tmp["artist_image_link"] = show.artists.image_link
        tmp["start_time"] = str(show.start_time)
        upcoming_shows_data.append(tmp)

    venue.upcoming_shows = upcoming_shows_data
    venue.upcoming_shows_count = len(upcoming_shows_data)

    return render_template('pages/show_venue.html', venue=venue)


@app.route('/venues/<venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.genres.data = venue.genres.split(",")

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)

    try:
        venue = Venue.query.get(venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = ",".join(form.genres.data)
        venue.image_link = form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] +
              ' edited successfully!')

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('Venue ' + request.form['name'] +
              ' was not edited successfully.')
    finally:
        db.session.close()

        return redirect(url_for('show_venue', venue_id=venue_id))


@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash("Venue " + venue.name + " was deleted successfully!")
    except ():
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue " + venue.name + " was not deleted successfully.")
    finally:
        db.session.close()

    return redirect(url_for("index"))


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get("search_term")

    venues_search = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_term)) |
        Venue.state.ilike('%{}%'.format(search_term)) |
        Venue.city.ilike('%{}%'.format(search_term))
    ).all()

    response = {}
    search_data = []

    response["count"] = len(venues_search)
    response["data"] = []

    for venue in venues_search:
        tmp = {}
        tmp['id'] = venue.id
        tmp['name'] = venue.name
        tmp['num_upcoming_shows'] = len(
            list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
        search_data.append(tmp)
    response['data'] = search_data
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    try:
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=",".join(form.genres.data),
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data,
        )
        db.session.add(artist)
        db.session.commit()
        flash("Artist " + '"' + request.form['name'] + '"' +
              " was successfully listed!")
    except:
        db.session.rollback()
        flash("Artist " + '"' + request.form['name'] + '"' +
              " was not successfully listed.")
    finally:
        db.session.close()

        return redirect(url_for("index"))


@app.route('/artists/<artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    artist.genres = artist.genres.split(",")

    # get all past shows

    past_shows = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

    past_shows_data = []
    for show in past_shows:
        tmp = {}
        tmp["venue_name"] = show.venues.name
        tmp["venue_id"] = show.venues.id
        tmp["venue_image_link"] = show.venues.image_link
        tmp["start_time"] = str(show.start_time)
        past_shows_data.append(tmp)

    artist.past_shows = past_shows_data
    artist.past_shows_count = len(past_shows_data)

#   Get upcoming shows
    upcoming_shows = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id).filter(Show. start_time > datetime.now()).all()

    upcoming_shows_data = []
    for show in upcoming_shows:
        tmp = {}
        tmp["venue_name"] = show.venues.name
        tmp["venue_id"] = show.venues.id
        tmp["venue_image_link"] = show.venues.image_link
        tmp["start_time"] = str(show.start_time)
        upcoming_shows_data.append(tmp)

    artist.upcoming_shows = upcoming_shows_data
    artist.upcoming_shows_count = len(upcoming_shows_data)

    return render_template('pages/show_artist.html', artist=artist)


@ app.route('/artists/<artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    form.genres.data = artist.genres.split(",")

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    try:
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = ",".join(form.genres.data)
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website_link = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.add(artist)
        db.session.commit()
        flash("Artist " + '"' +
              request.form['name'] + '"' + " was successfully edited!")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Artist " + '"' +
              request.form['name'] + '"' + " was not successfully edited.")
    finally:
        db.session.close()
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term')
    artists_search = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_term)) |
        Artist.state.ilike('%{}%'.format(search_term)) |
        Artist.city.ilike('%{}%'.format(search_term))
    ).all()

    response = {}
    response['count'] = len(artists_search)
    response['data'] = artists_search

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.all()

    data = []
    for show in shows:
        data.append({
            'venue_id': show.venues.id,
            'venue_name': show.venues.name,
            'artist_id': show.artists.id,
            'artist_name': show.artists.name,
            'artist_image_link': show.artists.image_link,
            'start_time': str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)

    try:
        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('Show was not successfully listed.')
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
