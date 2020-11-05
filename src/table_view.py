__all__ = ('TableView',)

from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder

Builder.load_file('table_view.kv')


class TableView(RelativeLayout):
    pass
