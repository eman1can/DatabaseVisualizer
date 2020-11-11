
# Set the window size on a new computer and make launch the readme if at the first launch.
from win32api import GetSystemMetrics
from os import environ, startfile, getcwd
environ['KIVY_HOME'] = '../save'
from kivy.config import Config
first_open = Config.get('kivy', 'first_open')
from logging import info
if first_open == 'True':
    info('Detected first opening. Launching readme.md')
    path = getcwd()
    startfile(path + '/../README.md')
    Config.set('graphics', 'width', int(GetSystemMetrics(0) * 2 / 3))
    Config.set('graphics', 'height', int(GetSystemMetrics(1) * 2 / 3))
    Config.set('kivy', 'first_open', False)
    Config.write()

# Regular imports
from io import BytesIO
from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from src.database import get_table, use, get_columns
from kivy.core.image import Image as CoreImage
from wordcloud import WordCloud


# To hook into styling; Look in .kv
class PermissionPopup(Popup):
    pass


# The main window object
# Controls interaction between the three main panes
class MainWindow(RelativeLayout):
    limit = NumericProperty(100)
    browser_minimized = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.connections = {}
        super().__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.load_data(), 0)

    # This is called after the constructor above finished executing
    def load_data(self):
        data = self.read_data()
        self.ids.browser_tab.data = data

    # Set the limit on the number of lines to load
    def set_limit(self, instance, limit):
        self.limit = limit

    # Make the warning toast fade into existance using Kivy Animations
    def show_toast(self, instance, reason):
        self.ids.toast.text = reason
        anim = Animation(opacity=1, duration=0.25)
        anim.start(self.ids.toast)
        Clock.schedule_once(self.fade_toast, 1.75)

    # Make the toast fade back into obscurity
    def fade_toast(self, dt):
        anim = Animation(opacity=0, duration=0.75)
        anim.start(self.ids.toast)

    # Launch the popup to ask if you really want to delete
    def get_permission(self, instance, question, callback):
        popup = PermissionPopup(size_hint=(0.75, 0.75))
        popup.ids.label.text = question
        popup.ids.confirm.bind(on_release=callback)
        popup.open()

    # Swap wether the browser pane is minimized
    def minimize_browser(self):
        self.browser_minimized = not self.browser_minimized

    # Read in the servers from the session ini
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

    # Add a server to the ini at the end from the input from the popup
    def add_server(self, server):
        # make sure we aren't adding a duplicate
        current_servers = self.read_data()
        for s in current_servers:
            if s['name'] == server['name']:
                return
        # Open the file
        try:
            file = open('data/session.ini', 'a')
        except Exception:
            return None
        # Write our new data
        file.write(f'[{server["name"]}]\n')
        file.write(f'host={server["host"]}\n')
        file.write(f'port={server["port"]}\n')
        file.write(f'user={server["user"]}\n')
        file.write(f'password={server["password"]}\n')
        file.close()

    # Delete a server from the ini file, cutting it out if it is in the middle
    def delete_server(self, server_name):
        # Make sure that it even exists in the file (it will 99.99% of the time)
        current_servers = self.read_data()
        for s in current_servers:
            if s['name'] == server_name:
                # Open the file
                try:
                    file = open('data/session.ini', 'r')
                except Exception:
                    return None
                # Read until we hit to the server we want to cut
                lines = []
                line = file.readline()
                while line != f"[{server_name}]\n":
                    lines.append(line)
                    line = file.readline()
                # Throw away the liens that contain the deleted server
                while line is not None and line != '' or line.startswith('['):
                    line = file.readline()
                # read the rest of the file
                while line != '' and line is not None:
                    line = file.readline()
                file.close()

                # Write the now cut data back to the file.
                # I realize there's probably an easier way to do this.
                try:
                    file = open('data/session.ini', 'w')
                except Exception:
                    return None
                for line in lines:
                    file.write(line)
                file.close()
                return

    # This is called when you select a node and will liad the table into the grid
    def load_table(self, instance, database, table, connection):
        # First, get our setup and then grab the table data itself
        use(connection, database)
        col_names = get_columns(connection, database, table)
        data = get_table(connection, table, self.limit)

        # Setup our table view grid size and values based on what we just loaded
        self.ids.table_view.connection = connection
        self.ids.table_view.table_name = table
        self.ids.table_view.database_name = database
        self.ids.table_view.ids.grid.rows = len(data)
        self.ids.table_view.ids.grid_layout.cols = len(col_names)
        self.ids.table_view.ids.delete_buttons_layout.rows = len(data)
        self.ids.table_view.ids.grid_headers_layout.cols = len(col_names)

        # Parse the column name and types into the names, whether or not we want to be able to edit and the full names
        grid_header_data = []
        grid_data = []
        max = 100
        actual_col_names = []
        disabled = []
        reference_check = []
        for col in col_names:
            disabled.append(col.startswith('PRI'))
            reference_check.append(col.startswith('MUL'))
            grid_header_data.append({'text': col, 'disabled': True})
            if 10 * len(col) > max:
                max = 10 * len(col)
            findex = col.index('-') + 1
            actual_col_names.append(col[findex:col.index('-', findex)].strip().lower())
        # Make sure that our text will fit in the boxes on the grid
        self.ids.table_view.ids.grid_layout.default_size = max, 50
        self.ids.table_view.ids.grid_headers_layout.default_size = max, 50

        # loop through every row and column, making the delete button and the textinput
        comment_words = ''
        delete_buttons = []
        for x, row in enumerate(data):
            for y, col in enumerate(row):
                comment_words += ' ' + str(col).lower() + ' '
                grid_data.append({'id': f"{x}-{y}", 'text_value': str(col), 'multiline': False, 'disabled': disabled[y], 'background_normal': '../res/textinput_ref_check.png' if reference_check[y] else 'atlas://data/images/defaulttheme/textinput'})
            delete_buttons.append({'id': f"{x}"})

        # Assign all that data we jsut made to the table_view and the grid and it's alyout
        self.ids.table_view.column_names = actual_col_names
        self.ids.table_view.col_key_and_names = col_names
        self.ids.table_view.ids.grid_headers.data = grid_header_data
        self.ids.table_view.ids.grid.data = grid_data
        self.ids.table_view.ids.grid.full_data = grid_data
        self.ids.table_view.ids.delete_buttons.data = delete_buttons
        self.ids.table_view.ids.delete_buttons.full_data = delete_buttons

        # Make sure that we have a couple words
        # Avoid any errors there
        if len(comment_words) > 10:
            # Create a cool word cloud of the whole table that is shown
            # This is just saving the image to a buffer and loading it with the kivy image loader
            wordcloud = WordCloud().generate(comment_words)
            pil_image = wordcloud.to_image()
            data = BytesIO()
            pil_image.save(data, format='png')
            data.seek(0)
            im = CoreImage(BytesIO(data.read()), ext='png')
            # assign the texture of the cloud to the image on the right pane
            self.ids.word_cloud.texture = im.texture


# The code below is what actually launches the app
class DatabaseVisualizerApp(App):
    def build(self):
        self.title = 'Database Visualizer'
        return MainWindow()


if __name__ == "__main__":
    DatabaseVisualizerApp().run()
