
import csv


class CreateCSV:
    def create(self):
        somedict=dict(raymond='red',rachel='blue',matthew='green')
        with(open("mycsvfile.csv",'wb')) as f:
            w = csv.writer(f)
            w.writerows(somedict.items())