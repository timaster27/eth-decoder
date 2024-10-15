class Account:
    def __init__(self):
        self.status = 0
        self.abi = None


class QueryData:
    Decode = 's0'
    Abi = 's1'
    Add = 's2'
    Del = 's3'


class Status:
    Start = 0
    Decode = 1
