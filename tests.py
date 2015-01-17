#import unittest
from pyaria2 import PyAria2 as aria

# ARIA_HOST = 'localhost'
# ARIA_PORT = 6800

# class TestAriaRunning(unittest.TestCase):
#     def setUp(self):
server = aria(rpcSecret={"useSecret":True, "fixedSecret":'ABCDEF'})

#     def test_tellActive(self):

print server.tellActive()

