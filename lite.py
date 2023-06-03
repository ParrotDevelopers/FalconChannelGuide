import xmltv
import re
import os
import sys
import gzip
import unicodedata
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import io

TS = " +0000"

days = 5
days_back = 3


def encode(string):
    string = str(unicodedata.normalize('NFKD', string).encode('ascii', 'ignore'), "utf-8")
    return string


class Get_channels_sms:
    def __init__(self):
        self.channels = []
        headers = {"user-agent": "SMSTVP/1.7.3 (242;cs_CZ) ID/ef284441-c1cd-4f9e-8e30-f5d8b1ac170c HW/Redmi Note 7 Android/10 (QKQ1.190910.002)"}
        self.html = requests.get("http://programandroid.365dni.cz/android/v6-tv.php?locale=cs_CZ", headers = headers).text
        self.ch = {}

    def own_channels(self, cchc):
        try:
            root = ET.fromstring(self.html)
            #cchc = cchc.split(",") # Lists are better for this
            for i in root.iter("a"):
                if True:
                    self.ch[i.attrib["id"]] = encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower())
                    try:
                        icon = "http://sms.cz/kategorie/televize/bmp/loga/velka/" + i.find("o").text
                    except:
                        icon = ""
                    self.channels.append({"display-name": [(i.find("n").text, u"cs")], "id": encode((i.attrib["id"] + "-" + i.find("n").text).replace(" ", "-").lower()), "icon": [{"src": icon}]})
        except:
            pass
        return self.ch, self.channels


class Get_programmes_sms:
    def __init__(self, days_back, days):
        self.programmes_sms = []
        self.days_back = days_back
        self.days = days

    def data_programmes(self, ch):
        if ch != {}:
            chl = ",".join(ch.keys())
            now = datetime.now()
            for i in range(self.days_back*-1, self.days):
                next_day = now + timedelta(days = i)
                date = next_day.strftime("%Y-%m-%d")
                date_ = next_day.strftime("%d.%m.%Y")
                headers = {"user-agent": "SMSTVP/1.7.3 (242;cs_CZ) ID/ef284441-c1cd-4f9e-8e30-f5d8b1ac170c HW/Redmi Note 7 Android/10 (QKQ1.190910.002)"}
                print(date_)
                html = requests.get("http://programandroid.365dni.cz/android/v6-program.php?datum=" + date + "&id_tv=" + chl, headers = headers).text
                root = ET.fromstring(html)
                root[:] = sorted(root, key=lambda child: (child.tag,child.get("o")))
                for i in root.iter("p"):
                    n = i.find("n").text
                    try:
                        k = i.find("k").text
                    except:
                        k = ""
                    #if i.attrib["id_tv"] in ch:
                    if True:
                        start = i.attrib["o"].replace("-", "").replace(":", "").replace(" ", "")
                        stop = i.attrib["d"].replace("-", "").replace(":", "").replace(" ", "")
                        start_time = datetime.strptime(start, "%Y%m%d%H%M%S")
                        stop_time = datetime.strptime(stop, "%Y%m%d%H%M%S")
                        #start_time = start_time + timedelta(hours=TS2)
                        #stop_time = stop_time + timedelta(hours=TS2)
                        start = start_time.strftime("%Y%m%d%H%M%S") + TS
                        stop = stop_time.strftime("%Y%m%d%H%M%S") + TS
                        self.programmes_sms.append({"channel": ch[i.attrib["id_tv"]].replace("804-ct-art", "805-ct-:d"), "start": start, "stop": stop, "title": [(n, "")], "desc": [(k, "")]})
                sys.stdout.write('\x1b[1A')
                print(date_ + "  OK")
        print("\n")
        return self.programmes_sms


class Others:
    def __init__(self):
        self.channels = []
        self.programmes = []

        self.patterns = {
            "display-name": re.compile("<display-name>(.*?)</display-name>"),
            "id": re.compile('<channel id="(.*?)">'),
            "icon": re.compile('<icon src="(.*?)"'),
            "url": re.compile('<url>(.*?)</url>'),
            "desc": re.compile('<desc lang="en">(.*?)</desc>'),
            "start": re.compile('start="(.*?)"'),
            "stop": re.compile('stop="(.*?)"')
        }

        self.epgs = [
            "https://epgshare01.online/epgshare01/epg_ripper_US1.xml.gz",
            "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS2.xml.gz",
            "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"
        ]

    def ungzip(self, url):
        response = requests.get(url)
        compressed_file = io.BytesIO(response.content)
        decompressed_file = gzip.GzipFile(fileobj=compressed_file)
        return decompressed_file.read()

    def data_own_programmes(self, allowed):
        for website in self.epgs:
            root = ET.fromstring(self.ungzip(website))
            for channel in root.findall('channel'):
                id = channel.get('id')
                #if id not in allowed:
                #    continue
                name = channel.find('display-name').text
                try:
                    icon = channel.find('icon').get('src')
                except:
                    icon = ""
                self.channels.append({"display-name": [(name, "")], "id": id, "icon": [{"src": icon}]})

            for programme in root.findall('programme'):
                id = programme.get('channel')
                #if id not in allowed:
                #    continue
                name = programme.find('title').text
                try:
                    desc = programme.find('desc').text
                except:
                    desc = ""
                start = programme.get('start').split(" ")[0]
                stop = programme.get('stop').split(" ")[0]
                start_time = datetime.strptime(start, "%Y%m%d%H%M%S")
                stop_time = datetime.strptime(stop, "%Y%m%d%H%M%S")
                
                start_time = start_time + timedelta(hours=1)
                stop_time = stop_time + timedelta(hours=1)

                start = start_time.strftime("%Y%m%d%H%M%S") + TS
                stop = stop_time.strftime("%Y%m%d%H%M%S") + TS
                self.programmes.append({"channel": id, "start": start, "stop": stop, "title": [(name, "")], "desc": [(desc, "")]})
        return self.channels, self.programmes


def EPG_Generator(channelList):
    #os.system('cls||clear')
    channels = []
    programmes = []
    print("TV.SMS.cz kanály")
    print("Stahuji data...")
    
    channels_ = Get_channels_sms()
    ch, channels_sms = channels_.own_channels(channelList)
    channels.extend(channels_sms)

    programmes_ = Get_programmes_sms(days_back, days)
    programmes_sms = programmes_.data_programmes(ch)
    programmes.extend(programmes_sms)
    
    print("Other Channels")
    print("Stahuji data...")
    channels_tvtv, programmes_tvtv = Others().data_own_programmes(channelList)

    channels.extend(channels_tvtv)
    programmes.extend(programmes_tvtv)

    if channels != []:
        print("Celkem kanálů: " + str(len(channels)))
        print("Generuji...")
        w = xmltv.Writer(encoding="utf-8", source_info_url="http://www.funktronics.ca/python-xmltv", source_info_name="Funktronics", generator_info_name="python-xmltv", generator_info_url="http://www.funktronics.ca/python-xmltv")
        for c in channels:
            w.addChannel(c)
        for p in programmes:
            w.addProgramme(p)

        w.write("epg.xml", pretty_print=True, gzip_=False)
        sys.stdout.write('\x1b[1A')
        sys.stdout.write('\x1b[2K')
        now = datetime.now()
        dt = now.strftime("%d.%m.%Y %H:%M")
        print("Hotovo (" + dt + ")\n\n")

    with open('epg.xml', 'rb') as f_in, gzip.open('epg.xml.gz', 'wb') as f_out:
        f_out.writelines(f_in)

    os.remove("epg.xml")

    return
