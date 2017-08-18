import logging
import requests
import re
import copy
from lxml import html
from darksky import forecast

# Todo: standardise some naming convention -.-
gHeaders = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Upgrade-Insecure-Requests': '1',
}

def gethttp(session, url):
    global gHeaders
    return session.get(url, headers=gHeaders)

def posthttp(session, url, data):
    global gHeaders
    return session.post(url, data, headers=gHeaders)

def retrieveDataFromWebsite(url, xpath, loginurl=None, logindata=None, csrf_data=None, session=None):

        session = session or requests.session()
    
        # If we need to get the csrf token before logging in, as it is often
        # random and required
        if csrf_data != None:
            csrf_page = gethttp(session, csrf_data["csrf_url"])
            tree = html.fromstring(csrf_page.content)
            csrf_token = csrf_data["csrf_extractor_fn"](tree.xpath(csrf_data["csrf_xpath"]))
            logindata = copy.deepcopy(logindata)
            logindata[csrf_data["csrf_token_property_name"]] = csrf_token

        # If we need to login, do socsrf_data[
        if loginurl != None:
            logging.info("Logging in at " + loginurl)
            loginpage = posthttp(session, loginurl, logindata)

            if loginpage.status_code != 200:
                raise Exception("Could not log. The error code is " + str(loginpage.status_code))
            
        # Go to target page
        logging.info("Retrieving data at " + url)
        targetpage = gethttp(session, url)
        
        if targetpage.status_code != 200:
            raise Exception("Could not get data. The error code is " + str(targetpage.status_code))

        # Extract data
        tree = html.fromstring(targetpage.content)
        data = tree.xpath(xpath)

        return data

class DataSource(object):
    def __init__(self, data=None):
        self.data = data

    def retrieve(self, authdata):
        pass

class YWSSource(DataSource):
    def __init__(self, data=None):
        return super().__init__(data)

    def retrieve(self, authdata):
        # Send password/username to login page
        loginurl = "https://www.youngwriterssociety.com/ucp.php?mode=login"
        notificationurl = "https://www.youngwriterssociety.com/ucp.php?i=main&mode=notifications"
        
        session = requests.Session()

        notificationRegion = retrieveDataFromWebsite(notificationurl, '//*[@id="cp-main"]/div/div', loginurl, authdata, session=session)

        if len(notificationRegion) == 0:
            raise Exception("Could not find notifications by xpath")

        notificationSubregions = notificationRegion[0].xpath('//div[@class="notifications"]')

        notifications = []
        for region in notificationSubregions:
            notificationObjects = region.getchildren()[0].getchildren()
            if len(notificationObjects) == 0:
                logging.warn("Unexpected notification HTML formatting: notification region exists, but is empty.")

            for obj in notificationObjects:
                notifications.append(re.sub(r'\W+', ' ', " ".join(obj.itertext())))
            
        notifications = list(reversed(notifications))

        return { "notifications": notifications }

class InterpalsSource(DataSource):
    def __init__(self, data=None):
        return super().__init__(data)

    def retrieve(self, authdata):
        # Send password/username to login page
        loginurl = "https://www.interpals.net/app/auth/login"
        notificationurl = "https://www.interpals.net/app/account"
        
        csrfdata = {
            "csrf_url": 'https://www.interpals.net/',
            "csrf_xpath": '/html/head/meta[8]',
            "csrf_extractor_fn": lambda x: x[0].items()[1][1],
            "csrf_token_property_name": "csrf_token",
        }

        notifs = retrieveDataFromWebsite(notificationurl, '//*[@id="div0"]/ul', loginurl, authdata, csrfdata)


        notifs = notifs[0].getchildren()
        notiftexts = [re.sub(r'\W+', ' ', " ".join(notif.itertext())) for notif in notifs]
        notiftexts = list(reversed(notiftexts))

        return { "notifications": notiftexts }


class WeatherSource(DataSource):
    def __init__(self, data=None):
        return super().__init__(data)

    def retrieve(self, authdata):

        with forecast(authdata["secret"], self.data["location"]["latitude"], self.data["location"]["longtitude"], units=self.data["units"]) as weather:
            res = {
                # 'Light rain throughout the week, with temperatures rising to
                # 20°C on Wednesday.'
                "daily_summary": weather.daily.summary,
                # 'Rain later tonight and tomorrow morning and breezy starting
                # tomorrow afternoon, continuing until tomorrow evening.'
                "hourly_summary": weather.hourly.summary,
                # 'Partly Cloudy'
                "currently_summary": weather.currently.summary,
                # 92.2
                "humidity": weather.currently.humidity * 100,
                # 13.03 (celsius)
                "apparent_temperature": weather.currently.apparentTemperature,
                # 13.2 (celsius)
                "temperature": weather.currently.temperature,
                # 0.2
                "uv_index": weather.currently.uvIndex,
                # 16.09 (km)
                "visibility": weather.currently.visibility,
                # 5.54 (m/s)
                "wind_speed": weather.currently.windSpeed,
                
            }
        
        return res