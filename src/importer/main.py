from src.importer.config_parser import Parser
from src.importer.connector import Connector
from os import listdir
from logging import info, warning, basicConfig, INFO
"""
The importer will do 2 things. It will parse and run an sql ddl file, and then load each table data.
"""

basicConfig(level=INFO)

file_path = '../data/'
# Files must be put into the data folder for the script to work
# The script will search the data folder for the files
ini_file = 'session.ini'
ddl_file = 'ddl.sql'

server_name = 'testing'  # The server connection from session.ini to use
database_name = 'imdb'

if __name__ == "__main__":
    # initalize my parser definition and conenct to the server
    config_parser = Parser()
    config_parser.init_config_parser(file_path + ini_file)
    config_parser.init_sql_parser(file_path + ddl_file)
    connector = Connector(config_parser.get_server(server_name))

    # Create the database itself, dropping it if it already existed
    info(f'Creating database `{database_name}`')
    connector.create_database(database_name)

    # Load the ddl for the database
    # This will read each sql statement in a .sql file and loop through them with an iterator
    info('Running DDL Script')
    table_names = []
    sql_st = config_parser.get_statement()
    while sql_st is not None:
        info(f'Executing "{sql_st}"')
        connector.execute_query(sql_st)
        # If we create a table in the ddl, add it to the table list.
        # This allows us to load data in order of creation so there are no reference failures
        if sql_st.lower().startswith('create table'):
            index_start = sql_st.index('`') + 1
            index_end = sql_st.index('`', index_start)
            table_names.append(sql_st[index_start:index_end])
        sql_st = config_parser.get_statement()
    connector.commit()

    # load data into tables
    info('Importing table data')
    files = listdir(file_path)
    # We loop through every table that was created and if a .csv file is in the data folder with the format `<table_name>_something.csv`
    # then we load that csv data into the table
    for table_name in table_names:
        data_found = False
        for file in files:
            if file.endswith('.csv') and table_name == file[:file.rindex('_')]:
                info(f'Importing data for {table_name}')
                # Columns are loaded from the csv and dynamically casted based on the type of the column read from the information table of the database
                types = connector.get_col_types(table_name)
                config_parser.parse_file(lambda lines: connector.insert(table_name, lines, types), file_path + file)
                connector.commit()
                data_found = True
                break
        if not data_found:
            warning(f'Table data for {table_name} was not imported')
    connector.close()
    info('Finished importing all data; Closing')
