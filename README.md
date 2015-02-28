Extracts blocks and transactions from standard clients of bitcoin or altcoins. Saves block and
transaction details to MongoDB. Works on Unix and Cygwin.

Written by: Danny Y. Huang (http://sysnet.ucsd.edu/~dhuang)

Prerequisites: 

- pymongo (http://api.mongodb.org/python/current/installation.html)
- MongoDB (http://www.mongodb.org)
- Bitcoin-QT or the standard QT-client of any altcoins.

Usage:

0. Install the prerequisites. Start MongoDB.
1. Fill in the configuration section in parser.py.
2. Run the script: python parser.py.
3. The script will exit automatically when the import of blockchain into MongoDB is complete.
