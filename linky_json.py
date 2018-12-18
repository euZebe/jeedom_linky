#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Generates energy consumption JSON files from Enedis (ERDF) consumption data
collected via their  website (API).
"""

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import datetime
import logging
import sys
import json
import linky
import getpass
from dateutil.relativedelta import relativedelta


# BASEDIR = os.environ['BASE_DIR']

# Generate y axis (consumption values)
def generate_y_axis(res):
  y_values = []

  # Extract data points from the source dictionary into a list
  for ordre, datapoint in enumerate(res['graphe']['data']):
    value = datapoint['valeur']

    # Remove any invalid values
    # (they're error codes on the API side, but useless here)
    if value < 0:
      value = 0

    y_values.insert(ordre, value)

  return y_values

# Generate x axis (time values)


def generate_x_axis(res, time_delta_unit, time_format, inc):
  x_values = []

  # Extract start date and parse it
  start_date_queried_str = res['graphe']['periode']['dateDebut']
  start_date_queried = datetime.datetime.strptime(
      start_date_queried_str, "%d/%m/%Y").date()

  # Calculate final start date using the "offset" attribute returned by the API
  kwargs = {}
  kwargs[time_delta_unit] = res['graphe']['decalage'] * inc
  start_date = start_date_queried - relativedelta(**kwargs)

  # Generate X axis time labels for every data point
  for ordre, _ in enumerate(res['graphe']['data']):
    kwargs = {}
    kwargs[time_delta_unit] = ordre * inc
    x_values.insert(
        ordre, (start_date + relativedelta(**kwargs)).strftime(time_format))

  return x_values

# Date formatting


def dtostr(date):
  return date.strftime("%d/%m/%Y")


# Export the JSON file for half-hours power measure (for the last past day)
def export_hours_values(res, basedir):
  hours_x_values = generate_x_axis(res,
                  'hours', "%Y-%m-%d %H:%M", 0.5)
  hours_y_values = generate_y_axis(res)
  hours_values = []

  for i in range(0, len(hours_x_values)):
    hours_values.append({"time": hours_x_values[i], "conso": hours_y_values[i]})
  endDateName = hours_x_values[len(hours_x_values)].replace(":", "")
  with open(basedir+"/export_hours_values_from_" + hours_x_values[0] + "_to_" + endDateName + ".json", 'w+') as outfile:
    json.dump(hours_values, outfile)

# Export the JSON file for daily consumption (for the past rolling 30 days)


def export_days_values(res, basedir):
  days_x_values = generate_x_axis(res,
                  'days', "%Y-%m-%d", 1)
  days_y_values = generate_y_axis(res)
  days_values = []

  for i in range(0, len(days_x_values)):
    days_values.append({"time": days_x_values[i], "conso": days_y_values[i]})
  with open(basedir+"/export_days_values_from_" + days_x_values[0] + ".json", 'w+') as outfile:
    json.dump(days_values, outfile)

# Export the JSON file for monthly consumption (for the current year, starting 12 months from currentDate)


def export_months_values(res, basedir):
  months_x_values = generate_x_axis(res,
                  'months', "%Y-%m", 1)
  months_y_values = generate_y_axis(res)
  months_values = []

  for i in range(0, len(months_x_values)):
    months_values.append(
        {"time": months_x_values[i], "conso": months_y_values[i]})
  with open(basedir+"/export_months_values_" + months_x_values[0] + ".json", 'w+') as outfile:
    json.dump(months_values, outfile)

# Export the JSON file for yearly consumption


def export_years_values(res, basedir):
  years_x_values = generate_x_axis(res,
                  'years', "%Y", 1)
  years_y_values = generate_y_axis(res)
  years_values = []

  for i in range(0, len(years_x_values)):
    years_values.append(
        {"time": years_x_values[i], "conso": years_y_values[i]})
  with open(basedir+"/export_years_values_" + years_x_values[0] + ".json", 'w+') as outfile:
    json.dump(years_values, outfile)


# Main script
def main():
  logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
  basedir = input("Enter export dir : ")
  username = input("Enter username : ")
  password = getpass.getpass("Enter password : ")

  try:
    if username is None or not username:
      username = "ton email"

    if password is None or not username:
      password = "ton mdp"

    if basedir is None or not basedir:
      basedir = "./"

    logging.info("logging in as %s...", username)
    token = linky.login(username, password)
    logging.info("logged in successfully!")

    logging.info("retreiving data...")

    currentDate = datetime.date.today()
    # currentDate = datetime.date(2018, 7, 16)
    month_startDate = datetime.date(2018, 11, 16)
    day_startDate = month_startDate
    hour_startDate = datetime.date(2018, 12, 12)

    # Years
    res_year = linky.get_data_per_year(token)

    # 12 months ago - currentDate
    # res_month = linky.get_data_per_month(token, dtostr(currentDate - relativedelta(months=11)), \
    #                    dtostr(currentDate))
    res_month = linky.get_data_per_month(token, dtostr(month_startDate), dtostr(currentDate))


    # One month ago - yesterday
    # res_day = linky.get_data_per_day(token, dtostr(currentDate - relativedelta(days=1, months=1)), \
    #                  dtostr(currentDate - relativedelta(days=1)))
    logging.info("res_day [startDate, endDate] = [" + dtostr(day_startDate) + ", " + dtostr(currentDate - relativedelta(days=1)) + "]")
    res_day = linky.get_data_per_day(token, dtostr(day_startDate), dtostr(currentDate - relativedelta(days=2)))

    # Yesterday - currentDate
    # res_hour = linky.get_data_per_hour(token, dtostr(currentDate - relativedelta(days=1)), \
    #                    dtostr(currentDate))
    res_hour = linky.get_data_per_hour(token, dtostr(hour_startDate), dtostr(currentDate))

    logging.info("got data!")
############################################
		# Export of the JSON files, with exception handling as Enedis website is not robust and return empty data often
    try:
      export_hours_values(res_hour, basedir)
    except Exception as exc:
    	# logging.info("hours values non exported")
      logging.error(exc)

    try:
      export_days_values(res_day, basedir)
    except Exception:
      logging.info("day values not exported")

    try:
      export_months_values(res_month, basedir)
    except Exception:
      logging.info("month values not exported")

    try:
      export_years_values(res_year, basedir)
    except Exception:
    	logging.info("year values non exported")

############################################

  except linky.LinkyLoginException as exc:
    logging.error(exc)
    sys.exit(1)



if __name__ == "__main__":
  main()
