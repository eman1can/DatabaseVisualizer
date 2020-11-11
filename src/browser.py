__all__ = ('Browser',)

from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.lang import Builder
from logging import warning, info

from mysql.connector import Error
from src.database import connect_to_server, list_databases, list_tables, list_columns

# import the script file
Builder.load_file('browser.kv')


# A listItem is the node that is on the browser tree
# it is makde up of a button, a label and a gridlayout
class ListItem(RelativeLayout):
    name = StringProperty(None, allownone=True)
    selectable = BooleanProperty(False)
    selected = BooleanProperty(False)
    show_children = BooleanProperty(False)
    p_height = NumericProperty(100) # This is what allows us to have the drop menu and stay the same size

    # register events for getting smaller and largber
    def __init__(self, *args, **kwargs):
        self.register_event_type('on_expand')
        self.register_event_type('on_contract')
        super().__init__(**kwargs)

    def on_expand(self, *args):
        if len(self.ids.list.children) == 0:
            self.populate_children()

    def on_contract(self):
        pass

    # When selected, we want to make sure that we were actually touched, that we were double tapped
    # and then deselect all other children on the same level as us
    def on_select(self, instance, touch):
        touched = instance.collide_point(*touch.pos)
        if touched and not self.selected:
            if touch.is_double_tap:
                self.selected = True
                print(self, 'selected')
                self.do_select()
                for child in self.parent.children:
                    if child == self:
                        continue
                    if child.selected:
                        print(child, 'deselected')
                        child.selected = False
        return True

    def do_select(self):
        pass

    def populate_children(self):
        pass

    # call through function
    def load_table(self, *args):
        if self.parent is not None:
            self.parent.parent.load_table(*args)

    # This sets the items dynamically so we can have different kinds of trees
    def set_items(self, item_class, item_list):
        for item_args, item_dict in item_list:
            item_dict['p_height'] = self.p_height
            self.add_widget(item_class(*item_args, **item_dict))

    # We want to add the grid to use, but add other nodes to the grid
    def add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, (ListItem, ColumnListItem)):
            widget.p_height = self.p_height
            self.ids.list.add_widget(widget, index, canvas)
        else:
            super().add_widget(widget, index, canvas)

    # opposite of add
    def remove_widget(self, widget):
        if isinstance(widget, (ListItem, ColumnListItem)):
            self.ids.list.remove_widget(widget)
        else:
            super().remove_widget(widget)

    # We want to make sure that all our children use the same scale as us
    def on_p_height(self, *args):
        if 'list' not in self.ids:
            return
        try:
            for child in self.ids.list.children:
                if isinstance(child, (ListItem, ColumnListItem)):
                    child.p_height = self.p_height
        except KeyError:
            pass

    def __str__(self):
        return f'ListItem - {self.name}'


# Very similar as above, but interacts with the table_view to get it's children as DatabaseListItems specifically
class ServerListItem(ListItem):
    def __init__(self, connection, **kwargs):
        super().__init__(**kwargs)
        self.connection = connection

    def on_expand(self, *args):
        if len(self.ids.databases.ids.list.children) == 0:
            self.populate_children()

    def load_table(self, database, table):
        self.parent.parent.parent.load_table(database, table, self.connection)

    def populate_children(self):
        self.set_items(DatabaseListItem, list_databases(self.connection))

    def set_items(self, item_class, item_list):
        self.ids.databases.set_items(item_class, item_list)

    def __str__(self):
        return f'ServerListItem - {self.name}'


# Has the tables sub node and then has TaskNode children
class DatabaseListItem(ListItem):
    def __init__(self, connection, **kwargs):
        super().__init__(**kwargs)
        self.connection = connection

    def on_expand(self, sub_group=None):
        if sub_group is None:
            return
        if sub_group == 'tables':
            if len(self.ids.tables.ids.list.children) == 0:
                self.populate_tables()

    def populate_children(self):
        pass

    def load_table(self, table):
        self.parent.parent.load_table(self.name, table)

    def populate_tables(self):
        self.set_tables(TableListItem, list_tables(self.connection, self.name))

    def set_items(self, item_class, item_list):
        pass

    def set_tables(self, item_class, item_list):
        self.ids.tables.set_items(item_class, item_list)

    def __str__(self):
        return f'DatabaseListItem - {self.name}'


#  Will have Column Children and needs the database & connection for selection
class TableListItem(ListItem):
    def __init__(self, connection, database, *args, **kwargs):
        super().__init__(selectable=True, **kwargs)
        self.connection = connection
        self.database = database

    def do_select(self):
        if self.parent is not None:
            self.parent.parent.load_table(self.name)

    def populate_children(self):
        self.set_items(ColumnListItem, list_columns(self.connection, self.database, self.name))

    def __str__(self):
        return f'TableListItem - {self.name}'


# Just a label to display the column name
class ColumnListItem(RelativeLayout):
    name = StringProperty(None, allownone=True)
    p_height = NumericProperty(100)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return f'ColumnListItem - {self.name}'


# The main class for the left pain. Manages interaction between itself and other panels
class Browser(RelativeLayout):
    data = ListProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_load_table')
        self.register_event_type('on_limit')
        super().__init__(**kwargs)

    # When we are given data from the MinaWindow, we want to load each server configuration and put them on their own nodes
    def on_data(self, *args):
        if self.data is None:
            if len(self.ids.list.children) != 0:
                self.ids.list.clear_widgets()
            return
        for server in self.data:
            connection = connect_to_server(server)
            if isinstance(connection, Error):
                # When a server fails to connect, i chose to error out
                info(f'Fatal Error. \'{server["name"]}\' has an invalid configuration. Closing app.')
                quit()
            list_item = ServerListItem(connection, name=server['name'], p_height=self.height * 0.05)
            self.ids.list.add_widget(list_item)

    def load_table(self, database, table, connection):
        self.dispatch('on_load_table', database, table, connection)

    def on_load_table(self, database, table, connection):
        pass

    def on_size(self, *args):
        if self.data is None:
            return
        try:
            for child in self.ids.list.children:
                child.p_height = self.height * 0.05
        except KeyError:
            pass

    # Mostly all call throughs
    def get_connection(self, name):
        return self._connections[name]

    def set_default_limit(self, amount):
        try:
            self.dispatch('on_limit', int(amount))
        except ValueError:
            warning('Bad limit value')

    def on_limit(self, amount):
        pass

    def add_new_server(self):
        popup = NewServerPopup(browser=self)
        popup.open()

    def add_server(self, server):
        self.parent.parent.add_server(server)

    # Call the popup in the main window for deleting
    def delete_server(self):
        for server in self.ids.list.children:
            if server.ids.button.state == 'down':
                info(f'Delete {server.name}')
                self.parent.parent.get_permission(None, f"Are you sure you want to delete \'{server.name}\' permanently?", lambda value: self.remove_server(server.name))
                return

    # Close the server and remove it's node
    def remove_server(self, server_name):
        info(f'Closing {server_name}')
        for server in self.ids.list.children:
            if server.name == server_name:
                server.connection.close()
                self.ids.list.remove_widget(server)
                self.parent.parent.delete_server(server_name)
                return

    # refresh the database list
    def refresh_servers(self):
        for server in self.ids.list.children:
            for database_folder in server.ids.list.children:
                for database in database_folder.ids.list.children:
                    database.populate_tables()


# The popup for adding a new server.
class NewServerPopup(Popup):
    browser = ObjectProperty(None)

    # When we click add, get all the text valeus and call the add on the browser
    def add_server(self):
        server = {}
        server['name'] = self.ids.name_input.text
        server['host'] = self.ids.host_input.text
        server['port'] = self.ids.port_input.text
        server['user'] = self.ids.user_input.text
        server['password'] = self.ids.password_input.text
        self.browser.add_server(server)
