import requests
import lxml.etree as etree
import datetime
import dateutil.parser as dp
import pytz


def download_forecast():
  # download forecast data

  FORECAST_URL = ("http://www.weather.gov/forecasts/xml"
    "/sample_products/browser_interface"
    "/ndfdXMLclient.php")

  lat = 37.76
  lon = -122.412
  start_date = datetime.datetime.today()
  num_days = 2
  metric = True
  location_info = [("lat", lat), ("lon", lon)]
  params = location_info + [("begin", start_date.strftime("%Y-%m-%dT%H:%M")),
                            ("end", (start_date + datetime.timedelta(num_days)).strftime("%Y-%m-%dT%H:%M")),
                            ("product", "time-series"),
                            ("Unit", "m" if metric else "e"),
                            ("maxt","maxt"),
                            ("mint","mint"),
                            ("pop12","pop12")
                            ]

  return requests.get(FORECAST_URL,params = params)


def parse_forecast(ndfd_xml_str,forecast_element):
  # parse forecast data

  root = etree.fromstring(ndfd_xml_str)
  el = root.find('./data/parameters/{0}'.format(forecast_element))

  # get start and end time series
  time_key = el.attrib['time-layout']
  times = root.xpath('./data/time-layout/layout-key[text() = "{0}"]'.format(time_key))[0].getparent()
  start_times = times.xpath('./start-valid-time/text()')
  end_times = times.xpath('./end-valid-time/text()')

  # get forecast values 
  forecast_values = el.xpath('./value/text()')

  # combine times and forecast values into a dictionary of forecasts
  forecasts = []
  for idx,val in enumerate(forecast_values):
    forecasts.append({
      'start_time': dp.parse(start_times[idx]), 
      'end_time': dp.parse(end_times[idx]),
      'value': int(val)
      })

  return forecasts


def _weighted_mean(forecasts,time):
  
  for idx in range(len(forecasts)):
    if forecasts[idx]['start_time'] < time < forecasts[idx]['end_time']:
      time_in_current_window = (forecasts[idx]['end_time'] - time).total_seconds()
      time_in_next_window = 12*60*60 - time_in_current_window

      p_in_current_window = (time_in_current_window/(12*60*60)) * forecasts[idx]['value']
      p_in_next_window = (time_in_next_window/(12*60*60)) * forecasts[idx+1]['value']
      
      return p_in_current_window + p_in_next_window


def forecast_at_time(forecasts,time,forecast_element):

  p_next_12h = None
  if forecast_element == 'probability-of-precipitation':
    p_next_12h = _weighted_mean(forecasts,time)
  return p_next_12h


if __name__ == '__main__':

  response = download_forecast()
  forecasts = parse_forecast(response.content,'probability-of-precipitation')
  print forecast_at_time(forecasts,datetime.datetime.now(pytz.utc),'probability-of-precipitation')
  
