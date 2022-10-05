# -*- coding: utf-8 -*- 

# Based on Abes_Apis_Intreface/AbesXml by @louxfaure
# Created for Koha 20.11

# À améliorer pour que ça prenne aussi en compte le "private" getBiblio

import os
import re
# external imports
import requests
import logging
import xml.etree.ElementTree as ET
import json
# internal import
import logs
from datetime import datetime

NS = {
    'marc': 'http://www.loc.gov/MARC21/slim'
    }

class Koha_API_PublicBiblio(object):
    """Koha_API_PublicBiblio
    =======
    A set of function wich handle data returned by Koha API 'getBiblioPublic' 
    https://api.koha-community.org/20.11.html#operation/getBiblioPublic
    On init take as arguments :
    - biblionumber (Koha identifier)
    - Koha server URL
    - [optional] : format (the response format) :
        - "application/marcxml+xml" (default)
        - "application/marc-in-json"
        - "application/marc"
        - "text/plain"

    ex : 
"""

    def __init__(self,bibnb,kohaUrl,service='Koha_API_PublicBiblio', format="application/marcxml+xml"):
        self.logger = logging.getLogger(service)
        self.endpoint = kohaUrl + "/api/v1/public/biblios/"
        self.service = service
        self.bibnb = str(bibnb)
        if format not in ["application/marcxml+xml",
                        "application/marc-in-json",
                        "application/marc",
                        "text/plain"]:
            self.format = "application/marcxml+xml"
        else:
            self.format = format
        #self.error_msg = ""
        if re.sub("\D", "", self.bibnb) != self.bibnb: # |||revoir cette conditin
            self.status = "Error"
            self.logger.error("{} :: Koha_API_PublicBiblio :: Biblionumber invalide".format(bibnb))
            self.error_msg = "Biblionumber invalide"
        else:
            url =  '{}/{}'.format(self.endpoint, self.bibnb) #Changer ça
            payload = {
                
                }
            headers = {
                "accept":self.format
                }
            r = requests.get(url, headers=headers, params=payload)
            try:
                r.raise_for_status()  
            except requests.exceptions.HTTPError:
                self.status = 'Error'
                self.logger.error("{} :: Koha_API_PublicBiblio_Init :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(bibnb, r.status_code, r.request.method, r.url, r.text))
                self.error_msg = "Biblionumber inconnu ou service indisponible"
            else:
                # apparently its double-encoded in JSON ?? See : https://stackoverflow.com/questions/4267019/double-decoding-unicode-in-python
                # So yeah, decode->encode->decode for JSON
                if self.format == "application/marc-in-json":
                    self.record = r.content.decode('utf-8').encode('raw_unicode_escape').decode('utf-8')
                else:
                    self.record = r.content.decode('utf-8')
                self.status = 'Success'
                self.logger.debug("{} :: Koha_API_PublicBiblio :: Notice trouvée".format(bibnb))

    def get_record(self):
            """Return the entire record as a string of the specified format.
            """
            return self.record

    def get_init_status(self):
        """Return the init status as a string.
        """
        return self.status

    def get_error_msg(self):
        """Return the error message as a string.
        """
        if hasattr(self, "error_msg"):
            return self.error_msg
        else:
            return "Pas de message d'erreur"  

    def get_leader(self):
        """Return the leader field content as a string.

        Application/marc and Text/plain formats are not supported for the time being.
        """
        if self.format == "application/marcxml+xml":
            root = ET.fromstring(self.record)
            return root.find("./marc:leader", NS).text
        elif self.format == "application/marc-in-json":
            return json.loads(self.record)["leader"]
        elif self.format == "application/marc" or self.format == "text/plain":
            return "Pas de prise en charge de ce format pour le moment."

    def get_title_info(self):
        """Return the first 200 field's title content as a string.
        Each subfield is separated by a space.

        Application/marc and Text/plain formats are not supported for the time being.
        """
        key_title = []
        
        if self.format == "application/marcxml+xml":
            root = ET.fromstring(self.record)
            for subfield in root.find("./marc:datafield[@tag='200']", NS).findall("./marc:subfield", NS):
                if subfield.attrib['code'] in ('a','d','e','h','i','v') :
                    key_title.append(subfield.text)

        elif self.format == "application/marc-in-json":
            for field in json.loads(self.record)["fields"]:
                if "200" in field.keys():
                    for subfield in field["200"]["subfields"]:
                        code = list(subfield.keys())[0]
                        if code in ('a','d','e','h','i','v') :
                            key_title.append(subfield[code])
                    break # To match XML find first, prevents finding another 200
        
        elif self.format == "application/marc" or self.format == "text/plain":
            return "Pas de prise en charge de ce format pour le moment."
        
        return " ".join(key_title)

    def get_dates_pub(self):
        """Return all publication dates in the 100 field.
        Returns a tuple :
         - 100 field
         - date type (pos. 8)
         - 1st publication date (pos. 9-12)
         - 2nd publication date (pos. 13-16)

        Application/marc and Text/plain formats are not supported for the time being.
        """
        zone_100 = None
        date_type = None
        date_1 = None
        date_2 = None

        if self.format == "application/marcxml+xml":
            root = ET.fromstring(self.record)
            if root.find("./marc:datafield[@tag='100']/marc:subfield[@code='a']", NS) != None :
                zone_100 = root.find("./marc:datafield[@tag='100']/marc:subfield[@code='a']", NS).text
        
        elif self.format == "application/marc-in-json":
            for field in json.loads(self.record)["fields"]:
                if "100" in field.keys():
                    for subfield in field["100"]["subfields"]:
                        code = list(subfield.keys())[0]
                        if code == "a":
                            zone_100 = subfield[code]

        # elif self.format == "application/marc" or self.format == "text/plain":
        #     return "Pas de prise en charge de ce format pour le moment."
        
        date_type = zone_100[8:9]
        date_1 = zone_100[9:13]
        date_2 = zone_100[13:17]
        
        return zone_100,date_type,date_1,date_2

    def get_editeurs(self):
        """Return all publishers in 210/214$c subfields as a list.
        
        Application/marc and Text/plain formats are not supported for the time being.
        """
        ed_list = []

        if self.format == "application/marcxml+xml":
            root = ET.fromstring(self.record)
            for ed in root.findall("./marc:datafield[@tag='214']/marc:subfield[@code='c']", NS):
                ed_list.append(ed.text)
            for ed in root.findall("./marc:datafield[@tag='210']/marc:subfield[@code='c']", NS):
                ed_list.append(ed.text)

        elif self.format == "application/marc-in-json":
            for field in json.loads(self.record)["fields"]:
                tag = list(field.keys())[0]
                if tag == "210" or tag == "214":
                    for subfield in field[tag]["subfields"]:
                        code = list(subfield.keys())[0]
                        if code == "c":
                            ed_list.append(subfield[code])
        
        # elif self.format == "application/marc" or self.format == "text/plain":
        #     return "Pas de prise en charge de ce format pour le moment."

        return ed_list
        

    # Manque de AbesXml :
    #     get_ppn_autre_support
    # Manque peut-être :
    #     get_dates_pub_210/214

print(Koha_API_PublicBiblio(116946, "https://pro-ensa-koha.test.biblibre.eu", format="application/marc-in-json").get_editeurs())