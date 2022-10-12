#!/usr/bin/env python
# -*- coding: utf-8 -*-

# D'aprés http://sametmax.com/ecrire-des-logs-en-python/
import logging
from logging.handlers import RotatingFileHandler


def init_logs(logsrep,programme,niveau):
    
    logsfile = logsrep + "/" + programme + ".log"
    # création de l'objet logger qui va nous servir à écrire dans les logs
    logger = logging.getLogger(programme)
    # on met le niveau du logger à DEBUG, comme ça il écrit tout
    logger.setLevel(getattr(logging, niveau))

    # création d'un formateur qui va ajouter le temps, le niveau
    # de chaque message quand on écrira un message dans le log
    formatter = logging.Formatter(u'%(asctime)s :: %(levelname)s :: %(message)s') # AlP : ajout du u pour l'encoding utf-8 mais ça a pas marché 
    # création d'un handler qui va rediriger une écriture du log vers
    # un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
    file_handler = RotatingFileHandler(logsfile, 'a', 10000000, 1, encoding="utf-8") # AlP : ajout de l'encoding utf-8 mais ça a pas marché 
    # on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
    # créé précédement et on ajoute ce handler au logger
    file_handler.setLevel(getattr(logging, niveau))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # création d'un second handler qui va rediriger chaque écriture de log
    # sur la console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, niveau))
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.debug('Le logger est dans la place !')