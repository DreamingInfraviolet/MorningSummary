from authentication import *
from data_sources import *
import pprint

if __name__ == "__main__":
    credentialsFileLocation = "credentials.json"
    authenticator = Authenticator(credentialsFileLocation)
    
    location = {
        "latitude": 53.5259,
        "longtitude": -7.3381,
    }

    weatherData = {
        # { latitude, longtitude }
        "location": location,
        # si is standard imperial units. ca is similar, but with km/h instead of m/s.
        "units": "ca",
    }

    sources = [YWSSource(), WeatherSource(weatherData)]
    
    for source in sources:
        credentials = authenticator.fetchCredentialsForSource(source)
        data = source.retrieve(credentials)
        pprint.pprint(data)

    print("Bye!")