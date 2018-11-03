import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request


class Blockchain(object):

    def __init__(self):
        self.blockchain = []
        self.transactions = []
        self.nodes = set()  # using set means nodes are unique

        # Genesis block on initialization
        self.block(prev_hash=1, proof=100)

    def block(self, proof, prev_hash=None):
        # add new blocks to blockchain
        block = {
            'index': len(self.blockchain) + 1,
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

    def add_node(self, address):
        # Add new node - address is ufl of node
        url_parsed = urlparse(address)
        self.nodes.add(url_parsed.netloc)

    def validate_blockchain(self, blockchain):
        last_block = blockchain[0]
        cur_index = 1

        # iterate through chain
        while cur_index < len(blockchain):
            block = blockchain[cur_index]

            # check block hash
            if block['prev_hash'] != self.hash(last_block):
                return False

            # check against PoW
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            cur_index += 1

        return True

    def consensus(self):
        # always replace chain w/ longest chain available

        nearby_nodes = self.nodes
        new_blockchain = None

        max_len = len(self.blockchain)

        # check chains on nodes on the netowrk
        for node in nearby_nodes:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                node_chain = response.json()['blockchain']

                # check length longer & chain validity
                if length > max_len and self.validate_blockchain(node_chain):
                    max_len = length
                    new_blockchain = node_chain

        if new_blockchain:
            self.blockchain = new_blockchain
            return True

        return False

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

    # 1. calc PoW
    proof = blockchain.PoW(last_block)

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
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():

    # 1. Check validity of sender address
    # 2. Check validity of recipient address
    # 3. Ensure sender has enough to send

    values = request.get_json()

    required = ['sender', 'to', 'amt']

    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.transaction(
        values['sender'],
        values['to'],
        values['amt'])

    response = {'message': f'Adding tx to Block at index {index}'}

    return jsonify(response), 201


@app.route('/blockchain', methods=['GET'])
def return_blockchain():
    response = {
        'blockchain': blockchain.blockchain,
        'length': len(blockchain.blockchain)
    }
    return jsonify(response), 200


@app.route('/nodes/add', methods=['POST'])
def add_node():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Err: not a valid node list", 400

    for node in nodes:
        blockchain.add_node(node)

        response = {
            'message': 'Added new nodes',
            'total_nodes': list(blockchain.nodes)
        }

    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    repl = blockchain.consensus()

    if repl:
        response = {
            'message': 'This chain has been replaced',
            'new_chain': blockchain.blockchain
        }
    else:
        response = {
            'message': 'This chain is the most valid',
            'new_chain': blockchain.blockchain
        }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
