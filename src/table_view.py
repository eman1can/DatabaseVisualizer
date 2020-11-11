__all__ = ('TableView',)

from kivy.properties import ListProperty, BooleanProperty, ObjectProperty, StringProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from src.database import update_row, delete_row, insert_row

# Make sure that we load the style file
Builder.load_file('table_view.kv')


# The middle pane class itself
class TableView(RelativeLayout):
    connection = ObjectProperty(None)
    table_name = StringProperty(None)
    database_name = StringProperty(None)
    col_key_and_names = ListProperty(None) # column names and types
    column_names = ListProperty(None)  # just the column names
    insert = NumericProperty(0)

    def __init__(self, **kwargs):
        self._current_filters = None
        # Register events so that we can call them from the kv file
        self.register_event_type('on_toast')
        self.register_event_type('on_permission')
        super().__init__(**kwargs)

    # This is what is called to setup the searching algorithm.
    # This method just parses the string into a dictionary of filters
    def on_search(self, instance, text):
        if self.table_name is None or self.column_names is None:
            self.apply_filters()
            return
        # Don't filter on just a column_name
        if '=' not in text:
            self.apply_filters()
            return
        filters = {}
        # Split by the and argument
        if '&' in text:
            parameters = text.split('&')
        else:
            parameters = [text]
        # loop through every and argument
        for parameter in parameters:
            if '=' not in parameter:
                continue
            # This would be form an incorrect parsing. I have it here because I encountered it
            if len(parameter.split('=')) > 2:
                return
            name, value = parameter.split('=')
            if value == '':
                continue
            # read in the or filters
            filters[name] = []
            if ',' in value:
                filters[name] += value.split(',')
            else:
                filters[name] += [value]
        # Clear or apply the filters
        if filters == {}:
            self.apply_filters()
        else:
            self.apply_filters(filters)

    # a callthough function. Called by the button and passes it to the MainWindow
    def minimize_browser(self):
        self.parent.minimize_browser()

    # call through function for toast
    def show_toast(self, reason):
        self.dispatch('on_toast', reason)

    # call through function for toast
    def on_toast(self, reason):
        pass

    # call through function for warning pop up
    def get_permission(self, question, callback):
        self.dispatch('on_permission', question, callback)

    # call through function for warning pop up
    def on_permission(self, question, callback):
        pass

    # This takes the parsed filters from above and applies them to the table
    def apply_filters(self, filters=None):
        # First I make sure we don't do the same filter twice and we always filter with content, otherwise we clear the search
        if self._current_filters == filters:
            return
        self._current_filters = filters
        if filters is None:
            self.ids.grid.clear_filter()
            self.ids.delete_buttons.clear_filter()
            return
        if self.ids.grid.full_data is None:
            return
        # Loop through the data in the rows and cols, filtering by first and and then or
        data = self.ids.grid.full_data
        filtered_data = []
        cols = len(self.column_names)
        for x in range(int(len(data) / cols)):
            passes = True
            for cname, filter_list in filters.items():
                if cname.lower() in self.column_names:
                    y = self.column_names.index(cname.lower())
                    # The or filter clause
                    or_pass = False
                    for or_clause in filter_list:
                        if data[x * cols + y]['text_value'].lower().startswith(or_clause.lower()):
                            or_pass = True
                            break
                    passes &= or_pass # or → and
            if passes:
                filtered_data.append((x * cols, (x + 1) * cols))  # add the rows that pass through the filter into the data array

        # This is for turning the indexes into commands for the grid to only keep certain rows.
        # clear all currently displayed widgets so we have no duplicates
        self.ids.grid.start_filter()
        self.ids.delete_buttons.start_filter()
        # Add only the ones that passes the filter
        for start_index, end_index in filtered_data:
            self.ids.grid.filter(start_index, end_index)
            number = int(start_index / cols)
            self.ids.delete_buttons.filter(number, number + 1)

    # This is called when you click the commit button. Will detect which text inputs have been modified and update them
    def commit_changes(self):
        if self.connection is None:
            return
        data = self.ids.grid_layout.children
        if self.insert != 0:
            # before we check each child, we need to make sure we add all row inserts to the database
            if not self.commit_inserts():
                return
        # Check each child
        for child in data:
            change = child.get_commit()
            if change:
                self.update_group(child)
                child.commit_text()
        self.connection.commit()

    # This is called by the above and is what grabs the row for each child and then submits it.
    # This is one reason why my code is quite unoptimized, as I don't group by row and have to index for each row
    # every time
    def update_group(self, child):
        children = self.ids.grid_layout.children
        row = int(child.id[:child.id.index('-')])
        start_row, end_row = row * len(self.column_names), (row+1) * len(self.column_names)

        actual_children = []
        idens = {}
        cols = {}

        # Recycle Preview doesn't display all children; Only those in viewport
        # We favor displayed children over data
        for child in children:
            if int(child.id[:child.id.index('-')]) == row:
                actual_children.append(child)

        # Fill in any gaps with the data
        row_data = self.ids.grid.data[start_row: end_row]
        for x, col in enumerate(row_data):
            for child in actual_children:
                if x == int(child.id[child.id.index('-') + 1:]):
                    commit = child.get_commit()
                    if commit:
                        cols[self.column_names[x]] = child.get_commit() # cols is the list of updated string
            idens[self.column_names[x]] = col['text_value'] # idens is the filter for the where clause

        # Call the update in database
        update_row(cols, idens, self.table_name, self.database_name, self.connection)

    # This is called when you click the insert button
    # When we insert, we do so first locally, then push to the server as seen above
    def insert_row(self):
        if self.connection is None:
            return
        current_data = self.ids.grid.data
        row = []
        # When adding the new row, we want to make sure we have the right diabled/salmon attributes
        for x, col in enumerate(self.col_key_and_names):
            reference_check = col.startswith('MUL')
            disabled = col.startswith('PRI')
            row.append({'id': f"{len(self.ids.delete_buttons.data)}-{x}", 'text_value': '', 'multiline': False, 'will_disable': disabled, 'disabled': False, 'background_normal': '../res/textinput_ref_check.png' if reference_check else 'atlas://data/images/defaulttheme/textinput'})
        # Add the new row into the grid and update the delte buttons
        self.ids.grid.rows += 1
        self.ids.delete_buttons_layout.rows += 1
        self.ids.grid.data = current_data + row
        current_data = self.ids.delete_buttons.data
        self.ids.delete_buttons.data = current_data + [{'id': f"{len(current_data)}"}]

        # Keep track of how many rows are stored locally
        self.insert += 1

    # This is called when we commit the modifed children above
    def commit_inserts(self):
        # The first thing we want to do is go through the children that cound and grab their updated fields
        cols = len(self.column_names)
        current_row = len(self.ids.grid.data) - self.insert * cols
        for row in range(self.insert):
            cols_new = self.ids.grid.data[current_row+row*cols:current_row+(row+1)*cols]
            for child in self.ids.grid_layout.children:
                for y, col in enumerate(cols_new):
                    if child.id == col['id']:
                        cols_new[y]['text_value'] = child.get_commit()
                        if cols_new[y]['text_value'] == '':
                            return
            # We then want to try to inert
            # If we encoutner an error, we throw the toast
            result = insert_row(cols_new, self.table_name, self.database_name, self.connection)
            if result is not None:
                self.show_toast(result)
                return
            # if we don't throw an error, then we updated the disabled values for the childrem. We also need to make sure when inserting, that we hadn;t locked them before the person added values.
            # We do that locking here
            for child in self.ids.grid_layout.children:
                for y, col in enumerate(cols_new):
                    if child.id == col['id']:
                        child.commit_text()
                        cols_new[y]['disabled'] = child.will_disable
                        cols_new[y].pop('will_disable')
                        if child.will_disable:
                            child.disabled = True
                            child.will_disable = False
            self.insert -= 1
        return True


# This is the base class for the recycleviews that I use
class FilterableRecycleView(RecycleView):
    rows = NumericProperty(1)

    def __init__(self, **kwargs):
        self.full_data = None
        super().__init__(**kwargs)

    # the filter functions for taking the data and backing it up and then getting a filtered verions
    def start_filter(self):
        self.data = []

    def filter(self, start_index, end_index):
        if self.full_data is None:
            return
        new_data = self.data + self.full_data[start_index:end_index]
        self.data = new_data
        self.refresh_from_data()

    def clear_filter(self):
        self.data = self.full_data


# This is the delete button class. Allows us to do complex callbacks
class DeleteButton(Button):
    # This is called when you click the delete button
    def delete_record(self, index):
        table_view = self.parent.parent.parent
        recycle_data = table_view.ids.grid
        cols = len(table_view.column_names)
        values = []
        row = recycle_data.data[int(index) * cols:(int(index) + 1) * cols]
        for col in row:
            values.append(col['text_value'])
        # Grab the row that was specified, display it and ask for permission
        self.parent.parent.parent.get_permission(f'Are you sure you want to delete record  at index{index}?\n{values}', lambda value: self.real_delete(index))

    # If permission is granted, then we delete it here
    def real_delete(self, index):
        print(f'Delete at', index)
        index = int(index)
        table_view = self.parent.parent.parent

        # We need to make sure that we don't touch the database if the delete is just an insert
        just_pop=False
        recycle_data = table_view.ids.grid
        if table_view.insert > 0:
            if index >= len(recycle_data.data) - table_view.insert:
                just_pop=True

        # Either way however, we do want to remove all the associated children from the recycleviews
        recycle_delete = self.parent.parent
        cols = len(table_view.column_names)

        before = recycle_data.data[:index*cols]
        row = recycle_data.data[index*cols:(index+1)*cols]
        after = recycle_data.data[(index+1)*cols:]

        new_data = before + after
        recycle_data.data = new_data

        before = recycle_delete.data[:index]
        after = recycle_delete.data[index+1:]

        new_data = before + after
        recycle_delete.data = new_data

        # Then we remove local or call  to the database
        if just_pop:
            table_view.insert -= 1
            return

        result = delete_row(table_view.table_name, table_view.column_names, row, table_view.database_name, table_view.connection)
        if result is not None:
            table_view.show_toast(result) # show warning toast on error


# This is the fieldinput that is used in the grif
class FieldInput(TextInput):
    # We want to keep track of modifications to the text
    text_changed = BooleanProperty(False)
    text_value = StringProperty(None)
    will_disable = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # When the text changes, we want to see if it is different than what the recycleview gives us. If it is, then mark it changed
    def on_text(self, *args):
        if self.text_value != self.text:
            self.text_changed = True
        else:
            self.text_changed = False

    # Make the modified text the new text
    def commit_text(self):
        self.text_value = self.text

    # update the text value with a new text from the recycleview
    def on_text_value(self, *args):
        if self.text != self.text_value:
            self.text = self.text_value
        self.text_changed = False

    # return whether or not we are changed
    def get_commit(self):
        if self.text_value != self.text:
            return self.text
        return None

    def get_current(self):
        return self.text_value

    def __str__(self):
        return f"{self.text_value}"
