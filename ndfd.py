import requests
import lxml.etree as etree

import datetime
import dateutil.parser as dp
import pytz

import logging


class NDFD:
  '''
  A lightweight client for the NDFD REST web service.
  
  Currently supports the following forecast elements: 
    - probability-of-precipitation (POP12)

  NDFD REST: http://graphical.weather.gov/xml/rest.php
  '''

  ELEMENT_ABBR = {
      'probability-of-precipitation': 'pop12'
      }

  FORECAST_URL = ("http://www.weather.gov/forecasts/xml"
    "/sample_products/browser_interface"
    "/ndfdXMLclient.php")


  def __init__(self, forecast_element, lat=37.76, lon=-122.412):

    self.forecast_element = forecast_element
    self.lat = lat
    self.lon = lon

    if self.forecast_element in self.ELEMENT_ABBR.keys():
      self.refresh()
    else:
      raise ValueError('Unsupported forecast element: ' + forecast_element)

  def refresh(self):
    '''Acquire updated data from the NDFD.
    '''
    ndfd_xml = self._download_forecast()
    self.forecasts = self._parse_forecast(ndfd_xml)

  def _download_forecast(self):
    '''
    Returns the response object containing a forecast for the given lat/lon 
    coords as XML.
    '''

    start_date = datetime.datetime.today()
    num_days = 2
    metric = True
    location_info = [("lat", self.lat), ("lon", self.lon)]
    params = location_info + [("begin", start_date.strftime("%Y-%m-%dT%H:%M")),
                              ("end", (start_date + datetime.timedelta(num_days)).strftime("%Y-%m-%dT%H:%M")),
                              ("product", "time-series"),
                              ("Unit", "m" if metric else "e"),
                              (self.ELEMENT_ABBR[self.forecast_element], self.ELEMENT_ABBR[self.forecast_element])
                              ]

    req = requests.get(self.FORECAST_URL, params = params)
    logging.info(req.url)

    return req.content


  def _parse_forecast(self, ndfd_xml_str):
    '''
    Returns a list of forecast dictionaries parsed from the given NDFD XML 
    string.
    '''

    root = etree.fromstring(ndfd_xml_str)
    elm = root.find('./data/parameters/{0}'.format(self.forecast_element))

    # get start and end time series
    time_key = elm.attrib['time-layout']
    times = root.xpath('./data/time-layout/layout-key[text() = "{0}"]'.format(time_key))[0].getparent()
    start_times = times.xpath('./start-valid-time/text()')
    end_times = times.xpath('./end-valid-time/text()')

    # get forecast values 
    forecast_values = elm.xpath('./value/text()')

    # combine times and forecast values into a dictionary of forecasts
    forecasts = []
    for idx, val in enumerate(forecast_values):
      forecasts.append({
        'start_time': dp.parse(start_times[idx]), 
        'end_time': dp.parse(end_times[idx]),
        'value': int(val)
        })

    return forecasts


  def _weighted_mean(self, time):
    '''
    Returns the weighted mean of two consecutive forecasts when both overlap 
    the 12 hours following the given time.
    '''
    
    for idx in range(len(self.forecasts)):
      if self.forecasts[idx]['start_time'] <= time < self.forecasts[idx]['end_time']:

        time_in_current_window = (self.forecasts[idx]['end_time'] - time).total_seconds()
        time_in_next_window = 12*60*60 - time_in_current_window

        p_in_current_window = (time_in_current_window/(12*60*60)) * self.forecasts[idx]['value']
        p_in_next_window = (time_in_next_window/(12*60*60)) * self.forecasts[idx+1]['value']

        logging.debug('First period forecast: ' + str(self.forecasts[idx]['value']))
        logging.debug('Second period forecast: ' + str(self.forecasts[idx+1]['value']))
        
        return p_in_current_window + p_in_next_window


  def forecast_at_time(self, time):
    '''
    Returns the 12-hour forecast beginning from the given time.
    
    If the given time does not fall exactly at the beginning of a forecast
    period, the returned forecast will be interpolated using the period
    containing the given time and the following period.
    '''

    p_next_12h = None
    if self.forecast_element == 'probability-of-precipitation':
      p_next_12h = self._weighted_mean(time)/100
    return p_next_12h


def main():
  '''Get the probability of precipitation over the next 12 hours.
  '''

  ndfd = NDFD('probability-of-precipitation')
  print ndfd.forecast_at_time(datetime.datetime.now(pytz.utc))


if __name__ == '__main__':
  main()
  
