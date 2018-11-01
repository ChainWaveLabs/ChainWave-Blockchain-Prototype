import hashlib
import json
from time import time
from uuid import uuid4

from textwrap import dedent
from flask import Flask, jsonify, request


class Blockchain(object):

    def __init__(self):
        self.blockchain = []
        self.transactions = []

        # Genesis block on initialization
        self.block(prev_hash=1, proof=100)

    '''
    A single block looks like
    block = {
        'i': 1,
        'timestamp': 1506057125.900785,
        'transactions': [
            {
                'sender': "8527147fe1f5426f9dd545de4b27ee00",
                'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
                'amount': 5,
            }
        ],
        'proof': 324984774000,
        'prev_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    }
    '''

    def block(self, proof, prev_hash=None):
        # add new blocks to blockchain
        block = {
            'i': len(self.blockchain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'proof': proof,
            'prev_hash': prev_hash or self.hash(self.blockchain[-1]),
        }

        # reset tx list
        self.transactions = []
        self.blockchain.append(block)
        return block

    def transaction(self, sender, to, amt):
        # add new tx to transactions
        self.transactions.append({
            'sender': sender,
            'to': to,
            'amt': amt
        })
        # return the the next block # to be mined
        return self.last_block['index'] + 1

    def PoW(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
      # adjust difficulty by adding # of leading zeros
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def hash(block):
        blk_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha3_256(blk_string).hexdigest()

    @property
    def last_block(self):
        # return last block in blockchain
        return self.blockchain[-1]


# FLASK / SERVER
app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # 1. Calculate PoW
    # 2. Reward miners by adding tx and returning coin
    # 3. Forge new block - add it to the chain

    last_block = blockchain.last_block
    last_proof = last_block['proof']

    # 1. calc PoW
    proof = blockchain.PoW(last_proof)

    # 2. set up tx
    blockchain.transaction(
        sender="0",
        to=node_identifier,
        amt=1
    )

    # 3. add block
    prev_hash = blockchain.hash(last_block)
    block = blockchain.block(proof, prev_hash)

    response = {
        'message': "Block added",
        'i': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
      Example request:
    {
     "from": "my address",
     "to": "someone else's address",
     "amount": 5
    }
    """
    # 1. Check validity of sender address
    # 2. Check validity of recipient address
    # 3. Ensure sender has enough to send

    values = request.get_json()
    required = ['from', 'to', 'amt']

    if not all(k in values for k in required):
        return "Missing Values", 400

    index = blockchain.transaction(values['from'], values['to'], values['amt'])
    response = {'message': f'Adding tx to Block at index {index}'}
    return jsonify(response), 201


@app.route('/blockchain', methods=['GET'])
def return_blockchain():
    response = {
        'blockchain': blockchain.blockchain,
        'length': len(blockchain.blockchain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
