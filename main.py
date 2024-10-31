# Version 6
# Switch Autosave
import argparse
import csv
import logging
import os
import sys
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, Menu, ttk
from tkinter.filedialog import askopenfile

import colorama
import pandas as pd
import tktooltip  # https://github.com/gnikit/tkinter-tooltip
from PIL import Image, ImageTk
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # , NavigationToolbar2Tk
from pycoingecko import CoinGeckoAPI

from src.db import Db
from src.format import color_logging

cg = CoinGeckoAPI()

'''Date:  23-01-2022, 22:32:33
{'bitcoin': {'usd': 35365}, 'polkadot': {'usd': 18.19}, 'near': {'usd': 11.12}, 'ethereum': {'usd': 2423.13}, 'ergo': {'usd': 3.13}}
The current price of Ergo:  35365
'''

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.pyplot").setLevel(logging.WARNING)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.category").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    console = color_logging(level=logging.DEBUG)
    logging.basicConfig(
        level=logging.DEBUG,
        force=True,
        handlers=[console],
    )  # Force is needed here to re config logging
    # Init should be here so as the colors be rendered properly in fly.io
    colorama.init(convert=True)


class Coin:
    """ A class containing coins"""
    thecoins = []

    def __init__(self, name):
        self.name = name.strip()
        if name != '':
            if name not in Coin.thecoins:  # So as not to be added twice
                Coin.thecoins.append(self.name)
                sorted(Coin.thecoins)
        # TODO make a self.symbol in a dictionary i.e. {Bitcoin: btc}

    @staticmethod
    def delete_coin(coin=None):
        if coin:
            Coin.thecoins.remove(coin)
            logger.debug(f"Coin()>delete_coin>>> '{coin}' was successfully deleted from the list.")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Persistent:
    """A class to store and retrieve a list of preferable coins"""

    @staticmethod
    def retrieve():
        """Retrieves the names from saved coins"""
        with Db() as database:
            coins = database.retrieve_coins()
            logger.debug(f"{coins=}")
            for coin in coins:
                Coin(name=coin[0])

    @staticmethod
    def store():
        """Stores the name of the coins to the db"""
        with Db() as database:
            for coin in Coin.thecoins:
                database.add_coins(coin=coin)
            logger.debug(f"Coins saved")

    @staticmethod
    def read_from_file():
        try:
            file = askopenfile(mode='r', filetypes=[('CSV files', 'csv')])
            if file is not None:
                reader = csv.reader(file, delimiter=';', quoting=csv.QUOTE_ALL)
                for row in reader:
                    Coin(row[0])
                logger.debug(f'{file.name} retrieved')
        except FileNotFoundError as err:
            logger.exception(f"Persistent>read_from_file> Error in finding saved list of coins: {err}")
        except Exception:
            logger.exception(msg="Error in reading from file")


class Mainpage:
    """ Main page"""

    def __init__(self, note, name, controller):
        self.secondpage = Secondpage
        self.note = note
        self.name = name
        self.controller = controller
        self.frame = ttk.Frame(self.note)
        self.frame.pack(expand=True, fill='both', padx=1, pady=1)
        # self.label = tk.Label(self.frame, text='', font='Arial 16')
        # self.label.pack(expand=True, fill='both', padx=1, pady=1)
        self.note.add(self.frame, text=name)
        # self.label.bind('<3>', self.controller.post_menu)  # Posts the Main Menu from App through this bind,
        # but only at the label!
        self.f1 = ttk.LabelFrame(self.frame, text='Add a coin')
        self.f1.pack(expand=True, fill='both', padx=1, pady=1)
        self.f1.bind('<3>', self.controller.post_menu)  # Posts the Main Menu from App through this bind,
        self.coin_entry()

    def __repr__(self):
        return self.name

    def coin_entry(self):
        """Press enter to add the coin you typed"""
        global text
        global text_var
        global entry
        text_var = tk.StringVar()
        entry = tk.Entry(self.f1, textvariable=text_var, font='Arial 14', width=12, bg='white',
                         fg='blue')

        entry.pack(expand=0)
        # entry.place(x=10, y=30)
        # entry.anchor('center')
        text_var.set("Add a coin")
        entry.bind(
            "<KeyRelease-Return>",
            lambda e: Mainpage.coin_call(self, controller=self.controller)
        )  # Without parentheses! https://www.tcl.tk/man/tcl8.4/TkCmd/keysyms.html
        entry.bind("<KeyRelease-Return>", lambda e: entry.delete(0, 'end'), add=True)
        entry.focus()
        # Delete the message from the entry box when a key is pressed
        entry.bind("<ButtonPress-1>", lambda e: text_var.set(""))

    def coin_call(self, controller):
        """Add the coin to the current coin list"""
        self.controller = controller
        # get() must be here. Otherwise, it gets nothing, as text_var is empty. Strip so as not to include " ".
        text = text_var.get().strip()
        if text not in Coin.thecoins:
            if text != '':  # To exclude the empty entry to be added
                Coin(text)
                self.controller.get_page_2(
                    'Secondpage')  # https://stackoverflow.com/questions/65181993/attributeerror-event-object-has-no-attribute-show-frame-in-tkinter

                logger.debug('The new list: ', Coin.thecoins)
                logger.debug(f'The coin "{text}" was added successfully')
        elif text in Coin.thecoins:
            return messagebox.showinfo('Message', f' Coin named "{text}" already exists.')


class Secondpage:
    """Coin list page"""
    retrieved_coins = []  # A list which contains the retrieved coins + their prices after the search in the search box
    values = []  # A list with the values for the Treeview
    header = ('Coin', 'Price')  # The names of the columns of the Tree
    search_tree = []  # A list which contains the searched coins without their prices

    @staticmethod
    def retrieve_coin_list_prices(term=''):
        '''Searches the dictionary and
        retrieves the searched coin list based on the term provided.
        If term=coin, retrieves only these coins.
        If term = None, it retrieves all the saved coins'''
        print(f'>retrieve_coin_list_prices() called with term: {term}')
        if term:
            if len(Secondpage.retrieved_coins) != 0:
                Secondpage.retrieved_coins.clear()
            for coin, prices in Coin_prices.thecoins_prices.items():
                if term:
                    if term.lower() in coin.lower():
                        pair = (str(coin), str(prices))
                        Secondpage.retrieved_coins.append(pair)
            Secondpage.retrieved_coins = sorted(Secondpage.retrieved_coins)
            logger.debug(f'The searched coins based on term: "{term}"  provided were successfully retrieved:'
                         f'Secondpage.retrieved_coins: {Secondpage.retrieved_coins}')
        else:
            if len(Secondpage.retrieved_coins) != 0:
                Secondpage.retrieved_coins.clear()
            for coin, prices in Coin_prices.thecoins_prices.items():
                pair = (str(coin), str(prices))
                Secondpage.retrieved_coins.append(pair)
            Secondpage.retrieved_coins = sorted(Secondpage.retrieved_coins)
            logger.debug(f'The coins were successfully retrieved:'
                         f'Secondpage.retrieved_coins: {Secondpage.retrieved_coins}')

    def __init__(self, note, name, controller):
        self.figure_toplevel = None
        self.canvas = None
        self.fig_frame = None
        self.figure = None
        self.secondpage = self
        self.note = note
        self.name = name
        self.controller = controller
        self.coins = Coin.thecoins
        self.tree = None
        self.frame = ttk.Frame(self.note)
        self.frame.pack(expand=True, fill='both', padx=1, pady=1)
        self.note.add(self.frame, text=name)
        self.topframe = ttk.Frame(self.frame)
        self.topframe.pack(side='top', expand=False, fill='both')
        # Search box
        self.left_label = ttk.Frame(self.topframe)
        self.left_label.pack(side='left', expand=True, fill='both')
        self.right_label = ttk.Frame(self.topframe)
        self.right_label.pack(side='left', expand=True, fill='both')
        self.f0 = ttk.LabelFrame(self.left_label, text='Search')
        self.f0.pack(side='right', expand=False, fill='both', padx=120)  # ,padx=App.x * 0.2, pady=15, padx=App.x*0.3
        self.text_var = tk.StringVar()
        self.search = tk.Entry(self.f0, textvariable=self.text_var, font='Arial 15', width=20)
        # self.search = customtkinter.CTkEntry(self.f0, textvariable=self.text_var, width=120,
        #                                     placeholder_text="Type a coin's name")
        # self.search1 = Entry_.Entry(self.f0, textvariable=self.text_var, font='Arial 15', width=20, placeholder_text='aok')
        self.search.pack(expand=False, side='left')
        # self.search1.pack(expand=False, side='left')
        # self.f0.place(relx=0.2)  # Proportionally to the y (width) of the whole App
        # Frame to the right
        self.insertframe = ttk.LabelFrame(self.right_label, text='Insert coins')
        self.insertframe.pack(side='left', expand=False, fill='both', padx=120)  # , pady=15 , padx=App.x*0.3
        # Coin entry
        self.text_coin = tk.StringVar()
        self.coin_entrybox = tk.Entry(self.insertframe, textvariable=self.text_coin, font='Arial 15', width=20)
        self.coin_entrybox.pack(side='right', expand=False)
        self.coin_entrybox.bind("<KeyRelease-Return>", lambda e: self.insert_coin(
            controller=self.controller))  # Without parentheses! https://www.tcl.tk/man/tcl8.4/TkCmd/keysyms.html
        self.coin_entrybox.bind("<KeyRelease-Return>", lambda e: self.coin_entrybox.delete(0, 'end'), add=True)
        self.coin_entrybox.focus()
        # Bind the self.search to self.search_handler
        self.search.bind('<KeyRelease>', self.search_handler)
        # Coins in a Listbox
        self.f1 = ttk.LabelFrame(self.frame, text='Coin list')
        self.f1.pack(side='top', expand=True, fill='both', padx=2, pady=2)
        # Emerging Menu for Secondpage
        self.context = Menu(font='Arial 12',
                            tearoff=0)  # Tearoff has to be 0, in order the command to start being posted
        # in position 0 of the menu.
        # self.root.config(menu=self.context) # if this is enabled, the menu will appear in the top left of the window
        self.context.add_command(label='Modify', command=self.modify)
        self.context.add_command(label='Delete', command=self.delete)
        self.contextsubmenu = Menu(font='Arial 12', tearoff=0)
        self.context.add_cascade(label='Charts', menu=self.contextsubmenu)
        self.contextsubmenu_usd = Menu(font='Arial 12', tearoff=0)
        self.contextsubmenu_eur = Menu(font='Arial 12', tearoff=0)
        self.contextsubmenu.add_cascade(label='Usd', menu=self.contextsubmenu_usd)
        self.contextsubmenu.add_cascade(label='Euro', menu=self.contextsubmenu_eur)
        self.contextsubmenu_usd.add_command(label='Previous 1 day', command=lambda: self.get_charts(days=1))
        self.contextsubmenu_usd.add_command(label='Previous 7 days', command=lambda: self.get_charts(days=7))
        self.contextsubmenu_usd.add_command(label='Previous 90 days', command=lambda: self.get_charts(days=90))
        self.contextsubmenu_usd.add_command(label='Previous 360 days', command=lambda: self.get_charts(days=360))
        self.contextsubmenu_usd.add_command(label='Since inception', command=lambda: self.get_charts(days='max'))
        self.contextsubmenu_usd.add_command(label='Custom days', command=lambda: self.custom_days(coin='usd'))
        self.contextsubmenu_eur.add_command(label='Previous 1 day', command=lambda: self.get_charts(days=1, coin='eur'))
        self.contextsubmenu_eur.add_command(label='Previous 7 days',
                                            command=lambda: self.get_charts(days=7, coin='eur'))
        self.contextsubmenu_eur.add_command(label='Previous 90 days',
                                            command=lambda: self.get_charts(days=90, coin='eur'))
        self.contextsubmenu_eur.add_command(label='Previous 360 days',
                                            command=lambda: self.get_charts(days=360, coin='eur'))
        self.contextsubmenu_eur.add_command(label='Since inception',
                                            command=lambda: self.get_charts(days='max', coin='eur'))
        self.contextsubmenu_eur.add_command(label='Custom days', command=lambda: self.custom_days(coin='eur'))
        # Tree
        self.tree = ttk.Treeview(self.f1, columns=Secondpage.header, show='headings')
        self.setup_tree()
        # Call the fill_box to fill the coin list
        self.fill_box()

    def setup_tree(self):
        # Fill the tree
        for head in Secondpage.header:
            self.tree.heading(column=head, text=f'{head}', command=lambda c=head: sortby(self.tree, c, 0))
            if head == 'Coin':
                self.tree.column(column=head, width=100)
        # Clear the list because otherwise it will contain duplicates
        Secondpage.values = []
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.pack(expand=True, fill='both')
        self.tree.bind('<ButtonRelease-3>', self.post_menu)  # Menu is posted only in the tree!

    def search_handler(self, event):
        print('>>>>Secondpage search handler is called')
        self.search.focus_set()
        self.display_with_term()

    def insert_coin_handler(self, event):
        print('>>>Secondpage insert coin handler is called')
        self.insert_coin(controller=self.controller)

    def insert_coin(self, controller):
        """Add the coin to the current coin list"""
        self.controller = controller
        # get() must be here. Otherwise, it gets nothing, as text_var is empty. Strip so as not to include " ".
        temp_text = self.text_coin.get().strip()
        if temp_text not in Coin.thecoins:
            if temp_text != '':  # To exclude the empty entry to be added
                Coin(temp_text)
                self.fill_box()  # https://stackoverflow.com/questions/65181993/attributeerror-event-object-has-no-attribute-show-frame-in-tkinter
                if autosave.get() is True:
                    self.controller.persistent.store()

                logger.debug('Secondpage>insert_coin>The new list: ', Coin.thecoins)
                logger.debug(f'Secondpage>insert_coin>The coin "{temp_text}" was added successfully')
        elif temp_text in Coin.thecoins:
            return messagebox.showinfo('Message', f' Coin named "{temp_text}" already exists.')

    def display_with_term(self):
        """Gets the search term"""
        term = self.text_var.get().strip()
        item_child = ''
        current_price_from_first_displayed_coin = ""
        # Pick the second value from the key 'values' from the dictionary self.tree.item(current)
        print(f'Secondpage>display_with_term(self) called with term: {term}')
        try:
            # TODO: When the search term doesn't correspond to the tree, keep the variable which was searched, so as
            # TODO: the tree not to be emptied
            # If the tree is totally empty, it will be filled with the coin list
            if len(self.tree.get_children()) == 0:
                # If no prices are fetched
                if len(Coin_prices.thecoins_prices) == 0:
                    print("Secondpage>display_with_term(self)>> Coin_prices.thecoins_prices is empty,Tree was empty:"
                          'calling self.retrieve_coin_list() & self.fill_box()')
                    self.retrieve_coin_list()
                    self.fill_box()
                # Prices exist
                else:
                    print(
                        'Secondpage>display_with_term(self)   Tree is empty, Coin_prices.thecoins_prices is NOT empty:'
                        'calling retrieve_coin_list_prices() & fill_box_with_prices(retrieve=False)')
                    self.retrieve_coin_list_prices()
                    self.fill_box_with_prices(retrieve=False)
            if len(self.tree.get_children()) != 0:
                item_child = self.tree.get_children()
                print(f'Secondpage>display_with_term(self)  item_child: {item_child}')
                current_price_from_first_displayed_coin = self.tree.item(item_child[0])['values'][1]  # Get the price
                # A tree without prices
                if current_price_from_first_displayed_coin == "":
                    print('Secondpage>display_with_term(self) #Empty prices')
                    print(
                        f'Secondpage>display_with_term(self) current_price_from_first_displayed_coin: {current_price_from_first_displayed_coin}')
                    self.retrieve_coin_list(term)
                    self.fill_box_after_search()
                # The tree contains the prices
                elif current_price_from_first_displayed_coin != "":
                    print('Secondpage>display_with_term(self) ##Something')
                    print(
                        f'Secondpage>display_with_term(self) current_price_from_first_displayed_coin: {current_price_from_first_displayed_coin}')
                    self.retrieve_coin_list_prices(term)
                    self.fill_box_with_prices(retrieve=True)
        except:
            raise

    def retrieve_coin_list(self, term=''):
        """Retrieve the searched coin list in Secondpage.search_tree based on the term provided.
        If term=coin, retrieves only these coins.
        If term = None, it retrieves all the saved coins"""
        logger.debug(f'Secondpage>retrieve_coin_list called with "{term}"')
        if term:
            logger.debug(f'Term : {term}')
            if len(self.search_tree) != 0:
                Secondpage.search_tree.clear()
            # Search through the tuples
            for tuple_coin in Secondpage.values:
                if term:
                    for item in tuple_coin:
                        if term.lower() in item.lower():
                            if tuple_coin not in Secondpage.search_tree:
                                Secondpage.search_tree.append(tuple_coin)
            logger.debug(f'The searched coins in Secondpage treeview '
                         f'based on term provided were successfully retrieved {Secondpage.search_tree}')
        # If term=''
        elif term == "":
            if len(Secondpage.search_tree) != 0:
                Secondpage.search_tree.clear()
            for tuple_coin in Secondpage.values:
                Secondpage.search_tree.append(tuple_coin)
        logger.debug('Secondpage>retrieve_coin_list>Search list for the treeview:', Secondpage.search_tree)

    def fill_box_after_search(self):
        """Fills the listbox with coins from Secondpage.search_tree"""
        # Clear the treeview
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
        except BaseException as err:
            raise err
        # Fill the treeview based on the typed entry
        try:
            if len(Secondpage.search_tree) != 0:
                for number, coin in enumerate(Secondpage.search_tree):
                    self.tree.insert("", tk.END, iid=str(number), values=coin)
            logger.debug(
                'Secondpage>fill_box_after_search(self): Search was successful: '
                'The results are now shown in Treeview'
            )
        except BaseException as err:
            raise err
            # print('Warning: Loading the searched Secondpage coin list failed!')

    def post_menu(self, event):
        self.context.post(event.x_root, event.y_root)
        logger.debug("Secondpage>post_menu>Emerging Menu from Secondage via right click is now visible")

    def modify(self):
        """Inserts the selected ID from the coin in the Coin class """
        #  Solution: https://stackoverflow.com/questions/30614279/tkinter-treeview-get-selected-item-values
        current = self.tree.focus()
        logger.debug(f'The selected row: {self.tree.item(current)}')
        # Pick the first value from the key 'values' from the dictionary self.tree.item(current)
        current_id_from_coin = self.tree.item(current)['values'][0]
        logger.debug(f'Selected coin: {current_id_from_coin}')
        # Add the coin to Coin class
        CoinWindow(controller=self.controller, operation='modify', coin=current_id_from_coin)

    def delete(self):
        """Inserts the selected ID from the coin in the Coin class """
        #  Solution: https://stackoverflow.com/questions/30614279/tkinter-treeview-get-selected-item-values
        current = self.tree.focus()
        logger.debug(f'The selected row: {self.tree.item(current)}')
        # Pick the first value from the key 'values' from the dictionary self.tree.item(current)
        current_id_from_coin = self.tree.item(current)['values'][0]
        logger.debug(f'Selected coin: {current_id_from_coin}')
        # Add the coin to Coin class
        CoinWindow(controller=self.controller, operation='delete', coin=current_id_from_coin)
        self.fill_box()  # Fill the Tree after deleting

    def search_handler_only_saved(self, event):
        """Called from entry in the search box"""
        self.display_with_term_only_saved()

    def display_with_term_only_saved(self):
        """Gets the search term, passes it to retrieve_coin_list_prices and then fills the tree"""
        print(">>>Secondpage: display_with_term_only_saved() is called")
        term = self.search.get().strip()
        self.retrieve_coin_list_prices(term)
        self.fill_box_after_search()

    def fill_box(self):
        """Fills the treeview with coins from Coin.thecoins"""
        # Clear the treeview
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            print('Secondpage>fill_box> Tree was erased')
        except Exception as err:
            print(f'Secondpage>fill_box>Error in deleting the Secondpage Tree {err}')
        try:
            # Create tuples for every coin with the name of the coin and an empty string (we don't know the price yet)
            Secondpage.values.clear()  # To be sure that the list is empty
            for coin in Coin.thecoins:
                Secondpage.values.append((coin, ''))
            coin_list_len = [font.measure(d[0]) for d in Secondpage.values]
            print(f'Secondpage>fill_box> Lengths of the coins: {coin_list_len}')
            self.tree.column(column='Coin', width=max(coin_list_len) + 5, stretch=False)  # Don't stretch
            for number, value in enumerate(Secondpage.values):
                self.tree.insert("", tk.END, iid=str(number), values=value)
            logger.debug(f'Secondpage>fill_box> Treeview was filled {Secondpage.values}')
        except Exception as err:
            print(f'Secondpage>fill_box> Loading the coin list failed! {err}')

    def fill_box_with_prices(self, retrieve=False):
        """Fill Secondpage treeview with the coin and their corresponding prices"""
        # Clear the treeview
        print(f'fill_box_with_prices(self, retrieve=False) was called with retrieve = {retrieve}')
        try:
            if len(Coin_prices.thecoins_prices) != 0:  # Do not delete the items if there are not any coins with prices
                for item in self.tree.get_children():
                    self.tree.delete(item)
                print('Secondpage>fill_box_with_prices>  Tree was erased')
        except Exception as err:
            print(f'Secondpage>fill_box_with_prices>  Error in deleting the Secondpage Tree {err}')
        try:
            if not retrieve:
                logger.debug(
                    f"Coin_prices.thecoins_prices: {Coin_prices.thecoins_prices} "
                    f"{len(Coin_prices.thecoins_prices)}"
                )

                if len(Coin_prices.thecoins_prices) != 0:
                    for i, coin in enumerate(Coin_prices.thecoins_prices):
                        self.tree.insert("", tk.END, iid=str(i), values=[coin, Coin_prices.thecoins_prices[coin]])
                else:
                    print(f"Secondpage>fill_box_with_prices> Coin_prices.thecoins_prices is empty")
            elif retrieve:
                logger.debug(
                    f"Secondpage>fill_box_with_prices> Secondpage.retrieved_coins: {Secondpage.retrieved_coins}")
                if len(Secondpage.retrieved_coins) != 0:
                    for i, tuple_coin in enumerate(Secondpage.retrieved_coins):
                        self.tree.insert("", tk.END, iid=str(i), values=[tuple_coin[0], tuple_coin[1]])
                else:
                    print(f"Secondpage>fill_box_with_prices> Coin_prices.thecoins_prices is empty")
        except Exception as err:
            print(f'Secondpage>fill_box_with_prices> '
                  f'Warning: Loading the searched coin list and their prices has failed! {err}')

    def get_charts(self, coin='usd', days=str(90)):
        """Draws a plot containing price, marketcap and total volumes for the previous 90 days.
           if days>90, coingecko sends data in days. If <90 data intervals are smaller."""
        # Destroy the toplevel, so as not to be overlapped by a previous one.
        if self.figure_toplevel or self.fig_frame or self.canvas is not None:
            self.figure_toplevel.destroy()
            self.fig_frame.destroy()
            self.canvas.get_tk_widget().destroy()
            print(f'Secondpage.get_charts: {self.figure_toplevel} destroyed')
            print(f'Secondpage.get_charts: {self.fig_frame} destroyed')
            print(f'Secondpage.get_charts: {self.canvas} destroyed')
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        # Clears the figure, so as not to be overlapped by a previous one.
        if self.figure is not None:
            self.figure.clf()
        current = self.tree.focus()
        self.figure_toplevel = tk.Toplevel()
        self.figure_toplevel.protocol("WM_DELETE_WINDOW", lambda: AskQuit(self.figure_toplevel))
        self.fig_frame = ttk.Frame(self.figure_toplevel)
        self.fig_frame.pack(expand=True, fill='both')

        logger.debug(f'The selected row: {self.tree.item(current)}')
        # Pick the first value from the key 'values' from the dictionary self.tree.item(current)
        current_id_from_coin = self.tree.item(current)['values'][0]
        logger.debug(f'Selected coin: {current_id_from_coin}')
        data = cg.get_coin_market_chart_by_id(id=f'{current_id_from_coin}', vs_currency=f'{coin}', days=f'{days}')
        if coin == 'eur':  # Replace eur with the name euro for a proper representation of the coin
            coin = 'euro'
        # Coingecko returns the data to UNIX timestamp in milliseconds
        for timestamp in data['prices']:
            if timestamp != 0:
                if days == 'max':
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')  # %H:%M:%S
                elif int(days) < 91:
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d  %H:%M')
                else:
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')
        for timestamp in data['market_caps']:
            if timestamp != 0:
                if days == 'max':
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')  # %H:%M:%S
                elif int(days) < 91:
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d  %H:%M')
                else:
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')
            if timestamp[1] not in (0, "", None):
                timestamp[1] = timestamp[1] / 1000000
        for timestamp in data['total_volumes']:
            if timestamp != 0:
                if days == 'max':
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')  # %H:%M:%S
                elif int(days) < 91:
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d  %H:%M')
                else:
                    timestamp[0] = datetime.fromtimestamp(timestamp[0] / 1000).strftime('%Y-%m-%d')
            if timestamp[1] not in (0, "", None):
                timestamp[1] = timestamp[1] / 1000000
        df = pd.DataFrame(data['prices'], columns=['Timestamp', 'Price', ])
        df2 = pd.DataFrame(data['market_caps'], columns=['Timestamp', 'Marketcap'])
        df3 = pd.DataFrame(data['total_volumes'], columns=['Timestamp', 'Total volumes'])

        # Merge the dataframes and insert them into the db
        database = Db()
        df_ = pd.DataFrame({"name": [f"{current_id_from_coin}" for i in range(0, len(df.index))]})
        df_total = df.copy()
        df_total = df_.join(df_total)
        # logger.debug(f"{df_total=}")
        df_total = df_total.merge(df2, how="left", on="Timestamp")
        df_total = df_total.merge(df3, how="left", on="Timestamp")
        # logger.debug(f"{df_total=}")
        database.insert_coin_values(df=df_total, coin=current_id_from_coin)

        self.figure = plt.figure(1, figsize=(15, 15), dpi=100)
        ax1 = self.figure.add_subplot(211)
        # Max first, because int('Max') is invalid and will raise an error.
        if days == 'max':
            ax1.set_title(f'{current_id_from_coin.capitalize()} metrics since inception')
        elif int(days) < 2:
            ax1.set_title(f'{current_id_from_coin.capitalize()} metrics for {days} day')
        elif days != 'max':
            ax1.set_title(f'{current_id_from_coin.capitalize()} metrics for {days} days')
        else:
            ax1.set_title(f'{current_id_from_coin.capitalize()} metrics for {days} days')
        ax1.set_ylabel(f'{coin.capitalize()}')
        plt.plot(df["Timestamp"], df["Price"], label='Price', color='blue')
        plt.xticks('')
        # Legend instructions: https://matplotlib.org/3.5.0/api/_as_gen/matplotlib.pyplot.legend.html
        ax1.legend(loc=2)
        ax3 = ax1.twinx()
        ax3.set_ylabel(f'Per million {coin.capitalize()}')
        ax3.plot(df3['Timestamp'], df3['Total volumes'], label='Total volumes',
                 color='red')  # 2nd line in the first subplot
        plt.legend(loc=1)
        ax2 = self.figure.add_subplot(212)
        ax2.plot(df2["Timestamp"], df2["Marketcap"])
        ax2.set_title('Marketcap')
        ax2.set_ylabel(f'Per million {coin.capitalize()}')
        if days == 'max':
            ax2.set_xticks(df["Timestamp"][::180])  # Every semester
        elif int(days) == 360:
            ax2.set_xticks(df["Timestamp"][::30])  # Every 30 days
        elif 2 > int(days):
            ax2.set_xticks(df["Timestamp"][::12])  # Every 60 minutes (5min interval)
        elif 8 > int(days) > 1:
            ax2.set_xticks(df["Timestamp"][::12])  # Every 12 hours
        elif 91 > int(days) > 13:
            ax2.set_xticks(df["Timestamp"][::96])  # Every 24 hours
        else:
            ax2.set_xticks(df["Timestamp"][::24])
        plt.xticks(rotation=45)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.fig_frame)
        self.canvas.draw()
        # placing the canvas on the Tkinter window
        self.canvas.get_tk_widget().pack()
        # TODO: add RSI in charts https://stackoverflow.com/questions/57006437/calculate-rsi-indicator-from-pandas-dataframe
        center(self.figure_toplevel, root)

    def toplevel_quit(self, widget):
        """how to bind a messagebox to toplevel window in python
           https://stackoverflow.com/questions/17910866/python-3-tkinter-messagebox-with-a-toplevel-as-master"""
        if messagebox.askokcancel(title="Quit", message="Do you want to quit?", parent=widget):
            if widget is not None:
                widget.destroy()

    def custom_days(self, coin='usd'):
        """Prompt a dialog for the user to enter the desired custom days"""
        custom_days_input = simpledialog.askinteger(title='Days', prompt='Define days', parent=self.tree, minvalue=0)
        self.get_charts(coin=coin, days=str(custom_days_input))

    def refresh(self):
        """ Destroys the current frame in Secondpage and initiates a new one"""
        self.frame.destroy()
        for name in ['Coin List']:
            self.__init__(self.note, name,
                          self.controller)  # controller has to be the App => controller = self in App class
        self.frame.tkraise()
        self.frame.focus()
        print("Second page is refreshed")

    def __repr__(self):
        return self.name


class CoinWindow:
    """A window prompted by right-click on a specific coin of the coin list"""

    def __init__(self, operation=None, coin=None, controller=None):
        self.f3 = None
        self.name_entry = None
        self.f1 = None
        self.f0 = None
        self.window = None
        self.operation = operation
        self.root = root
        self.coin = coin
        self.controller = controller
        self.fnt = 'Arial 15'
        if self.coin:
            self.name = self.coin
        else:
            self.name = ''
        if operation:
            self.create_window()

    def create_window(self):
        x, y = self.root.winfo_x(), self.root.winfo_y()
        self.window = tk.Toplevel(self.root)
        self.window.geometry('+{}+{}'.format(x, y))
        self.f0 = ttk.Frame(self.window)
        if self.operation == 'delete':
            msg = 'Delete coin'
        elif self.operation == 'modify':
            msg = 'Modify coin'
        elif self.operation == 'insert':
            msg = 'Insert new coin'
        else:
            msg = ''
        self.f0.pack(side='top', expand=True, fill='both', padx=2, pady=2)
        tk.Label(self.f0, text=msg, font=self.fnt).pack(side='left', expand=True, fill='both')
        self.f1 = ttk.Frame(self.window)
        self.f1.pack(side='top', expand=True, fill='both', padx=2, pady=2)
        ttk.Label(self.f1, text='Name: ', font=self.fnt).pack(side='left', expand=True, fill='both')
        self.name_entry = tk.Entry(self.f1, font=self.fnt, relief='sunken')
        self.name_entry.pack(side='left', expand=True, fill='both')
        if self.operation != 'insert':
            self.name_entry.insert('end', self.name)
        if self.operation == 'delete':
            self.name_entry.config(state='disabled')
        self.f3 = ttk.Frame(self.window)
        self.f3.pack(side='top', expand=True, fill='both', padx=2, pady=2)
        b1 = ttk.Button(self.f3, text='OK', command=self.to_act)
        b1.pack(side='left', expand=True, fill='both', padx=2, pady=2)
        b2 = ttk.Button(self.f3, text='Cancel', command=self.no_act)
        b2.pack(side='left', expand=True, fill='both', padx=2, pady=2)
        self.root.wait_window(self.window)

    def to_act(self):
        if self.operation == 'delete':
            self.window.destroy()
            Coin.delete_coin(self.name)
            if autosave.get() is True:
                self.controller.persistent.store()
                print(f'CoinWindow()>to_act()>Coin is autosaved!')
        else:
            new_name = self.name_entry.get().strip()
            # If the given coin already exists, we do nothing. Otherwise, we insert the coin name.
            if new_name in Coin.thecoins:
                tk.messagebox.showwarning(title='Warning', message=f'The coin {new_name} already exists.')
            else:
                if new_name:
                    Coin(new_name)
                    if autosave.get() is True:
                        self.controller.persistent.store()
                        print(f'CoinWindow()>to_act()>Coin is autosaved!')
            self.window.destroy()
        print('CoinWindow()>to_act()>Window destroyed')
        self.controller.frames['Coin List'].display_with_term()  # Calling controller (=App), the saved frames,
        # the value of the saved key (the key is the name of the class and the value is the object Secondpage class)
        # and last but not least, the function 'display_with_term()'

    def no_act(self):
        self.window.destroy()
        print('CoinWindow()Window destroyed')
        self.controller.frames['Coin List'].display_with_term()


class Coin_prices:
    """Retrieve prices from Coingecko"""
    thecoins_prices = {}

    def __init__(self, thecoins, controller):
        self.controller = controller
        self.thecoins: list = thecoins
        Coin_prices.thecoins_prices.clear()  # Clears the dictionary to display properly the new coins.

        try:
            # Returns a dictionary: {'bitcoin': {'usd': 35365}, 'polkadot': {'usd': 18.19}}
            coins_prices = cg.get_price(ids=self.thecoins, vs_currencies='usd')
            print(coins_prices)
        except Exception as err:
            print(f"Connecting to GoinGecko failed due to {err}")
            messagebox.showwarning('Warning', message='Connecting to GoinGecko failed')

        count = len(coins_prices)
        print(coins_prices)
        for x in range(count):
            coin_dict = list(coins_prices.values())
            coin_names = list(coins_prices.keys())
            name = str(coin_names[x])
            price = ''
            try:  # To catch the exception to not having a price
                price = list(coin_dict[x].values())
                price = price[0]
                Coin_prices.thecoins_prices[name] = price
            except:
                Coin_prices.thecoins_prices[name] = 'Price not found'
                print(f'Price for {name} was not found')
            logger.debug(name, '= ', price, '$')


class CustomMenuBar(ttk.Frame):
    """Substitute the menu bar
    https://stackoverflow.com/questions/63206613/how-to-change-the-color-of-a-tk-menu-object
    """

    def __init__(self, master=None, **kw):
        # kw = tk._cnfmerge((cnf, kw))
        # kw['relief'] = kw.get('relief', 'raised')
        # self._foregroung = kw.pop('fg', kw.pop('foreground', 'black'))
        # self._over_bg = kw.pop('overbackground', 'blue')
        super().__init__(master=master)
        self._lb_list = []

    def _on_press(self, label, command=None):
        """Internal function.
        This is called when a user clicks on a menubar."""
        label.menu.post(label.winfo_rootx(),
                        label.winfo_rooty() + label.winfo_height() + 5)  # 5 padding (set accordingly)
        if command:
            command()  # Calls the function passed to `add_menu` method.

    def add_menu(self, title, menu, font, command=None):
        """Add menu labels."""
        l = ttk.Label(self, text=title, font=font, padding=5)
        l.pack(side='left')
        l.menu = menu  # Easy to access menu with the instance
        # Underline text: https://stackoverflow.com/questions/3655449/underline-text-in-tkinter-label-widget
        current_font = tk.font.Font(l, l.cget("font"))
        current_font.configure(underline=True, weight="bold")
        l.configure(font=current_font)
        l.bind('<Enter>', lambda e: self.change_foreground(widget=l, operation='enter'))
        l.bind('<Leave>', lambda e: self.change_foreground(widget=l, operation='leave'))

        #   of the label saved in the `self._lb_list`
        l.bind('<1>', lambda e: self._on_press(l, command))
        self._lb_list.append(l)

    def change_foreground(self, widget, operation):
        if root.tk.call("ttk::style", "theme", "use") == "azure-dark":
            if operation == 'enter':
                widget.config(foreground='blue')
            else:
                widget.config(foreground='white')
            #print("CustomMenuBar>change_foreground>Azure-dark>changed")
        elif root.tk.call("ttk::style", "theme", "use") == "azure-light":
            if operation == 'enter':
                widget.config(foreground='blue')
            else:
                widget.config(foreground='black')
            #print("CustomMenuBar>change_foreground>Azure-light>changed")


class App:
    """Main App"""
    x = 1000
    y = 600
    # A solution https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
    available_coin_list = {}
    global page_dict
    page_dict = {}  # https://stackoverflow.com/questions/32212408/how-to-get-variable-data-from-a-class

    def __init__(self, root):
        self.time = None
        self.f_time = None
        self.top_label = None
        self.switch = None
        root.geometry(f'{App.x}x{App.y}')
        self.root = root
        center(root)
        self.root.title('My cryptocurrency app')
        self.custom_menu_bar = CustomMenuBar(self.root)
        self.custom_menu_bar.pack(side='top', fill='x', anchor='n', pady=0)
        global autosave
        autosave = tk.BooleanVar()  # To save the user's choice over autosaving the coin list
        self.widgets()
        self.note = ttk.Notebook(self.root)
        self.note.pack(expand=True, fill='both', padx=1, pady=1)
        self.secondpage = App.retrieve_second(self)
        # self.maipage = App.retrieve_main(self)
        self.frames = page_dict
        print('The initial pages are: ', self.frames)
        self.persistent = Persistent()  # to call an instance of Persistent class
        # Custom Menu bar
        self.main_menu = Menu(
            self.custom_menu_bar, font='Arial 16', tearoff=0
        )
        # Tearoff has to be 0, in order the command to start being posted in position 0.
        # self.custom_menu_bar.config(menu=self.main_menu)  # if this is enabled, the menu will appear in the top left of the window

        # Emerging Menu for main tk Window
        self.context = Menu(self.main_menu, font='Arial 16',
                            tearoff=0)
        self.main_menu.add_command(label='Show available coins', font='Arial 10', command=self.show_available_coins)
        self.main_menu.add_command(label='Show coin list', font='Arial 10', command=self.submenu_show_coinlist)
        self.main_menu.add_command(label='Get & show coin prices ', font='Arial 10', command=self.submenu_gets_prices)
        self.main_menu.add_command(label='Show saved coin prices ', font='Arial 10',
                                   command=self.submenu_show_saved_prices)
        self.main_menu.add_command(label="Load coins from file", command=self.read_from_file, font='Arial 10')
        self.main_menu.add_command(label='Save', font='Arial 10',
                                   command=self.main_menu_save)  # Save the list to csv file
        self.main_menu.add_separator()
        self.main_menu.add_command(label='Exit', font='Arial 10', command=self.exit_the_program)
        # add the main menu to the Custom menubar
        self.custom_menu_bar.add_menu(title='Menu', menu=self.main_menu, font='Arial 13')
        # create the Help menu
        self.help_menu = Menu(self.main_menu, tearoff=0)
        self.help_menu.add_command(label='Change theme', command=self.change_theme)
        self.help_menu.add_command(label='Welcome')
        self.help_menu.add_command(label='About...')
        # add the Help menu to the Custom menubar
        self.custom_menu_bar.add_menu(title='Help', menu=self.help_menu, font='Arial 13')
        '''
        # Main menu
        self.main_menu = Menu(self.root, font='Arial 16',
                              tearoff=0)  # Tearoff has to be 0, in order the command to start being posted in position 0.
        self.root.config(menu=self.main_menu)  # if this is enabled, the menu will appear in the top left of the window
        # Emerging Menu for main tk Window
        self.context = Menu(self.main_menu, font='Arial 16',
                            tearoff=0)
        self.context.add_command(label='Show available coins', font='Arial 10', command=self.show_available_coins)
        self.context.add_command(label='Show coin list', font='Arial 10', command=self.submenu_show_coinlist)
        self.context.add_command(label='Get & show coin prices ', font='Arial 10', command=self.submenu_gets_prices)
        self.context.add_command(label='Show saved coin prices ', font='Arial 10',
                                 command=self.submenu_show_saved_prices)
        self.context.add_command(label='Save', font='Arial 10',
                                 command=self.main_menu_save)  # Save the list to csv file
        self.context.add_separator()
        self.context.add_command(label='Exit', font='Arial 10', command=self.exit_the_program)
        # Add the cascade here. The submenu has to be built first and then be added to the main menu
        self.main_menu.add_cascade(label='Menu', menu=self.context)
        # create the Help menu
        help_menu = Menu(self.main_menu, tearoff=0)
        help_menu.add_command(label='Change theme', command=self.change_theme)
        help_menu.add_command(label='Welcome')
        help_menu.add_command(label='About...')
        # add the Help menu to the menubar
        self.main_menu.add_cascade(
            label="Help",
            menu=help_menu,
            underline=0
        )'''

    def save_retrieve_available_coins(self):
        """Checks if the saved info is old and replaces it with a new list of coins"""
        with Db() as database:
            available_coins_retrieved_settings_time = database.check_settings_time()
            if (
                    time.time() - available_coins_retrieved_settings_time > 86400
            ):
                database.save_settings_time()
                available_coins_list = cg.get_coins_list()
                logger.debug(f"Got a new coin list")
                database.save_all_available_coins(coins=available_coins_list)
                return available_coins_list

            logger.debug(f"Fetching the saved list with available coins")
            return database.retrieve_available_coins()

    def show_available_coins(self):
        """Show available coins from Coingecko"""
        '''[{'id': '0-5x-long-eos-token', 'symbol': 'eoshalf', 'name': '0.5X Long EOS Token'}]'''
        available_coins_list = self.save_retrieve_available_coins()
        for dicti_of_coin in available_coins_list:
            coin_id = dicti_of_coin["id"]
            symbol = dicti_of_coin["symbol"]
            name = dicti_of_coin["name"]
            coin_tuple = (coin_id, symbol, name)
            AvailableCoinsMultiColumnTree.values.append(coin_tuple)
        tree = AvailableCoinsMultiColumnTree(controller=self)

    def main_menu_save(self):
        """Calls the Persistent class and saves the current list to the .csv file"""
        Persistent.store()

    def submenu_show_coinlist(self):
        """Just shows the coinlist in the secondpage of the notebook(aka Secondpage class)"""
        # Bind the keys to the proper list
        self.frames['Coin List'].search.bind('<KeyRelease>', self.frames['Coin List'].search_handler)
        Secondpage.fill_box(self.frames['Coin List'])
        logger.debug('Show coin list called')

    def submenu_gets_prices(self):
        """Gets the prices for the given coins in Coin.thecoins"""
        Coin_prices(thecoins=Coin.thecoins, controller=self)
        # Overwrite bind of keys to the proper list, the one with the prices
        # self.frames['Coin List'].search.bind('<KeyRelease>', self.frames['Coin List'].search_handler_only_saved)
        Secondpage.fill_box_with_prices(self.frames['Coin List'], retrieve=False)

    def submenu_show_saved_prices(self):
        """Just show saved prices in Listbox"""
        Secondpage.fill_box_with_prices(self.frames['Coin List'], retrieve=False)

    def read_from_file(self):
        """Reads a csv containing coins and fills the Treeview"""
        self.persistent.read_from_file()
        Secondpage.fill_box(self.frames['Coin List'])
        if autosave:
            self.persistent.store()

    def exit_the_program(self):
        """Exits the program"""
        # self.root.destroy()
        print(f'App>exit_the_program()')
        sys.exit()

    def change_theme(self):
        # NOTE: The theme's real name is azure-<mode>
        if root.tk.call("ttk::style", "theme", "use") == "azure-dark":
            # Set light theme
            root.tk.call("set_theme", "light")
        else:
            # Set dark theme
            root.tk.call("set_theme", "dark")

    def post_menu(self, event):
        """Posts the main menu at the exact position of mouse click"""
        self.context.post(event.x_root, event.y_root)
        logger.debug("Emerging Menu via right click is now visible")

    def get_page(self, page_class):
        """Return the instance of a page given its class name as a string"""
        print(self.frames.keys())
        print(self.frames.values())
        print(self.frames[page_class])
        return self.frames[page_class]

    def retrieve_main(self):
        """Retrieve Mainpage"""
        for name in ['Mainpage']:
            if name not in list(page_dict.keys()):
                page_dict[name] = Mainpage(self.note, name, controller=self)
            else:
                self.frames['Mainpage'].frame.destroy()
                page_dict[name] = Mainpage(self.note, name, controller=self)

    def retrieve_second(self):
        """Retrieve second page"""
        for name in ['Coin List']:
            page_dict[name] = Secondpage(self.note, name, controller=self)
            # return Secondpage(self.note, name)

    def get_page_2(self, page_class):
        """Return the instance of a page given its class name as a string"""
        try:
            for page in self.frames.values():
                if str(page.__class__.__name__) == page_class:
                    page.frame.destroy()
                    App.retrieve_second(self)
                    logger.debug('The new refreshed dictionary of classes is: ', page_dict)
        except:
            print(f"Warning: Error in loading {page_class}")

    def widgets(self):
        # Top label
        self.top_label = ttk.Label(self.root,
                                   font="Arial 36")
        self.top_label.pack(fill='both')
        '''#' Time frame
        ti''me_now = datetime.now()
        dt = str(time_now.strftime("%d-%m-%Y, %H:%M:%S"))
        dt = 'Date: ' + dt
        var = StringVar()
        var.set(dt)
        self.f_time = ttk.Frame(root, height=40, width=160)
        self.f_time.pack(expand=False, side='left', fill="none", padx=20, pady=20)
        self.f_time.place(x=5, y=40)
        self.time = tk.Label(self.f_time, textvariable=var)
        self.time.pack(side='left')'''
        # Switch button
        self.switch = ttk.Checkbutton(self.top_label, text="Autosave", style="Switch.TCheckbutton",
                                      command=self.autosave_choice, variable=autosave, onvalue=str2bool(1),
                                      offvalue=str2bool(0))
        self.switch.pack(side='right', padx=5, pady=10)
        autosave.set(str2bool(1))  # Set the autosave BooleanVar to True
        # Tooltip attached to the Checkbutton -> https://github.com/gnikit/tkinter-tooltip
        tktooltip.ToolTip(self.switch,
                          msg='Switch to enable/disable autosaving \nthe coin list after every modification',
                          delay=0.1)

    def autosave_choice(self):
        print(f'Autosave set: type:{type(autosave)} value:{autosave.get()}')


class AvailableCoinsMultiColumnTree:
    """Creates a toplevel with the available coins"""
    id_list = []
    symbol_list = []
    name_list = []
    values = []
    header = ['ID', 'Symbol', 'Name']
    search_tree = []

    def __init__(self, controller):
        # dir_path = os.path.dirname(os.path.realpath(__file__))
        # print(dir_path)
        self.tree = None
        self.controller = controller
        self.toplevel_coins = tk.Toplevel()
        self.toplevel_coins.geometry('800x500+0+0')
        self.toplevel_coins.title('Available coins on CoinGecko')
        self.parentframe = ttk.Frame(self.toplevel_coins)
        self.parentframe.pack(expand=True, fill='both')
        # Search box
        self.f0 = ttk.LabelFrame(self.parentframe, text='Search')
        self.f0.pack(side='top', expand=False, padx=2, pady=2)  # Expand False so as not to expand to more space than
        # it needs
        self.search = tk.Entry(self.f0, font='Arial 16')
        self.search.pack(expand=False, fill='y')
        self.search.bind('<KeyRelease>', self.search_handler)
        # Tree
        self.frame = ttk.Frame(self.parentframe)  # Alternative, use LabelFrame
        self.frame.pack(expand=True, fill='both', padx=2, pady=2)
        self.setup_widgets()
        # Emerging menu
        self.context = Menu(font='Arial 12',
                            tearoff=0)  # Tearoff has to be 0, in order the command to start being posted
        # in position 0 of the menu.
        # self.toplevel_coins.config(menu=self.context) # if this is enabled, the menu will appear in the top left of the toplevel window
        self.context.add_command(label='Insert', command=self.insert)
        center(self.toplevel_coins, root)

    def setup_widgets(self):
        self.tree = ttk.Treeview(self.frame, columns=AvailableCoinsMultiColumnTree.header, show='headings')
        # Fill the tree
        for head in AvailableCoinsMultiColumnTree.header:
            self.tree.heading(column=head, text=f'{head}')
        for value in AvailableCoinsMultiColumnTree.values:
            self.tree.insert("", tk.END, values=value)
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.pack(expand=True, fill='both')
        self.tree.bind('<ButtonRelease-3>', self.post_menu)  # Menu is posted in self.tree from setup_widgets()!

    def search_handler(self, event):
        self.display_with_term()

    def display_with_term(self):
        """Gets the search term"""
        term = self.search.get()
        self.retrieve_coin_list(term)
        self.fill_box_after_search()

    def retrieve_coin_list(self, term=''):
        """Retrieve the searched coin list based on the term provided.
        If term=coin, retrieves only these coins.
        If term = None, it retrieves all the saved coins"""
        if term:
            start = time.time()
            logger.debug(f'Term : {term}')
            if len(AvailableCoinsMultiColumnTree.search_tree) != 0:
                AvailableCoinsMultiColumnTree.search_tree.clear()
            # Retrieve the tuples from the db
            with Db() as database:
                listed_coins = database.retrieve_coins_based_on_term(term=term)
                for tuple_coin in listed_coins:
                    # for item in tuple_coin:
                        # if term.lower() in item.lower():
                        #     if tuple_coin not in AvailableCoinsMultiColumnTree.search_tree:
                                AvailableCoinsMultiColumnTree.search_tree.append(tuple_coin)
            end = time.time()
            run_time = end - start
            print(f'Time: {run_time}')
            AvailableCoinsMultiColumnTree.search_tree = sorted(AvailableCoinsMultiColumnTree.search_tree)
            logger.debug('The searched coins in TopLevel based on term provided were successfully retrieved')
        # If term=''
        else:
            if len(AvailableCoinsMultiColumnTree.search_tree) != 0:
                AvailableCoinsMultiColumnTree.search_tree.clear()
            for tuple_coin in AvailableCoinsMultiColumnTree.values:
                AvailableCoinsMultiColumnTree.search_tree.append(tuple_coin)
            AvailableCoinsMultiColumnTree.search_tree = sorted(AvailableCoinsMultiColumnTree.search_tree)
        logger.debug('Search list for the treeview:')

    def fill_box_after_search(self):
        """Fills the listbox with coins from AvailableCoinsMultiColumnTree.search_tree"""
        # Clear the treeview
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
        except Exception as err:
            logger.debug(f"fill_box_after_search> {err}")
        # Fill the treeview based on the typed entry
        try:
            if len(AvailableCoinsMultiColumnTree.search_tree) != 0:
                for number, coin in enumerate(AvailableCoinsMultiColumnTree.search_tree):
                    self.tree.insert("", tk.END, values=coin)
            logger.debug('Search was successful: The results are now shown in Treeview')
        except Exception as err:
            print(f'Warning: Loading the searched coin list failed! {err}')

    def post_menu(self, event):
        self.context.post(event.x_root, event.y_root)
        logger.debug("Emerging Menu from class AvailableCoinsMultiColumnTree via right click is now visible")

    def insert(self):
        """ Inserts the selected ID from the coin in the Coin class """
        #  Solution: https://stackoverflow.com/questions/30614279/tkinter-treeview-get-selected-item-values
        current = self.tree.focus()
        logger.debug(f'AvailableCoinsMultiColumnTree>insert>The selected row: {self.tree.item(current)}')
        # Pick the first value from the key 'values' from the dictionary self.tree.item(current)
        current_id_from_coin = self.tree.item(current)['values'][0]
        logger.debug(f'AvailableCoinsMultiColumnTree>insert>Selected coin: {current_id_from_coin}')
        # Add the coin to Coin class
        if current_id_from_coin not in Coin.thecoins:
            if current_id_from_coin != '':  # To exclude the empty entry to be added
                Coin(current_id_from_coin)
                if autosave.get() is True:
                    print(f"AvailableCoinsMultiColumnTree>insert> Autosaving {current_id_from_coin} to the file")
                    self.controller.persistent.store()
        elif current_id_from_coin in Coin.thecoins:
            print(f"{current_id_from_coin} already exists in the list")
            # TODO: Create a class similar to AskQuit, named WarningMessage, to display a message to user
        self.controller.persistent.store()
        # Call the Secondpage.fill_box in order for the coin to be shown
        self.controller.frames["Coin List"].fill_box()


class AskQuit(tk.Toplevel):
    """
    A widget asking the user to quit or not.
    """

    def __init__(self, parent):
        super().__init__()
        # self.target = target
        self.parent = parent
        self.grab_set()
        self.big_frame = ttk.Frame(self)
        self.big_frame.pack(expand=True, fill='both')
        self.init_ui()
        self.setActive()
        # center_to_screen(self)
        # center_according_to_root(self, self.parent)
        center(self, self.parent)

    def init_ui(self):
        self.title("Quit")
        askquit_topframe = ttk.Frame(self.big_frame)
        askquit_topframe.pack(side='top', expand=True)
        valueLabel = ttk.Label(askquit_topframe, text="Do you want to quit?")
        valueLabel.pack(side='right', expand=True)
        image = Image.open("multimedia/images/questionmark.png")
        image = image.resize(
            (int(self.winfo_width() * 25), int(self.winfo_height() * 25)), Image.Resampling.LANCZOS
        )
        image = ImageTk.PhotoImage(image)
        image_label = ttk.Label(askquit_topframe, image=image)
        image_label.pack(side='left', expand=True, padx=10, pady=10)
        image_label.image = image
        buttonsframe = ttk.Frame(self.big_frame)
        buttonsframe.pack(side='bottom', expand=True)
        okButton = ttk.Button(buttonsframe, text="Ok", command=lambda: self.toplevel_quit(self.parent))
        okButton.pack(side='left', expand=True, pady=10, padx=10)
        cancelButton = ttk.Button(buttonsframe, text="Cancel", command=self.destroy)
        cancelButton.pack(side='right', expand=True, pady=10, padx=10)

    def toplevel_quit(self, widget=None):
        """how to bind a messagebox to toplevel window in python
           https://stackoverflow.com/questions/17910866/python-3-tkinter-messagebox-with-a-toplevel-as-master"""
        if widget is not None:
            if widget == root:
                print(f'AskQuit>toplevel_quit: Root is now exiting')
                sys.exit()
            else:
                widget.destroy()
                self.destroy()
                print(f'AskQuit>toplevel_quit: {widget} & {self} is now destroyed')

        else:
            self.destroy()
            print(f'AskQuit>toplevel_quit: {self} is now destroyed')

    def setActive(self):
        """
        https://stackoverflow.com/questions/15944533/how-to-keep-the-window-focus-on-new-toplevel-window-in-tkinter
        """
        self.big_frame.lift()
        self.big_frame.focus_force()
        self.big_frame.grab_set()
        # self.parent.grab_release()


def sort_(data) -> float | int:
    """Convert strings to float and 'Price not found' to 0"""
    try:
        return float(data[0])
    except ValueError:
        return 0  # If price not found, the price is set to 0 in order to be sorted alongside the other coins


def sortby(tree, col, descending) -> None:
    """sort tree contents when a column header is clicked on
    https://www.daniweb.com/programming/software-development/threads/350266/creating-table-in-python#post1487238"""
    # grab values to sort
    data = [(tree.set(child, col), child)
            for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    # data =  change_numeric(data)
    # now sort the data in place
    if col.title() == 'Coin':
        data.sort(reverse=descending)
    elif col.title() == 'Price':
        data.sort(key=sort_, reverse=descending)
    for ix, item in enumerate(data):
        if isinstance(item[1], int):
            tree.move(item, "", ix)
        else:
            tree.move(item[1], '', ix)
    # switch the heading, so it will sort in the opposite direction
    tree.heading(col, command=lambda colu=col: sortby(tree, col,
                                                      int(not descending)))


def str2bool(v: bool | int | str) -> bool | None:
    """
    Convert a string to a boolean argument
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(v, bool):
        return v
    elif isinstance(v, int):
        if v == 1:
            return True
        elif v == 0:
            return False
    elif v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def close_tkinter() -> None:
    if messagebox.askokcancel(title="Quit", message="Do you want to quit?"):
        root.destroy()
        logger.warning('close_tkinter(): Tkinter window is exiting')
        sys.exit()


def center(window, parent_window=None) -> None:
    """
    https://stackoverflow.com/questions/3352918/how-to-center-a-window-on-the-screen-in-tkinter
    :param window: The window to be centered
    :param parent_window: A toplevel or root
    """
    if not parent_window:
        window.update_idletasks()
        width = window.winfo_width()
        frm_width = window.winfo_rootx() - window.winfo_x()
        win_width = width + 2 * frm_width
        height = window.winfo_height()
        titlebar_height = window.winfo_rooty() - window.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = window.winfo_screenwidth() // 2 - win_width // 2
        y = window.winfo_screenheight() // 2 - win_height // 2
        window.geometry('+{}+{}'.format(x, y))
        window.deiconify()
        logger.debug(f"Window: {window} centered according to the screen width and height")
    else:
        window.update_idletasks()
        width_parent = parent_window.winfo_width()
        height_parent = parent_window.winfo_height()
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x_dif = width_parent // 2 - size[0] // 2
        y_dif = height_parent // 2 - size[1] // 2
        window.geometry('+{}+{}'.format(parent_x + x_dif, parent_y + y_dif))
        logger.debug(f"Window: {window} centered according to the {parent_window} width and height")


if __name__ == "__main__":
    persist = Persistent()
    persist.retrieve()  # Retrieve the saved coin list
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logger.debug(f"{dir_path=}")
    root = tk.Tk()  # First window
    font = tk.font.Font(size=11)
    #root.tk.call('source',
    #             os.path.join(dir_path, 'source/azure/azure.tcl'))  # https://github.com/rdbende/Azure-ttk-theme
    #root.tk.call("set_theme", "dark")
    myapp = App(root)
    #  This binds the X button of tkinter with a specific function. Otherwise, the script leaves a hung process behind
    #  when used as an exe, after drawing the chart.
    #  https://stackoverflow.com/questions/111155/how-do-i-handle-the-window-close-event-in-tkinte
    root.protocol(name="WM_DELETE_WINDOW", func=lambda: AskQuit(root))
    root.mainloop()

# To integrate into pyinstaller
# https://stackoverflow.com/questions/47380748/how-to-make-pyinstaller-import-the-ttk-theme
# To implement the same theme to title bar https://stackoverflow.com/questions/23836000/can-i-change-the-title-bar-in-tkinter
# https://stackoverflow.com/questions/4066027/making-tkinter-windows-show-up-in-the-taskbar
