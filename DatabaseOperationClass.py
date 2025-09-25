import sqlite3

class DatabaseOperations():
    # Handelt DB-Aufrufe und die Selektion der richtigen DB

    # Konstruktor
    def __init__(self):
        
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


    def doAppendToExpensePlanner(self, day, month, year, betragAusgabe, bezeichnungDerAusgabe):
        
        self.cursor.execute(f"INSERT INTO expensePlanner (betragAusgabe, bezeichnungDerAusgabe, tag, monat, jahr) VALUES (?, ?, ?, ?, ?)", 
                            (betragAusgabe, bezeichnungDerAusgabe, day, month, year))
        
        self.connection.commit()


    def doDeleteFromExpensePlanner(self, bezeichnungDerAusgabe, day,  month, year):
        self.cursor.execute("DELETE FROM expensePlanner WHERE bezeichnungDerAusgabe = ? AND tag = ? AND monat = ? AND jahr = ?",
                            (bezeichnungDerAusgabe, day, month, year))
        
        self.connection.commit()

    
    def doDeleteFromMonthlyBudget(self, betrag, bezeichnungDerAusgabe, entry_flag):
        self.cursor.execute("DELETE FROM monthlyBudget WHERE expense = ? AND description = ? AND expense_flag = ?",
                            (betrag, bezeichnungDerAusgabe, entry_flag))
        
        self.connection.commit()
    
    
    def doAppendToMonthlyBudget(self, expseneAmount, description, expense_flag):
        
        # Als Expense_flag wird entweder 'REV' (Revenue) oder 'EXP' (Expense) verwendet
        self.cursor.execute("INSERT INTO monthlyBudget (expense, description, expense_flag) VALUES (?,?,?)", (expseneAmount, description, expense_flag)) 
        
        self.connection.commit()

    # *********************************************************************** #

    # *********************************************************************** #
    #                      Database Reading Operations                        #
    # *********************************************************************** # 


    def getAusgabenFromExpensePlanner(self, month, year):

        self.cursor.execute("SELECT * FROM expensePlanner WHERE monat = ? AND jahr = ?", (month, year))
        self.rows = self.cursor.fetchall()

        return self.rows
    
    
    def getAusgabenFromMonthlyBudget(self):
        
        self.cursor.execute("SELECT * FROM monthlyBudget")
        self.rows = self.cursor.fetchall()
        
        return self.rows


    # *********************************************************************** #



if __name__ == "__main__":

    DataProvider = DatabaseOperations()
    
    rows = DataProvider.getAusgabenFromExpensePlanner(8,2025)
    for row in rows:
        print(row)
        

    