#!/usr/bin/python3

from usa import bea, config, eia
import common.config
from common import sqlhelper
from common.dbconnect import db

def runsql(sql):
    print(sql)
    db.execute(sql)

def dopostparse():
    create_code_tables()
    create_hybrid_tables()
    create_test_views()

# codes for hybrid table with our own sectors
def create_code_tables():
    for year in config.STUDY_YEARS:
        hybrid_code_table = "hybrid_codes_%d" % year
        runsql("DROP TABLE IF EXISTS %s" % hybrid_code_table)
    
        code_table = "%s.codes_%d" % (config.IO_SCHEMA, year)
        runsql("""
            SELECT code, description, CASE
                   WHEN %s THEN '%s'
                   WHEN %s THEN '%s'
                   ELSE '%s' END AS sector_type
              INTO %s
              FROM %s
             WHERE code <> '%s'"""
               % (bea.fd_sector_criteria[year], bea.FINAL_DEMAND,
                  bea.va_sector_criteria[year], bea.VALUE_ADDED,
                  bea.INTERMEDIATE_OUTPUT,
                  hybrid_code_table,
                  code_table,
                  eia.source_naics_map['PA'][year]))
    
        for source in ["PA-trans", "PA-nontrans"]:
            source_index = eia.modified_sources.index(source)
            source_name = eia.modified_source_names[source]
    
            runsql("""INSERT INTO %s
                      VALUES ('%s', '%s', '%s')"""
                   % (hybrid_code_table,
                      eia.source_naics_map[source][year],
                      source_name,
                      bea.INTERMEDIATE_OUTPUT))

def create_hybrid_tables():
    for year in config.STUDY_YEARS:
        strings = {
            # table names
            "eia_table": "%s.seds_us_%d" % (config.EIA_SCHEMA, year),
            "io_table": "%s.transact_view_%d" % (config.IO_SCHEMA, year),
            "map_table": "%s.eia_code_map_%d" % (config.IO_SCHEMA, year),
            "hybrid_table": "hybrid_transactions_%d" % year,
    
            # selected sector codes
            "pa_trans_code": eia.source_naics_map['PA-trans'][year],
            "pa_nontrans_code": eia.source_naics_map['PA-nontrans'][year],
            }
    
        runsql("DROP TABLE IF EXISTS %s CASCADE" % strings["hybrid_table"])
        runsql("""
            CREATE TABLE %(hybrid_table)s (
                from_sector varchar(6),
                to_sector varchar(6),
                expenditure float
            )""" % strings)
        
        for source in eia.sources:
            strings["shares_view"] = "%s_ex_proportions_%s" % (source.lower(), year)
            strings["source"] = source
            strings["source_naics"] = eia.source_naics_map[source][year]
    
            # seds prices are c.i.f., but when allocating btu among user
            # industries it is unfair to assign based on c.i.f. since what
            # they end up using is f.o.b.
            subquery = """
                SELECT codes.eia_sector, sum(io.fob) as fob
                  FROM %(io_table)s io, %(map_table)s codes
                 WHERE codes.eia_source = '%(source)s'
                   AND io.from_sector = '%(source_naics)s'
                   AND io.to_sector = codes.io_sector
                 GROUP BY codes.eia_sector""" % strings
    
            strings["subquery"] = subquery
    
            # the price each industry ends up actually paying for energy
            # should be the f.o.b. price which is (fob / cif) of the seds price
            runsql("""
            CREATE OR REPLACE VIEW %(shares_view)s AS
                SELECT io.to_sector, codes.eia_sector,
                       cast(io.fob as float) / cast(io.cif as float) as fob_share,
                       cast(io.fob as float) / cast(totals.fob as float) as ex_share
                  FROM %(io_table)s io, %(map_table)s codes,
                       (%(subquery)s) totals
                 WHERE codes.eia_source = '%(source)s'
                   AND io.from_sector = '%(source_naics)s'
                   AND io.to_sector = codes.io_sector
                   AND totals.eia_sector = codes.eia_sector""" % strings)
        
            # split petroleum
            if source == 'PA':
                strings["aviation_pa"] = sqlhelper.set_repr(
                    eia.aviation_petroleum)
                strings["other_pa"] = sqlhelper.set_repr(
                    eia.other_petroleum)
                strings["all_pa"] = sqlhelper.set_repr(
                    eia.aviation_petroleum + eia.other_petroleum)

                strings["pa_nontrans_view"] = "pa_nontrans_%d" % year
                strings["pa_trans_view"] = "pa_trans_%d" % year
                strings["pa_trans_shares_view"] = "pa_trans_proportions_%d" % year
                strings["aviation_code"] = eia.air_transportation_codes[year]
    
                # non transportation petroleum use
                runsql("""
                CREATE OR REPLACE VIEW %(pa_nontrans_view)s AS
                    SELECT shares.to_sector, shares.eia_sector,
                           sum(shares.ex_share * eia.use_btu) as btu,
                           sum(shares.ex_share * eia.use_btu
                               * eia.price * shares.fob_share) as ex
                      FROM %(shares_view)s shares, %(eia_table)s eia
                     WHERE eia.source in %(all_pa)s
                       AND shares.eia_sector = eia.sector
                       -- these two below are double counted
                       AND eia.source || eia.sector not in ('DFEI', 'PCIC')
                       AND eia.sector <> 'AC'
                     GROUP BY shares.to_sector, shares.eia_sector""" % strings)
        
                # petroleum use for transportation other than air
                runsql("""
                CREATE OR REPLACE VIEW %(pa_trans_view)s AS
                    SELECT io.to_sector, io.fob,
                           io.fob - nontrans.ex as remaining
                      FROM %(io_table)s io, %(pa_nontrans_view)s nontrans
                     WHERE io.from_sector = '%(source_naics)s'
                       AND io.to_sector = nontrans.to_sector
                       -- remaining is negative for IC and EI
                       AND nontrans.eia_sector in ('CC', 'RC')
                   UNION
                    SELECT io.to_sector, io.fob,
                           cast(io.fob as float) as remaining
                      FROM %(io_table)s io, %(map_table)s codes
                     WHERE io.from_sector = '%(source_naics)s'
                       AND io.to_sector = codes.io_sector
                       AND codes.eia_source = 'PA'
                       AND codes.eia_sector = 'AC'
                       AND io.to_sector <> '%(aviation_code)s' """ % strings)
    
                # proportions for petroleum allocated to transportation
                runsql("""
                CREATE OR REPLACE VIEW %(pa_trans_shares_view)s AS
                    SELECT use.to_sector, use.remaining / total.total as ex_share
                      FROM %(pa_trans_view)s use,
                           (SELECT sum(remaining) as total
                              FROM %(pa_trans_view)s) total""" % strings)
    
                # allocate all of JF and AV to air transportation
                runsql("""
                INSERT INTO %(hybrid_table)s
                    SELECT '%(pa_trans_code)s', io.to_sector, sum(eia.use_btu)
                      FROM %(io_table)s io,
                           %(eia_table)s eia
                     WHERE eia.source in %(aviation_pa)s
                       and eia.sector = 'AC'
                       and io.from_sector = '%(source_naics)s'
                       and io.to_sector = '%(aviation_code)s'
                     GROUP BY io.to_sector """ % strings)
    
                # allocate all other transportation
                runsql("""
                INSERT INTO %(hybrid_table)s
                    SELECT '%(pa_trans_code)s',
                           shares.to_sector, sum(shares.ex_share * eia.use_btu)
                      FROM %(pa_trans_shares_view)s shares, %(eia_table)s eia
                     WHERE eia.source in %(other_pa)s
                       AND eia.sector = 'AC'
                     GROUP BY shares.to_sector""" % strings)
    
                # allocate non-transportation petroleum use
                runsql("""
                INSERT INTO %(hybrid_table)s
                    SELECT '%(pa_nontrans_code)s', to_sector, btu
                      FROM %(pa_nontrans_view)s""" % strings)
                     #WHERE eia_sector in ('IC', 'EI')"""
    
                # dependencies in reverse order
                runsql("DROP VIEW %s" % strings["pa_trans_shares_view"])
                runsql("DROP VIEW %s" % strings["pa_trans_view"])
                runsql("DROP VIEW %s" % strings["pa_nontrans_view"])
                runsql("DROP VIEW %s" % strings["shares_view"])
    
            else:
                runsql("""
                INSERT INTO %(hybrid_table)s
                    SELECT '%(source_naics)s',
                           shares.to_sector, shares.ex_share * eia.use_btu
                      FROM %(shares_view)s shares, %(eia_table)s eia
                     WHERE eia.source = '%(source)s'
                       AND shares.eia_sector = eia.sector""" % strings)
    
                runsql("DROP VIEW %s" % strings["shares_view"])
    
        # insert remainder of standard io table
        energy_sectors = []
        for source in eia.sources:
            energy_sectors.append(eia.source_naics_map[source][year])
    
        strings["sectors"] = ", ".join(["'%s'" % s for s in energy_sectors])
    
        db.execute("""
            INSERT INTO %(hybrid_table)s
            SELECT from_sector, to_sector, fob
              FROM %(io_table)s
             WHERE from_sector not in (%(sectors)s)""" % strings)
    
        # split petroleum column proportional to trans and nontrans uses
        stmt = db.prepare("""
            SELECT trans.use_btu / total.use_btu as trans_share
              FROM (SELECT use_btu FROM %(eia_table)s
                     WHERE source = 'PA' AND sector = 'AC') trans,
                   (SELECT use_btu FROM %(eia_table)s
                     WHERE source = 'PA' AND sector = 'TC') total""" % strings)
    
        result = stmt()
        if len(result) and len(result[0]):
            strings["pa_naics"] = eia.source_naics_map['PA'][year]
            strings["trans_share"] = result[0][0]
            strings["nontrans_share"] = 1 - result[0][0]
    
            # transportation petroleum use column
            runsql("""
                INSERT INTO %(hybrid_table)s
                SELECT from_sector, '%(pa_trans_code)s',
                       %(trans_share).4f * expenditure
                  FROM %(hybrid_table)s
                 WHERE to_sector = '%(pa_naics)s' """ % strings)
    
            # non-transportation petroleum use column
            runsql("""
                UPDATE %(hybrid_table)s
                   SET expenditure = %(nontrans_share).4f * expenditure,
                       to_sector = '%(pa_nontrans_code)s'
                 WHERE to_sector = '%(pa_naics)s' """ % strings)

def create_test_views():
    for source in eia.sources:
        testview = "%s.hybrid_use_%s" % (common.config.TEST_SCHEMA, source.lower())
        compareview = "%s.hybrid_vs_eia_%s" % (common.config.TEST_SCHEMA, source.lower())
        subqueries = []
        for year in config.STUDY_YEARS:
            hybrid_table = "hybrid_transactions_%d" % year
    
            if source == 'PA':
                from_sector_cond = "from_sector in ('%s', '%s')" % \
                    (eia.source_naics_map["PA-trans"][year],
                     eia.source_naics_map["PA-nontrans"][year])
            else:
                from_sector_cond = "from_sector = '%s'" % \
                    eia.source_naics_map[source][year]
    
            subquery = "SELECT %d AS year," % year + \
                             " to_sector, expenditure AS btu\n" + \
                       "  FROM %s\n" % hybrid_table + \
                       " WHERE %s" % from_sector_cond
            subqueries.append(subquery)
    
        runsql("CREATE OR REPLACE VIEW %s AS\n %s" % \
            (testview, "\nUNION\n".join(subqueries)))
    
        runsql("""CREATE OR REPLACE VIEW %s AS
           SELECT eia.year, eia.use_btu, hybrid.btu
             FROM (SELECT * FROM eia.seds_use_btu
                    WHERE source = '%s' AND sector = 'TC') eia,
                  (SELECT year, sum(btu) AS btu
                     FROM %s GROUP BY year) hybrid
            WHERE eia.year = hybrid.year"""
               % (compareview, source, testview))

### EIA sector definitions:
# http://www.eia.gov/state/seds/sep_use/notes/use_intro.pdf

