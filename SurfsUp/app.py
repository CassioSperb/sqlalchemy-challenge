# Import the dependencies.
import numpy as np
import flask
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
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
def welcome():
    """List off all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )

# Results from precipitation analysis
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Starting from the most recent data point in the database. 
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    # Calculate the date 12 months ago from the most recent date.
    most_recent_date_dt = datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date_dt - relativedelta(years=1)

    # Perform a query to retrieve the data and precipitation scores
    precipitation_data = session.query(Measurement.date, Measurement.prcp)\
                            .filter(Measurement.date >= one_year_ago)\
                            .order_by(Measurement.date)\
                            .all()

    # Convert query results to dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    # Return the JSON representation of the dictionary
    return jsonify(precipitation_dict)

# Stations List
@app.route("/api/v1.0/stations")
def stations():
    # Query all unique station IDs from the dataset
    stations_data = session.query(Station.station).distinct().all()
    
    # Convert the list of tuples into a flat list
    stations_list = [station[0] for station in stations_data]
    
    # Return the JSON list of station IDs
    return jsonify(stations_list)

# Temperature over the last 12 months
@app.route("/api/v1.0/tobs")
def tobs():
    # Using the most active station id from the previous query
    most_active_station = session.query(Measurement.station, func.count(Measurement.station))\
                                .group_by(Measurement.station)\
                                .order_by(func.count(Measurement.station).desc())\
                                .first()[0]
    
    # Calculate the date 12 months ago from the most recent date.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    most_recent_date_dt = datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date_dt - relativedelta(years=1)

    # Query the dates and temperature observations for the previous year from the most active station
    temperature_data = session.query(Measurement.date, Measurement.tobs)\
                    .filter(Measurement.station == most_active_station)\
                    .filter(Measurement.date >= one_year_ago)\
                    .order_by(Measurement.date)\
                    .all()
   
    # Create a list of dictionaries for the temperature observations
    temperature_data_list = [{"date": date, "temperature": tobs} for date, tobs in temperature_data]

    # Return the JSON list of temperature observations
    return jsonify(temperature_data_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    # If no end date is provided, only use the start date
    if end:
        # Query TMIN, TAVG, TMAX for the given start and end range
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start)\
            .filter(Measurement.date <= end)\
            .all()
    else:
        # Query TMIN, TAVG, TMAX for dates greater than or equal to the start date
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start)\
            .all()

    # Convert the result into a dictionary
    temperature_data = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    # Return the JSON representation of the result
    return jsonify(temperature_data)

if __name__ == "__main__":
    app.run(debug=True)
