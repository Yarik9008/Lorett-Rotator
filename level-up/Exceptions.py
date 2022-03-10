class UnknownStationType(Exception):
    def __init__(self, statiomnType) -> None:
        self.message = f"The {statiomnType} type is not supported"

class CoordinatesAreNotGiven(Exception):
    def __init__(self, lon=1, lat=1, alt=1) -> None:
        self.message = ""

        if not lon:
            self.message += "Lon can't be None\n"
        if not lat:
            self.message += "Lat can't be None\n"
        if not alt:
            self.message += "Alt can't be None"
    
    def __str__(self) -> str:
        print("Station coordinates are not given.")
        return "\n" + self.message


class InvalidTimeCorrection(Exception):
    def __init__(self) -> None:
        pass
    
    def __str__(self) -> str:
        return "Correction of the time zone for more than 12 hours.\nThere is no such time zone."


class InvalidCoordinates(Exception):
    def __init__(self, *args) -> None:
        pass
    
    def __str__(self) -> str:
        return "The coordinates of the station are not specified correctly."
