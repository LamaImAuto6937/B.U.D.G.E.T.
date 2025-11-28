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

    # Expense Planner
    
    def doAppendToExpensePlanner(self, day, month, year, betragAusgabe, bezeichnungDerAusgabe, user_id):
        
        self.cursor.execute(f"INSERT INTO expensePlanner (betragAusgabe, bezeichnungDerAusgabe, tag, monat, jahr, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
                            (float(betragAusgabe), str(bezeichnungDerAusgabe), int(day), int(month), int(year), int(user_id)))
        
        self.connection.commit()


    def doDeleteFromExpensePlanner(self, bezeichnungDerAusgabe, day,  month, year, user_id):
        self.cursor.execute("DELETE FROM expensePlanner WHERE bezeichnungDerAusgabe = ? AND tag = ? AND monat = ? AND jahr = ? AND user_id = ?",
                            (bezeichnungDerAusgabe, day, month, year, user_id))
        
        self.connection.commit()

    
    # Monthly Budget
    
    def doDeleteFromMonthlyBudget(self, betrag, bezeichnungDerAusgabe, entry_flag, user_id):
        self.cursor.execute("DELETE FROM monthlyBudget WHERE expense = ? AND description = ? AND expense_flag = ? AND user_id = ?",
                            (betrag, bezeichnungDerAusgabe, entry_flag, user_id))
        
        self.connection.commit()
    
    
    def doAppendToMonthlyBudget(self, expseneAmount, description, expense_flag, user_id):
        
        # Als Expense_flag wird entweder 'REV' (Revenue) oder 'EXP' (Expense) verwendet
        self.cursor.execute("INSERT INTO monthlyBudget (expense, description, expense_flag, user_id) VALUES (?,?,?,?)", (float(expseneAmount), str(description), str(expense_flag), int(user_id))) 
        
        self.connection.commit()
    
    # Users
     
    def doAppendToUsers(self, user_id, username, hashed_password):
        
        self.cursor.execute("INSERT INTO users (user_id, username, password) VALUES (?,?,?)", (int(user_id), str(username), str(hashed_password)))
        
        self.connection.commit()
        
    # setBudgetForSelectedMonth
    
    def doAppendToSetBudgetForSelectedMonth(self, user_id, amount, month, year):
        
        self.cursor.execute("INSERT INTO setBudgetForSelectedMonth (user_Id, amount, month, year) VALUES (?, ?, ?, ?)", (int(user_id), float(amount), int(month), int(year)))

        self.connection.commit()
        
    # *********************************************************************** #

    # *********************************************************************** #
    #                      Database Reading Operations                        #
    # *********************************************************************** # 

    # Expense Planner
    
    def getAusgabenFromExpensePlanner(self, month, year, user_id):

        self.cursor.execute("SELECT * FROM expensePlanner WHERE monat = ? AND jahr = ? AND user_id = ?", (month, year, user_id))
        self.rows = self.cursor.fetchall()

        return self.rows
    
    # Monthly Budget
    
    def getAusgabenFromMonthlyBudget(self, user_id):
        
        self.cursor.execute("SELECT expense, description, expense_flag FROM monthlyBudget WHERE user_id = ?", (user_id,))
        self.rows = self.cursor.fetchall()
        
        return self.rows
    
    # Users
    
    def getUserIdFromUsers(self, username, password):

        self.cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))

        user_row = self.cursor.fetchone()

        if user_row:
            return user_row[0]  # nur die Zahl
        
        return None
    
    
    def getAllUserIDsFromUsers(self):
        
        self.cursor.execute("SELECT user_id FROM users")
        
        user_row = self.cursor.fetchall()
        
        return [r[0] for r in user_row]
    
    
    def getAllUsernamesFromUsers(self):
        
        self.cursor.execute("SELECT username FROM users")
        
        user_row = self.cursor.fetchall()
        
        return [r[0] for r in user_row]
    
    
    # setBudgetForSelectedMonth

    def getBudgetFromSetBudgetForSelectedMonth(self, user_id, month, year):
        
        self.cursor.execute("SELECT amount FROM setBudgetForSelectedMonth WHERE user_id = ? AND month = ? AND year = ?", (int(user_id), int(month), int(year)))
        
        amount = self.cursor.fetchone()
        
        return amount
    
    # *********************************************************************** #



if __name__ == "__main__":

    pass
        

    