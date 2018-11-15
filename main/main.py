# ! python3

import datetime
import json


""" Tkinter methods """

from tkinter import *
from gui import *


class Database:

    def openDatabase(self):
        with open("database.json", "r") as read_file:
            data = json.load(read_file)
            return data


class Category:
    def __init__(self, category, payee, memo, master):
        self.category = category
        self.payee = payee
        self.memo = memo
        self.master = master

    def getCategories(self):

        data = Database().openDatabase()
        result = []

        for x in data['categories']:
            result.append(x['Category'])

        return result

    def getMasterCategories(self):

        data = Database().openDatabase()
        result = []

        for x in data['categories']:
            result.append(x['Master Category'])

        return list(set(result))

    def searchCategory(self):

        # Open json database and search of any memo's can be found within the nested JSON structure
        data = Database().openDatabase()
        count = -1
        #Todo logging

        for x in data['categories']:
            count = count + 1

            searchterm = x['Master Category']
            regex = re.compile(searchterm, re.IGNORECASE)
            result = regex.search(self.master)
            if result:
                searchterm = x['Category']
                regex = re.compile(searchterm, re.IGNORECASE)
                result = regex.search(self.category)
                if result:
                    return count
        else:
            return ''

    def addCategory(self):

        # Todo logging
        # First, check if already exists, if not create new other wise add
        pos = self.searchCategory()
        print(pos)

        data = Database().openDatabase()

        if pos == '':
            # Open JSON file and add new master and category, save file again
            add = {'Category': self.category, 'Master Category': self.master, 'Memos': [self.memo], 'Payees': [self.payee]}

            data['categories'].append(add)

            # Open JSON and save dict as obj
            js = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
            with open('database.json', 'w+') as f:
                f.write(js)
        else:

            # Open JSON file and add to existing category, save file again
            if self.payee != '':
                data['categories'][pos]['Payees'].append(self.payee)

            if self.memo != '':
                data['categories'][pos]['Memos'].append(self.memo)

            # Open JSON and save dict as obj
            js = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
            with open('database.json', 'w+') as f:
                f.write(js)

class Transaction:

    def __init__(self, date, payee, memo, type, amount):
        self.date = self.convertDate(date)
        self.payee = str(payee.replace(',', ' &'))
        self.memo = memo
        self.type = type
        self.amount = float(amount.replace(',', '.'))

    def searchPayees(self):
        # Open json database and search of any payee's can be found within the nested JSON structure
        data = Database().openDatabase()

        # Access data, search for payee regex in all payee elements
        for x in data['categories']:
            searchterm = "|".join(x['Payees'])
            if searchterm:
                regex = re.compile(searchterm, re.IGNORECASE)
                result = regex.search(self.payee)
                if result:
                    category = x['Master Category'] + ': ' + x['Category']
                    return category
        else:
            return ''

    def searchMemos(self):
        # Open json database and search of any memo's can be found within the nested JSON structure
        data = Database().openDatabase()
        for x in data['categories']:

            searchterm = "|".join(x['Memos'])
            if searchterm:
                regex = re.compile(searchterm, re.IGNORECASE)
                result = regex.search(self.memo)
                if result:
                    category = x['Master Category'] + ': ' + x['Category']
                    return category
        else:
            return ''

    def convertDate(self, date):
        regex = re.compile('\d\d\d\d\d\d\d\d')
        date = regex.search(date)
        date = datetime.datetime.strptime(date.group(0), '%Y%m%d').strftime('%d/%m/%y')
        return date


def main():

    logging.basicConfig(level=logging.DEBUG)
    root = tk.Tk()
    app = Application(root)
    app.root.mainloop()

if __name__ == '__main__':
    main()

