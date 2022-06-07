import psycopg2 as pg
import pandas as pd 
from configparser import ConfigParser


def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]

    else:
        raise Exception('section {0} not found in the {1} file'.format(section, filename))

    return db


def connect(type_clustering):
    """ Connect to the PostgreSQL database server """
    conn = None 
    try:
        # Read connection parameters
        params = config()

        # Connect to the PostgreSQL server
        conn = pg.connect(**params)

        # Create dataframe
        lines_in_cites = pd.read_sql('SELECT * FROM osm.lines_in_'+str(type_clustering)+';', conn)

        line_length_in_cites = pd.read_sql('SELECT * FROM osm.lines_lenght_in_'+str(type_clustering)+';', conn )

        tags_in_cites = pd.read_sql('SELECT * FROM osm.tags_in_'+str(type_clustering)+';', conn )

    except (Exception, pg.DatabaseError) as error:
        print(error)

    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
            return lines_in_cites, line_length_in_cites, tags_in_cites


