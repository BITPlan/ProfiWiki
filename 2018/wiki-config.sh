#!/bin/bash
# wiki base configuration parameter
# when using docker compose this is the name of the database service
dbserver=db
# the databasename to use for the MySQL database to be use
dbname=wiki
# the database user to be used
dbuser=wikiuser
# The name of the wiki
wikiname=wiki
# The Wiki default user
wikiuser=Sysop
# Language of the wiki
wikilang=en
# the port to use
export MEDIAWIKI_PORT=8180
