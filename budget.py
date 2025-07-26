import sqlite3
from datetime import date

class Data_Provider():
    
    def __init__(self):
        pass
    


class Budget():
    
    # Constructor: Bevor das Objekt erzeugt wird, wird das hier aufgerufen 
    
    #Note: The self parameter is a reference to the current instance of the 
    #      class, and is used to access variables that belong to the class.
    def __init__(self):
        
        self.month = date.month
        self.year = date.year
        self.connection = sqlite3.connect("finanzapp.db")
        self.cursor  = self.connection.cursor()

    def getSelectedMonth(self):

        return self.month
    
    def getSelectedYear(self):

        return self.year
    
    def setMonth(self, month):

        self.month = month

    def setYear(self, year):

        self.year = year

    def devShowColumnNames(self, table):

        # Zeigt alle Spalten der Tabelle "budget" an
        self.cursor.execute(f"""PRAGMA table_info({str(table)});""")
        columns = self.cursor.fetchall()

        for column in columns:
            print(column)
    
    def doAusgabe(self):
        
        ausgabe = self.cursor.execute("SELECT * FROM budget")
        
        rows = self.cursor.fetchall()

        for row in rows:
            print(f"Betrag: {row[0]} | Bezeichnung: {row[1]} | Datum: {row[2]}")


    def doAppendToTable(self, betragAusgabe, bezeichnungDerAusgabe):
        
        self.cursor.execute(f"INSERT INTO budget (betragAusgabe, bezeichnungDerAusgabe, datumDesEintrags) VALUES (?, ?, ?)", 
                            (betragAusgabe, bezeichnungDerAusgabe, date.today()))
        
        self.connection.commit()

    def deleteFromBudget(self, bezeichnungDerAusgabe, datumDesEintrags):
        self.cursor.execute("DELETE FROM budget WHERE bezeichnungDerAusgabe = ? AND datumDesEintrags = ?",
                            (bezeichnungDerAusgabe, datumDesEintrags))
        
        self.connection.commit()




if __name__ == "__main__":

    klasse = Budget()
    #klasse.deleteFromBudget("Cutie", "2025-07-26")