from configparser import ConfigParser
import sqlparse


class Parser:
    def __init__(self):
        self.config = None
        self.sql = None
        self._statement_index = 0

    def init_config_parser(self, filename):
        self.config = ConfigParser()
        self.config.read(filename)

    def init_sql_parser(self, filename):
        file = open(filename, 'r', encoding='utf-8')
        data = file.read()
        file.close()
        self.sql = sqlparse.split(data)

    # This will read the .ini file to return a server configuration
    def get_server(self, server_name):
        if self.config is None:
            return
        server_login = {}
        for key in self.config[server_name]:
            server_login[key] = self.config[server_name][key]
        return server_login

    # Iterator for a .sql file
    def get_statement(self):
        if self.sql is None:
            return None
        if self._statement_index == len(self.sql):
            return None
        statement = self.sql[self._statement_index]
        self._statement_index += 1
        return statement

    # This will break the file into 250 line chunks, inserting into the table every chunk
    def parse_file(self, callback, filename):
        file = open(filename, 'r', encoding='utf-8')
        file.readline()
        while True:
            lines = []
            broken = False
            for x in range(250):
                line = file.readline()[:-1]
                if line == '':
                    broken = True
                    break
                lines.append(line)
            callback(lines)
            if broken:
                break
        file.close()
        return file
