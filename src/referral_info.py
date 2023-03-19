class ReferralInfo:
    name = str()
    endDate = str()
    hospitalName = str()
    referralId = str()

    def __init__(self, name, endDate, hospitalName, referralId):
        self.name = name
        self.endDate = endDate
        self.hospitalName = hospitalName
        self.referralId = referralId
