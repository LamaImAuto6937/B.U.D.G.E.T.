import sqlite3

class monthlyBudgetDBOperations():
# *********************************************************************** #
# Konstruktor
# *********************************************************************** #
    def __init__(self):
        
        self.connectToDatabase("finanzapp.db") # Standard Datenbank

    def connectToDatabase(self, DB_NAME):

        self.connection = sqlite3.connect(DB_NAME)
        self.cursor = self.connection.cursor()

# *********************************************************************** #
# Read
# *********************************************************************** #

    def getRevenueRows(self, user_id):
        self.cursor.execute("SELECT expense FROM monthlyBudget WHERE user_id = ? AND expense_flag = ?", (int(user_id), 'REV'))
        return [row[0] for row in self.cursor.fetchall()]

    def getExpenseRows(self, user_id):
        self.cursor.execute("SELECT expense FROM monthlyBudget WHERE user_id = ? AND expense_flag = ?", (int(user_id), 'EXP'))
        return [row[0] for row in self.cursor.fetchall()]

    def getAusgabenFromMonthlyBudget(self, user_id):  
        self.cursor.execute("SELECT expense, description, expense_flag FROM monthlyBudget WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

# *********************************************************************** #
# Write
# *********************************************************************** #

    def doDeleteFromMonthlyBudget(self, betrag, bezeichnungDerAusgabe, entry_flag, user_id):
        self.cursor.execute("DELETE FROM monthlyBudget WHERE expense = ? AND description = ? AND expense_flag = ? AND user_id = ?",
                            (betrag, bezeichnungDerAusgabe, entry_flag, user_id))
            
        self.connection.commit()
        
    def doAppendToMonthlyBudget(self, expseneAmount, description, expense_flag, user_id):
            
        # Als Expense_flag wird entweder 'REV' (Revenue) oder 'EXP' (Expense) verwendet
        self.cursor.execute("INSERT INTO monthlyBudget (expense, description, expense_flag, user_id) VALUES (?,?,?,?)", (float(expseneAmount), str(description), str(expense_flag), int(user_id))) 
            
        self.connection.commit()

class expensePlannerDBOperations():
# *********************************************************************** #
# Konstruktor
# *********************************************************************** #

    def __init__(self):
        
        self.connectToDatabase("finanzapp.db") # Standard Datenbank

    def connectToDatabase(self, DB_NAME):

        self.connection = sqlite3.connect(DB_NAME)
        self.cursor = self.connection.cursor()

# *********************************************************************** #
# Read
# *********************************************************************** #

    def getBudgetFromSetBudgetForSelectedMonth(self, user_id, month, year):
        
        self.cursor.execute("SELECT amount FROM setBudgetForSelectedMonth WHERE user_id = ? AND month = ? AND year = ?", (int(user_id), int(month), int(year)))
        return self.cursor.fetchone()

    def getBetragAusgabe(self, user_id, month, year):
        self.cursor.execute("SELECT betragAusgabe FROM expensePlanner WHERE user_id = ? AND monat = ? AND jahr = ?", (int(user_id), int(month), int(year)))
        return [row[0] for row in self.cursor.fetchall()]

    def getAusgabenFromExpensePlanner(self, month, year, user_id):

        self.cursor.execute("SELECT * FROM expensePlanner WHERE monat = ? AND jahr = ? AND user_id = ?", (month, year, user_id))
        return self.cursor.fetchall()

# *********************************************************************** #
# Write
# *********************************************************************** #

    def doAppendToExpensePlanner(self, day, month, year, betragAusgabe, bezeichnungDerAusgabe, user_id):
        
        self.cursor.execute(f"INSERT INTO expensePlanner (betragAusgabe, bezeichnungDerAusgabe, tag, monat, jahr, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
                            (float(betragAusgabe), str(bezeichnungDerAusgabe), int(day), int(month), int(year), int(user_id)))
        
        self.connection.commit()


    def doDeleteFromExpensePlanner(self, bezeichnungDerAusgabe, day,  month, year, user_id):
        self.cursor.execute("DELETE FROM expensePlanner WHERE bezeichnungDerAusgabe = ? AND tag = ? AND monat = ? AND jahr = ? AND user_id = ?",
                            (bezeichnungDerAusgabe, day, month, year, user_id))
        
        self.connection.commit()

    def doAppendToSetBudgetForSelectedMonth(self, user_id, amount, month, year):
        
        self.cursor.execute("INSERT INTO setBudgetForSelectedMonth (user_Id, amount, month, year) VALUES (?, ?, ?, ?)", (int(user_id), float(amount), int(month), int(year)))

        self.connection.commit()

class userDBOperations():

# *********************************************************************** #
# Konstruktor
# *********************************************************************** #
    def __init__(self):
        
        self.connectToDatabase("finanzapp.db") # Standard Datenbank

    def connectToDatabase(self, DB_NAME):

        self.connection = sqlite3.connect(DB_NAME)
        self.cursor = self.connection.cursor()

# *********************************************************************** #
# Read
# *********************************************************************** #

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

# *********************************************************************** #
# Write
# *********************************************************************** #

    def doAppendToUsers(self, user_id, username, hashed_password):
        
        self.cursor.execute("INSERT INTO users (user_id, username, password) VALUES (?,?,?)", (int(user_id), str(username), str(hashed_password)))
        
        self.connection.commit()
        
class savingPlanDBOperations():

# *********************************************************************** #
# Konstruktor
# *********************************************************************** #

    def __init__(self):
        
        self.connectToDatabase("finanzapp.db") # Standard Datenbank

    def connectToDatabase(self, DB_NAME):

        self.connection = sqlite3.connect(DB_NAME)
        self.cursor = self.connection.cursor()

# *********************************************************************** #
# Read
# *********************************************************************** #

    def getPlanDetails(self, user_id):
        self.cursor.execute(
            "SELECT * FROM savingPlans WHERE user_id = ?",
            (int(user_id),)
        )
        return self.cursor.fetchall()

    def getPlanById(self, plan_id, user_id):
        
        self.cursor.execute("SELECT id, user_id, plan_name, description, target_amount, created_at FROM savingPlans WHERE id = ? AND user_id = ?", (plan_id, user_id))
        return self.cursor.fetchone()

    def getAllExistingPlanIDs(self):
        self.cursor.execute("SELECT id FROM savingPlans")
        return [row[0] for row in self.cursor.fetchall()]
    
    def getAllExistingAccountingIDs(self):
        self.cursor.execute("SELECT id FROM planAccounting")
        return [row[0] for row in self.cursor.fetchall()]

    def getAccountingSummary(self, plan_id):
        self.cursor.execute("SELECT * FROM planAccounting WHERE plan_id = ?", (plan_id,))
        return self.cursor.fetchall()
    
    def getSavings(self, plan_id):
        # Expense_flag = 1 Einzahlung
        # Expense_flag = 0 Auszahlung
        self.cursor.execute("SELECT amount FROM planAccounting WHERE plan_id = ? AND expense_flag = ?", (int(plan_id), 1))
        return [row[0] for row in self.cursor.fetchall()]

    def getExpenses(self, plan_id):
        # Expense_flag = 1 Einzahlung
        # Expense_flag = 0 Auszahlung
        self.cursor.execute("SELECT amount FROM planAccounting WHERE plan_id = ? AND expense_flag = ?", (int(plan_id), 0))
        return [row[0] for row in self.cursor.fetchall()]
    
    

# *********************************************************************** #
# Write
# *********************************************************************** #

    def doAppendToAccounting(self, plan_id, amount, expense_flag, description ):
        self.cursor.execute("INSERT INTO planAccounting (plan_id, amount, expense_flag, description) VALUES (?,?,?,?)", (int(plan_id), float(amount), int(expense_flag), str(description))) 
        self.connection.commit()

    def doDeleteFromAccounting(self, transaction_id):
        self.cursor.execute("DELETE FROM planAccounting WHERE id = ?", (int(transaction_id),))      
        self.connection.commit() 

    def doDeleteAllPlanEntriesFromAccounting(self, plan_id):
        self.cursor.execute("DELETE FROM planAccounting WHERE plan_id = ?", (int(plan_id),))
        self.connection.commit()

    def doCreateNewPlan(self, user_id, plan_name, plan_description, target_amount):
        self.cursor.execute("INSERT INTO savingPlans (user_id, plan_name, description, target_amount) VALUES (?,?,?,?)", (int(user_id), str(plan_name), str(plan_description), float(target_amount))) 
        self.connection.commit()  

    def doDeletePlan(self, plan_id):
        self.cursor.execute("DELETE FROM savingPlans WHERE id = ?", (int(plan_id),))
        self.connection.commit() 

if __name__ == "__main__":

    from ModuleOperationClasses import *

    Dataprovider = savingPlanDBOperations()
    HelperClass = Helper()
    ops = SavingPlan(HelperClass, Dataprovider)

    transactions_data = Dataprovider.doCreateNewPlan
    print(transactions_data)


    
