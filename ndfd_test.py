import unittest
import ndfd
import datetime
import dateutil.parser as dp

class TestNDFD(unittest.TestCase):

  def test_parse_forecast(self):
    # Test NDFD XML parsing.

    with open('test-forecast.xml','r') as xml_file:
      xml_str = xml_file.read()
      actual = ndfd.parse_forecast(xml_str,'probability-of-precipitation')[0]
      print actual
      expected = {
          'start_time': dp.parse('2013-04-06T05:00:00-07:00'), 
          'end_time': dp.parse('2013-04-06T17:00:00-07:00'), 
          'value': 17
          }
      print expected
      self.assertTrue(actual == expected)
