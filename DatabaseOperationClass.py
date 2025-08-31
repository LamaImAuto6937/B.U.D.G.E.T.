import sqlite3
import DataProcessorClass

class DatabaseOperations():
    # Handelt DB-Aufrufe und die Selektion der richtigen DB

    # Konstruktor
    def __init__(self):
        
        self.DataProcessor = DataProcessorClass() # Data Processor Klasse
        self.connectToDatabase("finanzapp.db") # Standard Datenbank
    
    # *********************************************************************** #
    #                         Database Operations                             #
    # *********************************************************************** #  


    def connectToDatabase(self, DB_NAME):

        self.connection = sqlite3.connect(DB_NAME)
        self.cursor = self.connection.cursor()


    def devShowColumnNames(self, table):

        # Zeigt alle Spalten der Tabelle "budget" an
        self.cursor.execute(f"""PRAGMA table_info({str(table)});""")
        columns = self.cursor.fetchall()

        for column in columns:
            print(column)


    # *********************************************************************** #

    # *********************************************************************** #
    #                      Database Writing Operations                        #
    # *********************************************************************** # 


    def doAppendToTable(self, betragAusgabe, bezeichnungDerAusgabe):
        
        self.cursor.execute(f"INSERT INTO budget (betragAusgabe, bezeichnungDerAusgabe, tag, monat, jahr) VALUES (?, ?, ?, ?, ?)", 
                            (betragAusgabe, bezeichnungDerAusgabe, self.day, self.month, self.year))
        
        self.connection.commit()


    def doDeleteFromBudget(self, bezeichnungDerAusgabe, datumDesEintrags):
        self.cursor.execute("DELETE FROM budget WHERE bezeichnungDerAusgabe = ? AND datumDesEintrags = ?",
                            (bezeichnungDerAusgabe, datumDesEintrags))
        
        self.connection.commit()


    # *********************************************************************** #

    # *********************************************************************** #
    #                      Database Reading Operations                        #
    # *********************************************************************** # 


    def getAusgaben(self):

        self.cursor.execute("SELECT * FROM budget WHERE monat = ? AND tag = ?", (self.month, self.day))
        self.rows = self.cursor.fetchall()

        return self.rows


    # *********************************************************************** #



if __name__ == "__main__":

    #klasse = Budget()
    #klasse.devShowColumnNames("budget")

    pass