import logging
import csv
import os
import queue
import signal
from pathlib import Path

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import tkinter as tk

from main import *

logger = logging.getLogger(__name__)


class Application:
    """ The main application class, here we initialize the main LabelFrame windows (MainUI, SettingsUI and ConsoleUI)
    """

    def __init__(self, root):
        self.root = root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        self.root.title("INGtoYNAB Converter")

        # The main notebook, each tab consists of one PanedWindow with mutiple Labelframe windiws
        notebook = ttk.Notebook(self.root)
        notebook.grid(column=1, row=1, columnspan=2)

        # extend bindings to top level window allowing
        #   CTRL+TAB - cycles thru tabs
        #   SHIFT+CTRL+TAB - previous tab
        #   ALT+K - select tab using mnemonic (K = underlined letter)
        notebook.enable_traversal()

        first_tab = ttk.PanedWindow(self.root, orient=VERTICAL)
        first_tab.grid(row=0, column=0, sticky="nsew")

        # Create the panes and frames
        main_frame = ttk.Labelframe(first_tab, text="Info")
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        first_tab.add(main_frame)

        settings_frame = ttk.Labelframe(first_tab, text="Settings")
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.rowconfigure(0, weight=1)
        first_tab.add(settings_frame)

        console_frame = ttk.Labelframe(first_tab, text="Console")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        first_tab.add(console_frame)

        second_tab = ttk.PanedWindow(self.root, orient=VERTICAL)
        second_tab.grid(row=0, column=0, sticky="nsew")

        notebook.add(first_tab, text='Convert Transactions', underline=0, padding=2)
        notebook.add(second_tab, text='Manage Payees/Categories', underline=0, padding=2)

        # Initialize all frames
        self.main = MainUi(main_frame)
        self.settings = SettingsUi(settings_frame, self, self.root)
        self.console = ConsoleUi(console_frame)

        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        self.root.destroy()

class MainUi:

    def __init__(self, frame):
        self.frame = frame
        # Initialize UI
        self.initUI()
        self.add_padding()

    def initUI(self):

        # Main text explaining how app works
        text = """
               Grabs ING .csv file(s) from a directory, converts this into a YNAB format and exports files.
               Categories can be automatically extracted based on payee or memo (omschrijving/mededelingen).
               Unknown payees or memos can be added to categories.
               """
        intro = ttk.Label(self.frame, text=text, wraplength=800)
        intro.grid(column=0, columnspan=3, row=0, sticky=(W, E))

        text = """
               Input Format:
               Datum,Naam / Omschrijving,Rekening,Tegenrekening,Code,Af Bij,Bedrag (EUR),MutatieSoort,Mededelingen
               """

        input_format = ttk.Label(self.frame, text=text, wraplength=800)
        input_format.grid(column=0, columnspan=3, row=1, sticky=(W, E))

        text = """
               Output Format:
               Date,Payee,Category,Memo,Outflow,Inflow
               07/25/10,Sample Payee,(Master)Category,Sample Memo for an outflow,100.00,
               """
        output_format = ttk.Label(self.frame, text=text, wraplength=800)
        output_format.grid(column=0, columnspan=3, row=2, sticky=(W, E))

    def add_padding(self):
        for child in self.frame.winfo_children():
            child.grid_configure(padx=1, pady=1)

class SettingsUi:
    """ The mainUI class, shown on the top the opening screen, shows info about the app.
    """

    def __init__(self, frame, parent, root):
        self.frame = frame
        self.parent = parent
        self.root = root
        # Input/Output paths to search for
        self.input_path = StringVar()
        self.output_path = StringVar()
        # Initialize UI
        self.initUI()
        self.add_padding()

    def initUI(self):
        # Labels
        ttk.Label(self.frame, text="Input Directory").grid(column=0, row=3, sticky=E)
        ttk.Label(self.frame, text="Output Directory").grid(column=0, row=4, sticky=E)

        # Input fields
        input_entry = ttk.Entry(self.frame, width=35, textvariable=self.input_path)
        input_entry.grid(column=1, row=3, sticky=(W, E))

        output_entry = ttk.Entry(self.frame, width=35, textvariable=self.output_path)
        output_entry.grid(column=1, row=4, sticky=(W, E))

        # Buttons
        ttk.Button(self.frame, text="Browse..", command=self.inputdirectory).grid(column=2, row=3, sticky=W)
        ttk.Button(self.frame, text="Browse..", command=self.outputdirectory).grid(column=2, row=4, sticky=W)

        ttk.Button(self.frame, text="Run", command=lambda: self.scanAndConvert(self.input_path.get(), self.output_path.get())).grid(column=0, row=5, sticky=W)
        ttk.Button(self.frame, text="Close", command=lambda: self.parent.quit()).grid(column=1, row=5, sticky=W)

    def add_padding(self):
        for child in self.frame.winfo_children():
            child.grid_configure(padx=1, pady=1)

    def outputdirectory(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_path.set(dirname)

    def inputdirectory(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.input_path.set(dirname)

    # Main method to search for files and process transactions
    def scanAndConvert(self, input_path, output_path):

        logtext = 'Found ' + str(len(list(os.scandir(input_path)))) + ' files to process..'
        LogWindow.submit_message('INFO', logtext)

        for file in os.scandir(input_path):
            filename = Path(file)
            if not filename.name.startswith('.'):
                if not filename.name.endswith(".csv"):
                    logtext = str(filename) + ' is not a CSV file.. Skipped.'
                    LogWindow.submit_message('WARNING', logtext)
                else:
                    logtext = 'Started processing file ' + str(filename)
                    LogWindow.submit_message('INFO', logtext)

                    # Define output CSV filename
                    outputfile = output_path + '/' + filename.name
                    outputfile = open(outputfile, 'w', newline='')
                    outputwriter = csv.writer(outputfile)
                    outputwriter.writerow(["Date", "Payee", "Category", "Memo", "Outflow", "Inflow"])

                    # Load input CSV file
                    inputfile = open(filename)
                    csvreader = csv.reader(inputfile)
                    inputdata = list(csvreader)

                    logtext = 'Found ' + str(len(inputdata)) + ' rows to process.'
                    LogWindow.submit_message('INFO', logtext)

                    # Create transaction instance and convert
                    for row in inputdata[1:]:
                        print(row)

                        # date, payee, category, memo, type, amount

                        row = Transaction(row[0], row[1], str(row[8]), str(row[5]), str(row[6]))

                        # Use payee or memo to search for the category, if not retunn empty
                        category = row.searchPayees()
                        if not category:
                            category = row.searchMemos()
                            if not category:
                                logtext = 'Category not found for payee. Please add category to continue.'
                                LogWindow.submit_message('INFO', logtext)

                                dialog = AddCategoryDialog(self.root, prompt="Add category")
                                dialog.populate_transaction(row.__dict__.values())
                                result = dialog.show()

                                if result == 'Cancelled':
                                    logtext = 'Processing has been stopped.'
                                    LogWindow.submit_message('INFO', logtext)
                                    return
                                else:
                                    if result == 'Skipped':
                                        logtext = 'Transaction skipped.'
                                        LogWindow.submit_message('INFO', logtext)
                                        continue

                                    else:
                                        logtext = 'Category or payee added.'
                                        LogWindow.submit_message('INFO', logtext)
                                        category = result
                        if category:
                            logtext = 'Category found.' + 'Payee: ' + row.payee + ' Category: ' + category
                            LogWindow.submit_message('INFO', logtext)

                            if row.type == 'Af':
                                type = ','
                            else:
                                type = ',,'

                            # Date,Payee,Category,Memo,Outflow,Inflow
                            # 07/25/10,Sample Payee,,Sample Memo for an outflow,100.00,
                            # 07/26/10,Sample Payee 2,,Sample memo for an inflow,,500.003')

                            output = row.date + ',' + str(row.payee) + ',' + category
                            output = output + ',' + row.memo + type + str(row.amount)
                            print(output)

                            outputwriter.writerow(output.split(','))
                            logtext = 'Transaction processed.' + 'Payee: ' + row.payee + ' Category: ' + category
                            LogWindow.submit_message('INFO', logtext)

                    # Close the file
                    logtext = 'Processed file completly. Saving output to disk. ' + str(filename)
                    LogWindow.submit_message('INFO', logtext)
                    outputfile.close()


class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class LogWindow:
    """Class that creates the logging console.
    """

    def __init__(self, frame):
        self.frame = frame
        self.add_padding()
        self.loglines = tk.StringVar()
        self.level = tk.StringVar()

    def add_padding(self):
        for child in self.frame.winfo_children(): child.grid_configure(padx=5, pady=5)

    @staticmethod
    def submit_message(level, loglines):
        # Get the logging level numeric value
        lvl = getattr(logging, level)
        logger.log(lvl,loglines)


class ConsoleUi:

    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=12)
        self.scrolled_text.grid(row=0, column=0, sticky=(N, S, W, E))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)

        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


class CategoryUi:

    def __init__(self, parent, frame, root):
        self.parent = parent
        self.frame = frame
        self.initUI()
        self.add_padding()
        self.root = root

    def initUI(self):

        # Todo change styling of labels

        lbl1 = Label(self.frame, text="Payee", width=15)
        lbl1.grid(column=0, row=0, columnspan=1)

        self.entry1 = Entry(self.frame)
        self.entry1.grid(column=1, row=0, columnspan=2, sticky=(W, E))

        lbl2 = Label(self.frame, text="Memo", width=15)
        lbl2.grid(column=0, row=1, columnspan=1)

        self.entry2 = Entry(self.frame)
        self.entry2.grid(column=1, row=1, columnspan=2, sticky=(W, E))


        # Fetch (master)categories
        categories = Category('','','','').getCategories()
        mastercategories = Category('','','','').getMasterCategories()

        lbl3 = Label(self.frame, text="Master Category", width=15)
        lbl3.grid(column=0, row=2, columnspan=1)

        self.mastercat = ttk.Combobox(self.frame, values=mastercategories)
        self.mastercat.grid(column=1, row=2, columnspan=2, sticky=(W, E))

        lbl4 = Label(self.frame, text="Category", width=15)
        lbl4.grid(column=0, row=3, columnspan=1)

        self.category = ttk.Combobox(self.frame, values=categories)
        self.category.grid(column=1, row=3, columnspan=2, sticky=(W, E))

        ## buttons
        btn = {u"Save and continue": self.save_category, u"Skip": self.skip_category, u"Cancel Processing": self.cancel_process}
        column = -1
        for i, item in btn.items():
            column = column + 1
            ttk.Button(self.frame, text=u"%s" % i, command=item).grid(in_=self.frame, column=column, row=4)

    def add_padding(self):
        for child in self.frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def save_category(self):
        #Todo logging
        if self.mastercat.get() == '' and self.category.get() == '':
            messagebox.showerror(message='Master category and category not filled in.')
        else:
            if self.mastercat.get() == '':
                messagebox.showerror(message='Master category not filled in.')
            else:
                if self.category.get() == '':
                    messagebox.showerror(message='Category not filled in.')
                else:
                    self.parent.var.set(self.mastercat.get() + ': ' + self.category.get())
                    # If a payee or memo is filled in, add category, otherwise just leave as is
                    if self.entry1.get() or self.entry2.get():
                        Category(self.category.get(), self.entry1.get(), self.entry2.get(), self.mastercat.get()).addCategory()
                    self.root.destroy()

    def skip_category(self):
        self.parent.var.set('Skipped')
        self.root.destroy()

    def cancel_process(self):
        self.parent.var.set('Cancelled')
        self.root.destroy()


class TransactionUI:

    def __init__(self, frame, root):
        self.frame = frame
        self.initUI()
        self.add_padding()
        self.root = root
        self.var = tk.IntVar()

    def initUI(self):

        info = (u"Date", u"Payee", u"Memo",
                u"Type", u"Amount")
        for i, item in enumerate(info):
            ttk.Label(self.frame, text=u"%s:" % item).grid(in_=self.frame, column=0, row=i, sticky='w')

    def add_padding(self):
        for child in self.frame.winfo_children():
            child.grid_configure(padx=5, pady=5)


class AddCategoryDialog:
    def __init__(self, parent, prompt="", default=""):
        self.popup = tk.Toplevel(parent)
        self.popup.title(prompt)
        self.popup.transient(parent)
        self.parent = parent
        self.popup.columnconfigure(0, weight=1)

        # Create window
        self.bottom_pane = ttk.PanedWindow(self.popup, orient=HORIZONTAL)
        self.bottom_pane.grid(row=1, column=0, sticky="nsew")

        self.transaction_frame = ttk.Labelframe(self.bottom_pane, text="Unknown Transaction")
        self.transaction_frame.columnconfigure(1, weight=1)
        self.bottom_pane.add(self.transaction_frame, weight=5)

        self.category_frame = ttk.Labelframe(self.bottom_pane, text="Add Category")
        self.category_frame.grid(columnspan=1)

        self.category_frame.columnconfigure(0, weight=1)
        self.category_frame.rowconfigure(0, weight=1)
        self.bottom_pane.add(self.category_frame, weight=1)

        # Initalize
        self.transactions = TransactionUI(self.transaction_frame, self)
        self.category = CategoryUi(self, self.category_frame, self.popup)
        self.var = tk.StringVar()

    def show(self):
        self.parent.wait_window(self.popup)
        return self.var.get()


    def populate_transaction(self, transaction_info):

        for i, item in enumerate(transaction_info):
            ttk.Label(self.transaction_frame, text=u"%s" % item, wraplength=600).grid(in_=self.transaction_frame, column=1, row=i, sticky='w')


#Todo: add tab to see payees/memos and categories
# Todo: Change categories

#Todo: add explanation
# Todo; check output
# todo: check if no payee memo is possible
# TOdo: change text on frontpage

