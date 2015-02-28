"""
Extracts blocks and transactions from standard clients of bitcoin or altcoins. Saves block and
transaction details to MongoDB. Works on Unix and Cygwin.

Written by: Danny Y. Huang (http://sysnet.ucsd.edu/~dhuang)

"""
import pymongo
from jsonrpc import ServiceProxy, JSONRPCException
import multiprocessing
import time
import subprocess
import random


######################################################
# CONFIGURATION START
######################################################

# How many worker processes to use to communicate with the QT-client.
WORKER_COUNT = 15

# Name of the database.
DB_NAME = 'blockchain_test'

# Which RPC port to have the QT-client listen on. This can be a random number if you want.
RPC_PORT = 36184

# The full path of the QT client of the coin. Please change it.
COIN_QT_CLIENT_FULL_PATH = '/please/set/this'

# Whether to rebuild the coin database. If you're running this script for the first time,
# set the following to True. Otherwise, if you've run this script before and you would simply
# like to import the updated blockchain to the database, set the following to False.
DB_REINDEX = True

######################################################
# CONFIGURATION END
######################################################



def main():

  # Start the coin's QT client.

  cmd = [COIN_QT_CLIENT_FULL_PATH, '-server=1', '-rpcuser=user', '-rpcpassword=12345',
         '-rpcport=%s' % RPC_PORT, '-rpcthreads=%s' % WORKER_COUNT, '-txindex=1']
  if DB_REINDEX:
    cmd.append('-reindex')
  qt_client = subprocess.Popen(cmd)

  time.sleep(15)

  # Start the worker processes to extract the blockchain to MongoDB.

  proc_list = []

  for worker_id in xrange(WORKER_COUNT):
    proc = multiprocessing.Process(target=save_block_info,
                                   args=(worker_id, WORKER_COUNT))
    proc.daemon = True
    proc.start()
    proc_list.append(proc)

  [ proc.join() for proc in proc_list ]

  # Clean up.

  qt_client.terminate()

  return



def save_block_info(worker_id, worker_count):

  # Start the worker processes one by one so as not to overwhelm the QT client.
  time.sleep(worker_id * random.randint(10, 20))

  # Connect to database.
  mongo_client = pymongo.MongoClient()
  db = mongo_client[DB_NAME]
  block_collection = db['block']
  txn_collection = db['txn']

  # Connect to the QT-client's RPC interface.
  daemon = ServiceProxy('http://user:12345@localhost:%s' % RPC_PORT)
  current_height = -1

  # Wait till client is ready.
  while True:
    try:
      total_block_count = daemon.getblockcount()
      break
    except:
      time.sleep(10)

  print 'Started worker', worker_id, 'of', worker_count

  while current_height < total_block_count:

    current_height += 1

    if current_height % worker_count != worker_id:
      continue

    # Check if we have already visited this block.
    if block_collection.find({'_id': current_height}).count() > 0:
      continue

    # Ask the wallet for block information.
    try:
      block_dict = daemon.getblock(daemon.getblockhash(current_height))
    except JSONRPCException:
      print 'Cannot get height', current_height
      time.sleep(1)
      continue

    # Get and save txn information.
    for txn_hash in block_dict.get('tx', []):
      # Three attempts.
      txn_dict = None
      for attempt in xrange(3):
        try:
          txn_dict = daemon.getrawtransaction(txn_hash, 1)
        except:
          print 'Unable to get transaction', txn_hash
          time.sleep((attempt + 1) * 5)
        else:
          break
      if txn_dict:
        txn_dict['_id'] = txn_dict['txid']
        txn_collection.save(txn_dict)

    # Save block to db.
    block_dict['_id'] = current_height
    block_collection.save(block_dict)
    print 'Height', current_height, 'of', total_block_count

    if current_height % 1000:
      total_block_count = daemon.getblockcount()


if __name__ == '__main__':
  main()
