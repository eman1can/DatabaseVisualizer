__all__ = ('Browser',)

from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ListProperty, StringProperty, NumericProperty, ReferenceListProperty, BooleanProperty
from kivy.lang import Builder
from kivy.clock import Clock
from src.database import connect_to_server, list_databases, list_tables, list_columns

Builder.load_file('browser.kv')


class ListItem(RelativeLayout):
    name = StringProperty(None, allownone=True)
    show_children = BooleanProperty(False)
    p_height = NumericProperty(100)

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_expand')
        self.register_event_type('on_contract')
        super().__init__(**kwargs)

    def on_expand(self, *args):
        if len(self.ids.list.children) == 0:
            self.populate_children()

    def on_contract(self):
        pass

    def populate_children(self):
        pass

    def set_items(self, item_class, item_list):
        for item_args, item_dict in item_list:
            item_dict['p_height'] = self.p_height
            self.add_widget(item_class(*item_args, **item_dict))

    def add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, (ListItem, ColumnListItem)):
            widget.p_height = self.p_height
            self.ids.list.add_widget(widget, index, canvas)
        else:
            super().add_widget(widget, index, canvas)

    def remove_widget(self, widget):
        if isinstance(widget, (ListItem, ColumnListItem)):
            self.ids.list.remove_widget(widget)
        else:
            super().remove_widget(widget)

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
        return 'ListItem'


class ServerListItem(ListItem):
    def __init__(self, connection, **kwargs):
        super().__init__(**kwargs)
        self.connection = connection

    def on_expand(self, *args):
        if len(self.ids.databases.ids.list.children) == 0:
            self.populate_children()

    def populate_children(self):
        self.set_items(DatabaseListItem, list_databases(self.connection))

    def set_items(self, item_class, item_list):
        self.ids.databases.set_items(item_class, item_list)

    def __str__(self):
        return 'ServerListItem'


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

    def populate_tables(self):
        self.set_tables(TableListItem, list_tables(self.connection, self.name))

    def set_items(self, item_class, item_list):
        pass

    def set_tables(self, item_class, item_list):
        self.ids.tables.set_items(item_class, item_list)

    def __str__(self):
        return 'DatabaseListItem'


class TableListItem(ListItem):
    def __init__(self, connection, database, *args, **kwargs):
        super().__init__(**kwargs)
        self.connection = connection
        self.database = database

    def populate_children(self):
        self.set_items(ColumnListItem, list_columns(self.connection, self.database, self.name))

    def __str__(self):
        return 'TableListItem'


class ColumnListItem(RelativeLayout):
    name = StringProperty(None, allownone=True)
    p_height = NumericProperty(100)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return 'ColumnListItem'


class Browser(RelativeLayout):
    data = ListProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_data(self, *args):
        if self.data is None:
            if len(self.ids.list.children) != 0:
                self.ids.list.clear_widgets()
            return
        for server in self.data:
            connection = connect_to_server(server)
            list_item = ServerListItem(connection, name=server['name'], p_height=self.height * 0.05)
            self.ids.list.add_widget(list_item)

    def on_size(self, *args):
        if self.data is None:
            return
        try:
            for child in self.ids.list.children:
                child.p_height = self.height * 0.05
        except KeyError:
            pass

    def get_connection(self, name):
        return self._connections[name]