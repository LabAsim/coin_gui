import sys
from tkinter import ttk
import tkinter as tk
from PIL import Image, ImageTk
from src.helper_funcs import center, logger


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
        self.root = master

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
        l.bind(
            '<Enter>', lambda e: self.change_foreground(widget=l, operation='enter', root=self.root)
        )
        l.bind(
            '<Leave>', lambda e: self.change_foreground(widget=l, operation='leave', root=self.root)
        )

        #   of the label saved in the `self._lb_list`
        l.bind('<1>', lambda e: self._on_press(l, command))
        self._lb_list.append(l)

    def change_foreground(self, root, widget, operation):
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
        logger.debug(f"{self.parent=}, {self.parent}")

    def init_ui(self):
        self.title("Quit")
        askquit_topframe = ttk.Frame(self.big_frame)
        askquit_topframe.pack(side='top', expand=True)
        valueLabel = ttk.Label(askquit_topframe, text="Do you want to quit?")
        valueLabel.pack(side='right', expand=True)
        image = Image.open("multimedia/images/questionmark.png")
        image = image.resize(
            size=(
                int(self.winfo_width() * 25),
                int(self.winfo_height() * 25)
            ),
            resample=Image.Resampling.LANCZOS
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
            logger.debug(f"{widget=}")
            if f"{widget}" == ".":
                logger.info(f'AskQuit>toplevel_quit: Root is now exiting')
                sys.exit()
            else:
                widget.destroy()
                self.destroy()
                logger.debug(f'AskQuit>toplevel_quit: {widget} & {self} is now destroyed')

        else:
            self.destroy()
            logger.debug(f'AskQuit>toplevel_quit: {self} is now destroyed')

    def setActive(self):
        """
        https://stackoverflow.com/questions/15944533/how-to-keep-the-window-focus-on-new-toplevel-window-in-tkinter
        """
        self.big_frame.lift()
        self.big_frame.focus_force()
        self.big_frame.grab_set()
        # self.parent.grab_release()

