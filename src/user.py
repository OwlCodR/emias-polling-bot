class User:
    oms = str()
    birthday = str()
    id = str()

    def __init__(self, oms, id):
        self.oms = oms
        self.id = id
        self.birthday = None