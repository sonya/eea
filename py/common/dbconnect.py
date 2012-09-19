#!/usr/bin/python3

from common import config
import postgresql

db = postgresql.open("pq://localhost%s/%s" % (config.DB_PORT, config.DB_NAME))

