import json

class Authenticator(object):
    def __init__(self, credentialsPath):
        with open(credentialsPath) as file:
            self.data = json.load(file)

    def fetchCredentialsForSource(self, source):
        name = type(source).__name__
        if name not in self.data:
            return {}
        return self.data[name]