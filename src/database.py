__all__ = ('connect_to_server', 'list_databases', 'list_tables', 'get_columns', 'update_row', 'delete_row', 'insert_row')

from mysql.connector import connect, Error, IntegrityError


# All my database wrapping functions
# I didn't make it a class because there are so many connections.
# i guess I could have made a sort or Pool class that just has the dictionary of connections
# i can go into what ifs all day


# Start the initial connection
def connect_to_server(s):
    try:
        connection = connect(host=s['host'], port=int(s['port']), user=s['user'], password=s['password'])
    except Error as e:
        return e
    return connection


# Execute a query, returning all results and rolling back on failure
def execute_query(connection, query, fetch=True):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Error as e:
        connection.rollback()
        raise e
    if fetch:
        return cursor.fetchall()


# Get a list of the databases in a server from the information schemea and clean out backend databases
def list_databases(connection, clean=True):
    dbs = execute_query(connection, 'show databases')
    db_list = []
    for db in dbs:
        # Filter out backend databases
        if clean and ('#' in db[0] or 'schema' in db[0] or 'mysql' in db[0]):
            continue
        db_list.append(([connection], {'name': db[0]}))
    return db_list


# Show tables that aer in a database
def list_tables(connection, database):
    tbs = execute_query(connection, f'show tables from {database}')
    tb_list = []
    for tb in tbs:
        tb_list.append(([connection, database], {'name': tb[0]}))
    return tb_list


# List columns from a database, used in the browser panel so I format it specifically for that
def list_columns(connection, database, table):
    cursor = connection.cursor()
    cursor.execute(f'select COLUMN_KEY, COLUMN_NAME, COLUMN_TYPE from information_schema.COLUMNS where TABLE_NAME=\'{table}\' and TABLE_SCHEMA=\'{database}\'')
    cols = cursor.fetchall()
    col_list = []
    for column_key, column_name, column_type in cols:
        name = f'{column_key} - {column_name} {column_type}'
        col_list.append(([], {'name': name}))
    return col_list


# Similar to above but just returns a plain list
def get_columns(connection, database, table):
    cols = execute_query(connection, f'select COLUMN_KEY, COLUMN_NAME, COLUMN_TYPE from information_schema.COLUMNS where TABLE_NAME=\'{table}\' and TABLE_SCHEMA=\'{database}\'')
    col_list = []
    for column_key, column_name, column_type in cols:
        col_list.append(f'{column_key} - {column_name} - {column_type}')
    return col_list


# The use statement
def use(connection, database):
    execute_query(connection, f'USE {database};', fetch=False)


# get EVERYTHING in a table
def get_table(connection, table, limit):
    return execute_query(connection, f'SELECT * FROM {table} LIMIT {limit};')


# Get the column types from the inforamtion schema
def get_types(table_name, database, connection):
    results = execute_query(connection, f'SELECT c.DATA_TYPE FROM information_schema.columns c WHERE c.TABLE_NAME=\'{table_name}\' AND c.TABLE_SCHEMA=\'{database}\';')
    types = []
    for data_type in results:
        types.append(data_type[0])
    return types

# Make sure that we are inserting a corectly formated type
def check_type(data_type, value):
    if data_type == 'int' or data_type == 'smallint':
        if value is None:
            return 0
        return int(value.strip())
    elif data_type == 'float':
        if value is None:
            return 0.0
        return float(value.strip())
    elif data_type == 'varchar':
        if value is None or value == '':
            return 'Null'
        return '\'' + value.strip().replace('\'', '\\\'') + '\''
    elif data_type == 'datetime':
        if value is None:
            return 'Null'
        return '\'' + value.strip().replace('\'', '\\\'') + '\''
    return value


# Update the row, constructing the query
def update_row(columns, identifiers, table, database, connection):
    types = get_types(table, database, connection)
    query = f"UPDATE {table} SET "
    first = True
    # construct the select clause
    for column_name, update_value in columns.items():
        if first:
            first = False
        else:
            query += ', '
        query += f"{column_name}={check_type(types[list(identifiers.keys()).index(column_name)], update_value)}"
    query += ' WHERE '
    index = 0
    first = True
    # construct the where clause
    for column_name, current_value in identifiers.items():
        if first:
            first = False
        else:
            query += ' AND '
        query += f"{column_name}={check_type(types[index], current_value)}"
        index += 1
    query += ';'

    # Fallback on error
    execute_query(connection, query, fetch=False)
    connection.commit()


# Delete the row,
def delete_row(table_name, columns, row, database, connection):
    types = get_types(table_name, database, connection) # get types
    query = f"DELETE FROM {table_name} WHERE "
    first = True
    for x, column_name in enumerate(columns):
        if first:
            first = False
        else:
            query += ' AND '
        query += f"{column_name}={check_type(types[x], row[x]['text_value'])}"
    query += ';'

    # Fallback on error
    try:
        execute_query(connection, query, fetch=False)
    except IntegrityError:
        return 'Something depends on that row; You cannot delete it'
    connection.commit()


# insert into the database a single row
def insert_row(row, table_name, database, connection):
    types = get_types(table_name, database, connection)
    query = f"INSERT INTO {table_name} VALUE ("
    first = True
    for x, col in enumerate(row):
        if first:
            first = False
        else:
            query += ', '
        query += f"{check_type(types[x], col['text_value'])}"
    query += ');'

    # fallback on error
    try:
        execute_query(connection, query, fetch=False)
    except IntegrityError:
        return 'You need to add the foreign key row first! Foreign key failed.'
    connection.commit()
