# Ethan Wolfe Lab 10

## Installation
I built lab 10 using a custom fork of kivy.
As I'm sure you know how to modify python commands, you can install these as you like.
My lab will only run on windows 10. Feel free to message me if you have any errors with the installation, although I don't expect any, or if you just want to talk with me about my code.
You can look at the official installation documentation if you need it here `https://kivy.readthedocs.io/en/master/installation/installation-windows.html`
They also do the installation with a virtual enviroment if you would rather do that so you don't clutter your workspace
1. Install the kivy dependencies
	- Both the `python` and the `python\Scripts` directories **must** be on the PATH.
	- `python -m pip install --upgrade pip wheel setuptools`
	- `python -m pip install Cython==0.29.21 docutils pygments pypiwin32 kivy_deps.sdl2 kivy_deps.glew kivy_deps.angle  kivy_deps.glew_dev kivy_deps.sdl2_dev`
	- MSVC 2019 Build tools are required 
2. Clone my fork to a folder and install it
	- `git clone https://github.com/eman1can/kivy`
		- My latest code is on master
	- `cd kivy`
	- `python -m pip install -e .`
		- This installs it as an edit in place, which is what I use to develop in Kivy
3.  I have also used the `wordcloud, sqlparse, mysql-connector-python` packages in my lab
	- `python -m pip install wordcloud sqlparse mysql-connector-python`
4. I will be submitting a .zip but I also have my code for this at https://eman1can/database_visualizer if you have any errors with the submitted zip.


Hi! I'm your first Markdown file in **StackEdit**. If you want to learn about StackEdit, you can read me. If you want to play with Markdown, you can edit me. Once you have finished with me, you can create new files by opening the **file explorer** on the left corner of the navigation bar.

# My File Structure
There are three main files inside my project
## Res
This contains all of the images that I use in my project
	
## Save
The save folder is the location that stores the Kivy configuration data after it has been written by the beginning of my program. You can largely ignore this folder unless you want to change the resolution of the window
## Src
The src folder has all of the files that make up my app itself. To run my app, just run the *database_visualizer.py* file. The other .py files are dependencies that I wrote and the .kv files are kv's rough equivalent to a javascript/css mix that makes it much easier to do the graphical styling. Classes found in browser.py will have their styling in browser.kv and so on.
#### Data
Inside the src folder, which contains all of my code files, is the data folder, in which I have placed a file *session.ini* that contains server connection information as well as my ddl file and all of the csv files.
#### Importer
I have placed my importing script and all of its dependencies in this folder, and it runs separate from my main app. To run the importer you just run the *main.py*. If you want to mess with which database it uploads to, I have almost all of the files declared as global variables so that they are easily editable. The *connector.py* file is my sql commands for the importer and the *config_parser.py* has the methods I use to parse out the csv and sql files.

## Importer - How do it work?!

For my importer, I wanted the user to have to do as  little as possible, so I wrote a parser that will read the ddl file and run it automatically, picking out any table that are made and then looking for that .csv file with the format `<table_name>_something.csv` in my data folder. If it does find a csv file, it reads it in 250 line chunks and uses callbacks to then create an insert statement and insert the values into the database. It will also get the column types as int, or varchar, rtc and then casts the read value so that it goes in properly. I used wrapper functions for my mysql-connector calls and put them in connector.

## Database browser - How do it work?!
Anytime I reference Figure x.x, it will be located in the `res/references` folder
**Figure 1.1** shows the general overview of the database browser. It is split into three main parts. The database browser itself on the left, the grid of table data in the center and the wordcloud image on the right. The three panes are split by splitters that you can drag left and right to give more or less space to a pane.
### Database Browser
When a server is put into the session.ini folder and read upon the start of the app, there will be a node for it on the tree on the left. Clicking on the right facing arrow will drop down the tree and give the databases in that server. It then goes `database → tables → table → columns`
A table node will be surrounded by a rectangular white border which indicated that it is selectable. Double tapping on it will make that tables data get loaded into the table grid. When clicking on a server, you can use the minus, plus and refresh at the top (from left to right) to either add a new server, remove the currently selected servers, which are all the ones with a downwards facing arrow, and refresh the currently open servers. Upon a refresh, the browser will re-grab the databases that are in the server. Upon removing a server, you will be asked to confirm. Clicking cancel or clicking outside of the border of the popup will cancel it. The popup can be seen in **Figure 1.2**. When adding a new server, you will be prompted to put in the connection information in another popup. This popup can be seen in **Figure 1.3**. Clicking outside the bound of the popup or clicking cancel will cancel it. Once a server is added, you will see it appear in the left pane and it will be saved to *session.ini*. The text-box next to the refresh button is the amount of lines that are loaded into the table grid. I didn't add a feature to proactively load more in a table, but you can increase to default of 100 to say 1000, and after hitting *enter* (thsi is important) that value will be saved and will take effect the next time you load a table. You cannot unload a table but for loading another table in it's place, so the easier way to reload is to load another table and then go back.
Also a part of the database browser, yet on the other end of the splitter is the arrow in the top left of the middle pane. This will hide the database browser so that you can get a better look at the table.

### Table grid
Directly below the hiding button is the commit button. This one of the most important buttons, as when you insert a row, an empty row is not pushed to the database. You have to enter information that will make it valid and then click commit for it to work. If you try to commit with an improper value, a toast will pop up with a failure message. On the far left hand side of the grid, you have the button to delete that row. It will scroll along with the grid. When going to delete, you will be prompted to confirm. Trying to delete a row that another row depends on will pop up a error toast. Looking at the grid itself, it is all text inputs and there are three variations. The disabled, which is slightly darker, and is used to denote columns that are read only. The salmon columns are foreign keys to another column/table and you would need to enter a valid number for the commit to go through. The regular column is denoted by the plain white. At the top of the grid you can see the column headers,  which contain the key designation, the name of the column as well as the datatype. You can click and drag the grid to move it. Sadly, you cannot shift scroll to more left and right. , but you can scroll up and down. 
At the very top of the grid is the search bar which allows you to filter the table. You do not have to use quotes and can search for strings and numbers equally. Entering a column_name followed by an equals and then the value you want will give you a filter. Ex: `name=Alyssa`. The filters all search proactively, so if you entered `name=Al` You would get results like Aly, Alyssa, Alaric and Alice. You can also use commas to denote an or on the same column, such as `name=Al,An`, which would come up with names such as `Alyssa, and Algerion`. You can also use *&*s to create an and clause between columns such as `name=Al,Ar&real_name=A` Which would find those with names that start with Ar or An as well as their real name starts with an A. I sadly do not have a way for searching for strings that might have a string in the middle. The likelihood that you couldn't find a row because of this is small so I ignored it.
To the right of the search bar, from left to right you have the insert, top of page and bottom of page buttons. Clicking on the insert button will add a new row to the bottom of the grid. It will not be saved until you commit, so be careful with adding more rows, or changing the search while importing data. My grid is not that sophisticated and can't keep track of that. Trying to insert a new row during a search or on a non-fully loaded array might have unpredictable results. clicking the top of page button will always bring you to the top of the page and use useful when traversing thousands of records. The save goes for the bottom of the page button.
### Word Cloud
And finally, on the last pane, we have a word cloud that is generated on the loading of the table. I had originally planned on doing graphs, but ended up feeling it would be hard to implement good looking graphs across large swaths of situations.

## Known Bugs and errors
- First off, I have not optimized this much other than the importer, so it will start to chug on the larger datasets. Just give it like 15-30 seconds and it will be fine, even though the window will be responsive. 
- When moving the window or loading different tables or other things that  may affects the size or position of the grid, it may get stuck out of place.
	- Just move the scroll around and it will fix right up
- When selecting a table to show, the tables sub-folder may get highlighted and cause the whole node to turn pink. This would take a lot of debugging to fix and isn't worth it. It's a rare error.
	- reload to fix
- There is a mostly fixed but still very rarely occurring error where clicking too fast on the database browser will cause random nodes to expand or contract
- Trying to insert a row in the middle of a search or on a non-fully loaded table may cause it to crash. This is because I use a lot of indexes, and inserting in the middle messes with how I calculate the indexes to grab the row and then submit it.
	- If I had a ton more time, I would have made the grid into more of a bunch of rows where each row is one object which would make grabbing the row content and submitting/checking them would be much easier.
- I think that's all the errors/bugs I've run into that I haven't fixed, really.