#!/usr/bin/python
#
# Copyright 2012 Sonya Huang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from usa import config, eia
import common.config
from common.dbconnect import db

def runsql(sql):
    print(sql)
    db.execute(sql)

def dopostparse():
    for year in config.STUDY_YEARS:
        tablename = config.IO_SCHEMA + ".eia_code_map_" + str(year)
        codetable = config.IO_SCHEMA + ".codes_" + str(year)
    
        db.execute("DROP TABLE IF EXISTS %s CASCADE" % tablename)
        db.execute("""
    CREATE TABLE %s (
        io_sector char(6),
        eia_source char(2),
        eia_sector char(2)
    );""" % tablename)
    
        if year <= 1992:
            conditions = eia.sector_naics_map_old
        else:
            conditions = eia.sector_naics_map
    
        for source in eia.sources:
            # AC prices for natural gas are zero for years prior to 1990
            # but except for petroleum, only the use_btu column is looked at
            # so this mapping still works for NG/AC before 1990.
            cases = ["WHEN %s THEN '%s'"
                         % (conditions[sector],
                            eia.valid_sectors_by_source[source][sector])
                         for sector in ("ind", "res", "elec", "com", "trans")]
    
            db.execute("""
    INSERT INTO %s
    SELECT code, '%s', CASE
           %s
           ELSE 'IC' END
      FROM %s;
    """ % (tablename, source, "\n       ".join(cases), codetable))
    
        # create views
        checktotal_parts = []
        checksector_parts = []
    
        strings = {
            "iotable": "%s.transact_view_%d" % (config.IO_SCHEMA, year),
            "eiatable": "%s.seds_us_%d" % (config.EIA_SCHEMA, year),
            "maptable": "%s.eia_code_map_%d" % (config.IO_SCHEMA, year),
            }
    
        for (eia_source, io_sectors) in eia.source_naics_map.items():
            if eia_source not in eia.sources:
                # make sure we don't create tables for modified sources
                continue

            strings["io_view"] = "io_%s_%d" % (eia_source.lower(), year)
            strings["from_sector"] = io_sectors[year]
            strings["eia_source"] = eia_source

            runsql("""
    CREATE OR REPLACE VIEW %(io_view)s AS
      SELECT io.to_sector, energy.sector, io.fob, io.cif,
             energy.price * (cast(io.fob as float) / cast(io.cif as float)) as price
        FROM %(iotable)s io,
             %(maptable)s codes,
             %(eiatable)s energy
       WHERE io.from_sector = '%(from_sector)s'
         AND energy.source = '%(eia_source)s'
         AND codes.eia_source = '%(eia_source)s'
         AND io.to_sector = codes.io_sector
         AND energy.sector = codes.eia_sector;
    """ % strings)

            checktotal_parts.append("""
      SELECT eia.source,
             CAST(eia.ex as int) AS eia_ex,
             SUM(io.cif) AS io_ex,
             CAST(eia.use_btu as int) AS eia_btu,
             CAST(SUM(io.fob / io.price) as int) AS io_btu
        FROM %(eiatable)s eia, %(io_view)s io
       WHERE eia.source = '%(eia_source)s'
         AND eia.sector = 'TC'
       GROUP BY eia.source, eia.ex, eia.use_btu
    """ % strings)
    
            checksector_parts.append("""
      SELECT eia.source, eia.sector,
             CAST(eia.ex as int) AS eia_ex,
             SUM(io.cif) AS io_ex,
             CAST(eia.use_btu as int) AS eia_btu,
             CAST(SUM(io.fob / io.price) as int) AS io_btu
        FROM %(eiatable)s eia, %(io_view)s io
       WHERE eia.source = '%(eia_source)s'
         AND eia.sector = io.sector
         AND eia.sector <> 'TC'
       GROUP BY eia.source, eia.sector, eia.price, eia.ex, eia.use_btu
    """ % strings)
    
        checktotal_view = "%s.eia_io_totals_%d" % (common.config.TEST_SCHEMA, year)
        checksector_view = "%s.eia_io_sectors_%d" % (common.config.TEST_SCHEMA, year)
    
        runsql("CREATE OR REPLACE VIEW %s AS %s" % \
            (checktotal_view, "UNION".join(checktotal_parts)))
        runsql("CREATE OR REPLACE VIEW %s AS %s" % \
            (checksector_view, "UNION".join(checksector_parts)))
