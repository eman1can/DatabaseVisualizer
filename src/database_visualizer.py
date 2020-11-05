from kivy.config import Config
Config.set('kivy', 'log_level', 'debug')
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.relativelayout import RelativeLayout
from os import mkdir


class MainWindow(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_data(), 0)

    def load_data(self):
        data = self.read_data()
        self.ids.browser_tab.data = data

    def read_data(self):
        try:
            file = open('data/session.ini', 'r')
        except Exception:
            return None
        servers = []
        server = {}
        for line in file:
            line = line.strip()
            if line == '' or line == '\n':
                continue
            print('\'' + line + '\'')
            if '[' in line and ']' in line:
                if len(server) != 0:
                    servers.append(server)
                    server = {}
                server['name'] = line[1:-1]
                continue
            parts = line.split('=')
            server[parts[0]] = parts[1]
        if len(server) != 0:
            servers.append(server)
        file.close()
        return servers

    def write_data(self, data):
        try:
            file = open('data/session.ini', 'w')
        except Exception:
            # No save data; Create save data file
            mkdir('data')
            file = open('data/session.ini', 'w')
        file.write(data)
        file.close()


class DatabaseVisualizerApp(App):
    def build(self):
        self.title = 'Database Visualizer'
        return MainWindow()


if __name__ == "__main__":
    DatabaseVisualizerApp().run()
