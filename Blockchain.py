class Blockchain(object):

    def __init__(self):
        self.blockchain = [];
        self.transactions = [];

    '''
    A single block looks like
    block = {
        'index': 1,
        'timestamp': 1506057125.900785,
        'transactions': [
            {
                'sender': "8527147fe1f5426f9dd545de4b27ee00",
                'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
                'amount': 5,
            }
        ],
        'proof': 324984774000,
        'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    }
    '''
    def block(self):
        #add new blocks to blockchain
        pass

    def transaction(self,sender,recipient,amt):
        #add new tx to transactions

        
        self.transactions.append({
            'sender':sender,
            'recipient': recipient,
            'amt': amt
        })
        #return the the next block # to be mined
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        #block hashing
        pass

    @property
    def last_block(selfself):
        #return last block in blockchain
        pass


###
Example