#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# ###################################################################################
# Copyright @ 2017 by Deloitte, All rights reserved                                 #
#                                                                                   #
# This software is proprietary to and embodies the confidential technology          #
# of Deloitte. Possession, use, or copying of this software and media is            #
# authorized only pursuant to a valid written license from Deloitte or              #
# an authorized sublicensor.                                                        #
#                                                                                   #
# File:       MongoDAO.py                                                           #
# Created:    Vivek                                                                 #
# updated:    Vivek                                                                 #
#                                                                                   #
#####################################################################################
# Import All required libraries

import configparser
from pymongo import MongoClient
import json
# Read the configuration file
# Read the configuration file
app_config = configparser.ConfigParser()
app_config.read_file(open(r'configuration/settings.ini'))
config_mongo_host = app_config.get('MONGODB', 'host')
config_mongo_port = app_config.get('MONGODB', 'port')
config_mongo_db = app_config.get('MONGODB', 'collection')

client = MongoClient('mongodb://'+app_config.get('MONGODB', 'host')+':'+app_config.get('MONGODB', 'port')+'/humanfactor')

class MongoDao:

    def gethumanfactor(RUN_INSTANCE_ID):
        print(RUN_INSTANCE_ID)
        results = client[config_mongo_db]['humanfactor'].find()
        output_result = []
        print(results.count())
        for result in results:
            output_result.append(result)
        return output_result
        #client[app_config.get('MONGODB', 'collection')]['Signaldetectalgooutput'].insert(dict(RUN_INSTANCE_ID))\

    def write_to_mongo(humanfactval,collectionName):
        output = humanfactval
        client[app_config.get('MONGODB', 'collection')][collectionName].insert(output)