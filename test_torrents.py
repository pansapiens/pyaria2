from pyaria2 import PyAria2 as aria
import argparse

try:
  input=raw_input
except:
  pass

"""
A simple testbed for pyaria2 functionalities.
A connection to an aria2c instance is done (spawned if needed!),
checked it has no files, add a torrent, check it's added correctly,
and then shut down the aria2c instance.
"""

parser = argparse.ArgumentParser()
parser.add_argument("--host", dest="host", default="localhost")
parser.add_argument("--port", dest="port", default=6800)
parser.add_argument("--secret", dest="secret", default="ABCDEF")
parser.add_argument("--shutdown", dest="shutdown", default=True, type=bool)
parser.add_argument("newtorrent")

args = parser.parse_args()
server = aria( args.host, args.port,
               rpcSecret={"useSecret":True, "secret":args.secret})

print("files actually downloaded by aria2c: ", server.tellActive())
input("press enter to continue...")
server.addTorrent(args.newtorrent, options=dict(dir="."))
print("you should have more!", server.tellActive())
input("press enter to continue...")
if args.shutdown:
  server.shutdown()
  print("server shut down correctly")

print("the test was executed correctly. gg.")
