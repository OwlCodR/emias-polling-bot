class SlotInfo:
    date = str()
    availableResourceId = str()
    complexResourceId = str()
    startTime = str()
    endTime = str()

    def __init__(self, date, availableResourceId, complexResourceId, startTime, endTime):
        self.date = date
        self.availableResourceId = availableResourceId
        self.complexResourceId = complexResourceId
        self.startTime = startTime
        self.endTime = endTime
