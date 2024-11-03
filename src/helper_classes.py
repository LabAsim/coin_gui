from tkinter import ttk
import tkinter as tk


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
