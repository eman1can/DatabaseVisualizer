__all__ = ('connect_to_server', 'list_databases', 'list_tables', 'list_columns')

from mysql.connector import connect, Error


def connect_to_server(s):
    try:
        print(s['host'])
        print(int(s['port']))
        print(s['user'])
        print(s['password'])
        connection = connect(host=s['host'], port=int(s['port']), user=s['user'], password=s['password'])
    except Error as e:
        print('ERROR', e)
        return None
    return connection


def list_databases(connection, clean=True):
    cursor = connection.cursor()
    cursor.execute('show databases')
    dbs = cursor.fetchall()
    db_list = []
    for db in dbs:
        # Filter out backend databases
        if clean and ('#' in db[0] or 'schema' in db[0] or 'mysql' in db[0]):
            continue
        db_list.append(([connection], {'name': db[0]}))
    return db_list


def list_tables(connection, database):
    cursor = connection.cursor()
    cursor.execute(f'show tables from {database}')
    tbs = cursor.fetchall()
    tb_list = []
    for tb in tbs:
        tb_list.append(([connection, database], {'name': tb[0]}))
    return tb_list


def list_columns(connection, database, table):
    cursor = connection.cursor()
    cursor.execute(f'select COLUMN_KEY, COLUMN_NAME, COLUMN_TYPE from information_schema.COLUMNS where TABLE_NAME=\'{table}\' and TABLE_SCHEMA=\'{database}\'')
    cols = cursor.fetchall()
    col_list = []
    for column_key, column_name, column_type in cols:
        name = f'{column_key} - {column_name} {column_type}'
        col_list.append(([], {'name': name}))
    return col_list
