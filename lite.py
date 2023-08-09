import xmltv
import re
import os
import sys
import gzip
import time
import unicodedata
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import io

TS = " +0000"

days = 5
days_back = 3


def replace_names(name, *args):
    return name

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


def get_tm_programmes(tm_ids, d, d_b, lng):
    if d > 10:
        d = 10
    if lng == "cz":
        prfx = "tm-"
    else:
        prfx = "mag-"
    tm_ids_list = tm_ids.split(",")
    programmes2 = []
    params={"dsid": "c75536831e9bdc93", "deviceName": "Redmi Note 7", "deviceType": "OTT_ANDROID", "osVersion": "10", "appVersion": "3.7.0", "language": lng.upper()}
    headers={"Host": lng + "go.magio.tv", "authorization": "Bearer", "User-Agent": "okhttp/3.12.12", "content-type":  "application/json", "Connection": "Keep-Alive"}
    req = requests.post("https://" + lng + "go.magio.tv/v2/auth/init", params=params, headers=headers, verify=True).json()
    token = req["token"]["accessToken"]
    headers2={"Host": lng + "go.magio.tv", "authorization": "Bearer " + token, "User-Agent": "okhttp/3.12.12", "content-type":  "application/json"}
    req1 = requests.get("https://" + lng + "go.magio.tv/v2/television/channels?list=LIVE&queryScope=LIVE", headers=headers2).json()["items"]
    channels2 = []
    ids = ""
    tvch = {}
    for y in req1:
        id = str(y["channel"]["channelId"])
        if tm_ids_list == [""]:
            name = y["channel"]["name"]
            logo = str(y["channel"]["logoUrl"])
            ids = ids + "," + id
            tm = str(ids[1:])
            tvch[name] = prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-")
            channels2.append(({"display-name": [(replace_names(name.replace(" HD", "")), u"cs")], "id": prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-"), "icon": [{"src": logo}]}))
        else:
            if id in tm_ids_list:
                name = y["channel"]["name"]
                logo = str(y["channel"]["logoUrl"])
                ids = ids + "," + id
                tm = str(ids[1:])
                tvch[name] = prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-")
                channels2.append(({"display-name": [(name.replace(" HD", ""), u"cs")], "id": prfx + id + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-"), "icon": [{"src": logo}]}))
    now = datetime.now()
    for i in range(d_b*-1, d):
        next_day = now + timedelta(days = i)
        back_day = (now + timedelta(days = i)) - timedelta(days = 1)
        date_to = next_day.strftime("%Y-%m-%d")
        date_from = back_day.strftime("%Y-%m-%d")
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_)
        req = requests.get("https://" + lng + "go.magio.tv/v2/television/epg?filter=channel.id=in=(" + tm + ");endTime=ge=" + date_from + "T23:00:00.000Z;startTime=le=" + date_to + "T23:59:59.999Z&limit=" + str(len(channels2)) + "&offset=0&lang=" + lng.upper(), headers=headers2).json()["items"]
        for x in range(0, len(req)):
            for y in req[x]["programs"]:
                channel = y["channel"]["name"]
                start_time = y["startTime"].replace("-", "").replace("T", "").replace(":", "")
                stop_time = y["endTime"].replace("-", "").replace("T", "").replace(":", "")
                title = y["program"]["title"]
                desc = y["program"]["description"]
                epi = y["program"]["programValue"]["episodeId"]
                if epi != None:
                    title = title + " (" + epi + ")"
                year = y["program"]["programValue"]["creationYear"]
                try:
                    subgenre = y["program"]["programCategory"]["subCategories"][0]["desc"]
                except:
                    subgenre = ''
                try:
                    genre = [(y["program"]["programCategory"]["desc"], u''), (subgenre, u'')]
                except:
                    genre = None
                try:
                    icon = y["program"]["images"][0]
                except:
                    icon = None
                try:
                    directors = []
                    for dr in y["program"]["programRole"]["directors"]:
                        directors.append(dr["fullName"])
                except:
                    directors = []
                try:
                    actors = []
                    for ac in y["program"]["programRole"]["actors"]:
                        actors.append(ac["fullName"])
                except:
                    actors = []
                try:
                    programm = {'channel': tvch[channel], 'start': start_time + TS, 'stop': stop_time + TS, 'title': [(title, u'')], 'desc': [(desc, u'')]}
                    if year != None:
                        programm['date'] = year
                    if genre != None:
                        programm['category'] = genre
                    if icon != None:
                        programm['icon'] = [{"src": icon}]
                    if directors != []:
                        programm['credits'] = {"director": directors}
                        if actors != []:
                            programm['credits'] = {"director": directors, "actor": actors}
                    if actors != []:
                        programm['credits'] = {"actor": actors}
                        if directors != []:
                            programm['credits'] = {"actor": actors, "director": directors}
                    if programm not in programmes2:
                        programmes2.append(programm)
                except:
                    pass
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels2, programmes2


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
                
                start_time = start_time + timedelta(hours=2)
                stop_time = stop_time + timedelta(hours=2)

                start = start_time.strftime("%Y%m%d%H%M%S") + TS
                stop = stop_time.strftime("%Y%m%d%H%M%S") + TS
                self.programmes.append({"channel": id, "start": start, "stop": stop, "title": [(name, "")], "desc": [(desc, "")]})
        return self.channels, self.programmes


def get_muj_tv_programmes(ids, d, d_b):
    ids = ids.split(",")
    if d_b > 1:
        d_b = 1
    if d > 10:
        d = 10
    channels = []
    programmes = []
    ids_ = {'723': '723-skylink-7', '233': '233-stingray-classica', '234': '234-stingray-iconcerts', '110': '110-stingray-cmusic', '40': '40-orf1', '41': '41-orf2', '49': '49-rtl', '50': '50-rtl2', '39': '39-polsat', '37': '37-tvp1', '38': '38-tvp2', '174': '174-pro7', '52': '52-sat1', '54': '54-kabel1', '53': '53-vox', '393': '393-zdf', '216': '216-zdf-neo', '46': '46-3sat', '408': '408-sat1-gold', '892': '892-vixen', '1040': '1040-canal+sport'}
    channels = []
    c = {'display-name': [(replace_names('Skylink 7'), u'cs')], 'id': '723-skylink-7','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=ac6c69625699eaecc9b39f7ea4d69b8c&amp;p2=80'}]}, {'display-name': [(replace_names('Stingray Classica'), u'cs')], 'id': '233-stingray-classica','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=661af53f8f3b997611c29f844c7006fd&amp;p2=80'}]}, {'display-name': [(replace_names('Stingray iConcerts'), u'cs')], 'id': '234-stingray-iconcerts','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=99c87946872c81f46190c77af7cd1d89&amp;p2=80'}]}, {'display-name': [(replace_names('Stingray CMusic'), u'cs')], 'id': '110-stingray-cmusic','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=b323f2ad3200cb938b43bed58dd8fbf9&amp;p2=80'}]}, {'display-name': [(replace_names('ORF1'), u'cs')], 'id': '40-orf1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=422162d3082a84fc97a7fb9b3ad6823f&amp;p2=80'}]}, {'display-name': [(replace_names('ORF2'), u'cs')], 'id': '41-orf2','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=477dcc38e54309f5db7aec56b62b4cdf&amp;p2=80'}]}, {'display-name': [(replace_names('RTL'), u'cs')], 'id': '49-rtl','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=7cb9005e66956c56fd0671ee79ee2471&amp;p2=80'}]}, {'display-name': [(replace_names('RTL2'), u'cs')], 'id': '50-rtl2','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=418e0d04529ea3aaa2bc2c925ddf5982&amp;p2=80'}]}, {'display-name': [(replace_names('Polsat'), u'cs')], 'id': '39-polsat','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=f54e290782e8352303cfe43ce949d339&amp;p2=80'}]}, {'display-name': [(replace_names('TVP1'), u'cs')], 'id': '37-tvp1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=770431539d1fa662f705c1c05a0dd943&amp;p2=80'}]}, {'display-name': [(replace_names('TVP2'), u'cs')], 'id': '38-tvp2','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=e2ce4065f27ce199f7613f38878cef72&amp;p2=80'}]}, {'display-name': [(replace_names('Pro7'), u'cs')], 'id': '174-pro7','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=e23a7fb8caff9ff514f254c43a39d9b6&amp;p2=80'}]}, {'display-name': [(replace_names('SAT1'), u'cs')], 'id': '52-sat1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=97dd916e0164fff141065c3fba71c291&amp;p2=80'}]}, {'display-name': [(replace_names('Kabel1'), u'cs')], 'id': '54-kabel1','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=be6dc88dd3c1c243ba4f28cccb8f1d34&amp;p2=80'}]}, {'display-name': [(replace_names('VOX'), u'cs')], 'id': '53-vox','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=d2c68d2b145a5f2e20e5c05c20a9679e&amp;p2=80'}]}, {'display-name': [(replace_names('ZDF'), u'cs')], 'id': '393-zdf','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=dad48d516fbdb30321564701cc3faa04&amp;p2=80'}]}, {'display-name': [(replace_names('ZDF Neo'), u'cs')], 'id': '216-zdf-neo','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=cd5b8935893b0e4cde41bc3720435f14&amp;p2=80'}]}, {'display-name': [(replace_names('3SAT'), u'cs')], 'id': '46-3sat','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=58d350c6065d9355a52c6dbc3b31b185&amp;p2=80'}]}, {'display-name': [(replace_names('SAT.1 GOLD'), u'cs')], 'id': '408-sat1-gold','icon': [{'src': ''}]}, {'display-name': [(replace_names('Vixen'), u'cs')], 'id': '892-vixen','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=4499ebafb26a915859febcb4306703ca&amp;p2=80'}]}, {'display-name': [(replace_names('Canal+ Sport'), u'cs')], 'id': '1040-canal+sport','icon': [{'src': 'https://services.mujtvprogram.cz/tvprogram2services/services/logoImageDownloader.php?p1=ab73879fdf9b10e1deb0224bfbb3cfd8&amp;p2=80'}]}
    for x in c:
        if x["id"].split("-")[0] in ids:
            channels.append(x)
    now = datetime.now()
    for x in range(d_b*-1, d):
        next_day = now + timedelta(days = x)
        date_ = next_day.strftime("%d.%m.%Y")
        print(date_)
        for y in ids:
            html = requests.post("https://services.mujtvprogram.cz/tvprogram2services/services/tvprogrammelist_mobile.php", data = {"channel_cid": y, "day": str(x)}).content
            root = ET.fromstring(html)
            for i in root.iter("programme"):
                programmes.append({"channel": ids_[y],  "start": time.strftime('%Y%m%d%H%M%S', time.localtime(int(i.find("startDateTimeInSec").text))) + TS, "stop": time.strftime('%Y%m%d%H%M%S', time.localtime(int(i.find("endDateTimeInSec").text))) + TS, "title": [(i.find("name").text, "")], "desc": [(i.find("shortDescription").text, "")]})
        sys.stdout.write('\x1b[1A')
        print(date_ + "  OK")
    print("\n")
    return channels, programmes

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
    
    print("Magio Go kanály")
    print("Stahuji data...")
    mag_id = "4560,4561,4562,4563,4564,4565"
    channels_mag, programmes_mag = get_tm_programmes(mag_id, days, days_back, "sk")
    channels.extend(channels_mag)
    programmes.extend(programmes_mag)




    print("můjTVprogram.cz kanály")
    print("Stahuji data...")
    #mujtv_id = "723,233,234,110,40,41,49,50,39,37,38,174,52,54,53,393,216,46,408,892,1040"
    mujtv_id = "723"
    channels_mujtv, programmes_mujtv = get_muj_tv_programmes(mujtv_id, days, days_back)
    channels.extend(channels_mujtv)
    programmes.extend(programmes_mujtv)

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
