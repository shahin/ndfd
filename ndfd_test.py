from ndfd import NDFD
import datetime
import dateutil.parser as dp

import unittest
import logging
from mock import MagicMock


class TestNDFD(unittest.TestCase):


  def test_parse_forecast(self):
    # Test NDFD XML parsing.

    with open('test-forecast.xml','r') as xml_file:

      # set up test data
      xml_str = xml_file.read()
      ndfd_mock = MagicMock(forecast_element='probability-of-precipitation')
      ndfd_mock._parse_forecast = NDFD.__dict__['_parse_forecast']

      # run test operation
      actual = ndfd_mock._parse_forecast(ndfd_mock,xml_str)[0]

      expected = {
          'start_time': dp.parse('2013-04-06T05:00:00-07:00'), 
          'end_time': dp.parse('2013-04-06T17:00:00-07:00'), 
          'value': 17
          }
      self.assertEquals(actual, expected)


  def test_weighted_mean(self):
    # Test weighted-mean interpolation over two forecast periods. 

      # set up test data
      ndfd_mock = MagicMock(forecasts=[
        {
          'start_time': dp.parse('2013-04-06T05:00:00-07:00'), 
          'end_time': dp.parse('2013-04-06T17:00:00-07:00'), 
          'value': 10
        },
        {
          'start_time': dp.parse('2013-04-06T17:00:00-07:00'), 
          'end_time': dp.parse('2013-04-07T05:00:00-07:00'), 
          'value': 20
        }
        ])
      ndfd_mock._weighted_mean = NDFD.__dict__['_weighted_mean']

      # test for a weighted mean over two forecast periods
      actual = ndfd_mock._weighted_mean(ndfd_mock, dp.parse('2013-04-06T11:00:00-07:00'))

      expected = 15
      self.assertEqual(actual, expected)

      # test for a weighted mean over one forecast period
      actual = ndfd_mock._weighted_mean(ndfd_mock, dp.parse('2013-04-06T05:00:00-07:00'))

      expected = 10
      self.assertEqual(actual, expected)

      # test for a weighted mean without enough remaining data 
      self.assertRaises(
        IndexError,
        ndfd_mock._weighted_mean,
        ndfd_mock, dp.parse('2013-04-06T17:00:01-07:00')
        )
