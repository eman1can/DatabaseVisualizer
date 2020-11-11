from mysql.connector import connect, Error
from csv import reader


# The connector searches the data folder for the database connection
class Connector:
    def __init__(self, server_data):
        # will connect to a server with data from a .ini file
        try:
            self.connection = connect(**server_data)
            self.connection.autocommit = False
        except Error as e:
            print(f"The error '{e}' occurred")
            raise Exception("SQL Connection Error", e)
        self.cursor = self.connection.cursor()

    # Execute a sql statement, rolling back in case of error.
    # To commit the changes, call commit based on the loop of the situation
    def execute_query(self, query):
        try:
            self.cursor.execute(query)
        except Error as e:
            print(f"The error '{e}' occurred")
            self.connection.rollback()
            self.close()
            raise Exception("SQL Connection Error", e)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

    # The below are mostly used for setting up and inserting into a database
    def create_database(self, database_name):
        self.execute_query(f'DROP DATABASE IF EXISTS `{database_name}`;')
        self.execute_query(f'CREATE DATABASE `{database_name}`;')
        self.execute_query(f'USE `{database_name}`;')
        self.commit()

    # Get the list of all the tables
    def get_tables(self):
        tables = []
        self.execute_query('SHOW TABLES;')
        for table in self.cursor.fetchall():
            tables.append(table[0])
        return tables

    # Cast the value to the appropriate format
    def check_type(self, data_type, value):
        if data_type == 'int' or data_type == 'smallint':
            if value is None:
                return 0
            return int(value)
        elif data_type == 'float':
            if value is None:
                return 0.0
            return float(value)
        elif data_type == 'varchar':
            if value is None:
                return 'Null'
            return '\'' + value.replace('\'', '\\\'') + '\''
        return value

    # Get the column types of the table
    def get_col_types(self, table_name):
        self.execute_query(f'SELECT c.DATA_TYPE FROM information_schema.columns c WHERE c.TABLE_NAME=\'{table_name}\';')
        types = []
        for data_type in self.cursor:
            types.append(data_type[0])
        return types

    # Insert <=250 lines into the database
    def insert(self, table_name, lines, types):
        string = "("
        csv = reader(lines, delimiter=',', quotechar='"')
        for x, line in enumerate(csv):
            if x != 0:
                string += "),\n("
            for y, value in enumerate(line):
                if y != 0:
                    string += ', '
                if value == '':
                    value = None
                string += f"{self.check_type(types[y], value)}"
            string += ', \'Ethan Wolfe\''
        string += ")"
        self.execute_query(f'INSERT INTO {table_name} VALUES {string}')
