# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False})

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available API routes with usage instructions."""
    return (
        f"<h2>Available Routes:</h2>"
        f"<ul>"
        f"<li><a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a> - Last 12 months of precipitation data</li>"
        f"<li><a href='/api/v1.0/stations'>/api/v1.0/stations</a> - List of all stations</li>"
        f"<li><a href='/api/v1.0/tobs'>/api/v1.0/tobs</a> - Temperature observations for the most active station</li>"
        f"</ul>"
        f"<h2>Dynamic Routes:</h2>"
        f"<p>For the following routes, replace &lt;start&gt; and &lt;end&gt; with dates in YYYY-MM-DD format:</p>"
        f"<ul>"
        f"<li>/api/v1.0/&lt;start&gt; - Min, Avg, and Max temperature from &lt;start&gt; date (e.g., <a href='/api/v1.0/2017-01-01'>/api/v1.0/2017-01-01</a>)</li>"
        f"<li>/api/v1.0/&lt;start&gt;/&lt;end&gt; - Min, Avg, and Max temperature between &lt;start&gt; and &lt;end&gt; (e.g., <a href='/api/v1.0/2017-01-01/2017-08-23'>/api/v1.0/2017-01-01/2017-08-23</a>)</li>"
        f"</ul>"
        f"<p><b>Note:</b> Dates must be in <code>YYYY-MM-DD</code> format.</p>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return JSON representation of the last 12 months of precipitation data"""
    

    # Get the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_datetime = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    
    # Calculate the date one year before the most recent date
    one_year_ago = most_recent_datetime - dt.timedelta(days=365)

    # Query for last 12 months of precipitation data
    precipitation_data = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_year_ago.date())
        .all()
    )

    # Convert query results to a dictionary (date as key, prcp as value)
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    # Return JSON response
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of all stations in the dataset"""

    # Query all stations
    stations_data = session.query(Station.station).all()

    # Convert the list of tuples into a normal list
    stations_list = [station[0] for station in stations_data]

    # Return JSON response
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations (tobs) for the most active station for the last year"""

    # Find the most active station ID
    most_active_station_id = session.query(Measurement.station)\
        .group_by(Measurement.station)\
        .order_by(func.count(Measurement.station).desc())\
        .first()[0]

    # Get the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_datetime = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")

    # Calculate the date one year before the most recent date
    one_year_ago = most_recent_datetime - dt.timedelta(days=365)

    # Query the last 12 months of temperature observations for the most active station
    tobs_data = session.query(Measurement.tobs)\
        .filter(Measurement.station == most_active_station_id)\
        .filter(Measurement.date >= one_year_ago.date())\
        .all()

    # Convert temperature observations to a list
    tobs_list = [tobs[0] for tobs in tobs_data]

    # Return the JSON response
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
def temp_start(start):
    """Return TMIN, TAVG, and TMAX for all dates greater than or equal to the start date"""

    # Query the min, avg, and max temperatures for dates >= start date
    temp_stats = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start).all()

    # Convert the result into a dictionary
    temp_dict = {
        "TMIN": temp_stats[0][0],
        "TAVG": temp_stats[0][1],
        "TMAX": temp_stats[0][2]
    }

    # Return the JSON response
    return jsonify(temp_dict)


@app.route("/api/v1.0/<start>/<end>")
def temp_start_end(start, end):
    """Return TMIN, TAVG, and TMAX for all dates between start and end date (inclusive)"""

    # Query the min, avg, and max temperatures for dates between start and end
    temp_stats = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    # Convert the result into a dictionary
    temp_dict = {
        "TMIN": temp_stats[0][0],
        "TAVG": temp_stats[0][1],
        "TMAX": temp_stats[0][2]
    }

    # Return the JSON response
    return jsonify(temp_dict)

# Close the session
session.close()

if __name__ == "__main__":
    app.run(debug=True)