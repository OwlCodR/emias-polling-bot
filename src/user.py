class User:
    oms = str()
    birthday = str()
    id = str()
    isAutoAppointment = bool()
    hasNotification = bool()
    pollingIntervalMinutes = str()
    specialityId = str()            # ID специальности направления
    referralId = str()              # ID направления
    availableResourceId = str()     # ID доступной записи
    complexResourceId = str()       # ID комнаты
    availabilityDate = str()
    startTime = str()
    endTime = str()

    def __init__(self, oms, id):
        self.oms = oms
        self.id = id
        self.birthday = None
        self.isAutoAppointment = False
        self.hasNotification = False
        self.pollingIntervalMinutes = None
        self.referralId = None
        self.availableResourceId = None
        self.complexResourceId = None
        self.specialityId = None
        self.availabilityDate = None
        self.startTime = None
        self.endTime = None