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


    def doAppendToExpensePlanner(self, day, month, year, betragAusgabe, bezeichnungDerAusgabe, user_id):
        
        self.cursor.execute(f"INSERT INTO expensePlanner (betragAusgabe, bezeichnungDerAusgabe, tag, monat, jahr, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
                            (int(betragAusgabe), str(bezeichnungDerAusgabe), int(day), int(month), int(year), int(user_id)))
        
        self.connection.commit()


    def doDeleteFromExpensePlanner(self, bezeichnungDerAusgabe, day,  month, year, user_id):
        self.cursor.execute("DELETE FROM expensePlanner WHERE bezeichnungDerAusgabe = ? AND tag = ? AND monat = ? AND jahr = ? AND user_id = ?",
                            (bezeichnungDerAusgabe, day, month, year, user_id))
        
        self.connection.commit()

    
    def doDeleteFromMonthlyBudget(self, betrag, bezeichnungDerAusgabe, entry_flag, user_id):
        self.cursor.execute("DELETE FROM monthlyBudget WHERE expense = ? AND description = ? AND expense_flag = ? AND user_id = ?",
                            (betrag, bezeichnungDerAusgabe, entry_flag, user_id))
        
        self.connection.commit()
    
    
    def doAppendToMonthlyBudget(self, expseneAmount, description, expense_flag, user_id):
        
        # Als Expense_flag wird entweder 'REV' (Revenue) oder 'EXP' (Expense) verwendet
        self.cursor.execute("INSERT INTO monthlyBudget (expense, description, expense_flag, user_id) VALUES (?,?,?,?)", (float(expseneAmount), str(description), str(expense_flag), int(user_id))) 
        
        self.connection.commit()

    # *********************************************************************** #

    # *********************************************************************** #
    #                      Database Reading Operations                        #
    # *********************************************************************** # 


    def getAusgabenFromExpensePlanner(self, month, year, user_id):

        self.cursor.execute("SELECT * FROM expensePlanner WHERE monat = ? AND jahr = ? AND user_id = ?", (month, year, user_id))
        self.rows = self.cursor.fetchall()

        return self.rows
    
    
    def getAusgabenFromMonthlyBudget(self, user_id):
        
        self.cursor.execute("SELECT expense, description, expense_flag FROM monthlyBudget WHERE user_id = ?", (user_id,))
        self.rows = self.cursor.fetchall()
        
        return self.rows
    
    def getAusgabenFromUsers(self, username, password):

        self.cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))

        user_row = self.cursor.fetchone()

        if user_row:
            return user_row[0]  # nur die Zahl
        
        return None

    # *********************************************************************** #



if __name__ == "__main__":

    pass
        

    