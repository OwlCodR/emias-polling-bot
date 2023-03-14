import json

class StringsManager:
    strings = {}

    def getString(self, id):
        return self.strings[id]
    
    def __init__(self, filename):
        with open(filename) as f:
            self.strings = json.load(f)