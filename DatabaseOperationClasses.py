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
        self.cursor.execute("SELECT expense, duration FROM monthlyBudget WHERE user_id = ? AND expense_flag = ?", (int(user_id), 1))
        return self.cursor.fetchall()
    
    def getRevenueData(self, user_id):
            self.cursor.execute("SELECT * FROM monthlyBudget WHERE user_id = ? AND expense_flag = ?", (int(user_id), 1))
            return self.cursor.fetchall()

    def getExpenseRows(self, user_id):
        self.cursor.execute("SELECT expense, duration FROM monthlyBudget WHERE user_id = ? AND expense_flag = ?", (int(user_id), 0))
        return self.cursor.fetchall()
    
    def getExpenseData(self, user_id):
        self.cursor.execute("SELECT * FROM monthlyBudget WHERE user_id = ? AND expense_flag = ?", (int(user_id), 0))
        return self.cursor.fetchall()

    def getAusgabenFromMonthlyBudget(self, user_id):  
        self.cursor.execute("SELECT expense, description, expense_flag FROM monthlyBudget WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

# *********************************************************************** #
# Write
# *********************************************************************** #

    def doDeleteFromMonthlyBudget(self, monthlyBudgetID):
        self.cursor.execute("DELETE FROM monthlyBudget WHERE monthlyBudgetID = ?",
                            (monthlyBudgetID,))
            
        self.connection.commit()
        
    def doAppendToMonthlyBudget(self, expseneAmount, description, expense_flag, user_id, duration_in_months, start_date):
            
        # Als Expense_flag wird entweder 'REV' (Revenue) oder 'EXP' (Expense) verwendet
        self.cursor.execute("INSERT INTO monthlyBudget (expense, description, expense_flag, user_id, duration, start_date) VALUES (?,?,?,?,?,?)", (float(expseneAmount), str(description), int(expense_flag), int(user_id), int(duration_in_months), str(start_date))) 
            
        self.connection.commit()
        
    def doUpdateMonthlyBudgetEntry(self, amount, description, expense_flag, duration_in_months, start_date, monthlyBudgetID):
        
        self.cursor.execute(f"UPDATE monthlyBudget SET expense = ?, description = ?, expense_flag = ?, duration = ?, start_date = ? WHERE monthlyBudgetID = ?", (float(amount), str(description), int(expense_flag), int(duration_in_months), str(start_date), int(monthlyBudgetID)))

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
        self.cursor.execute(
            """
            SELECT e.id, e.betragAusgabe, e.bezeichnungDerAusgabe, e.day, e.monat, e.jahr, e.user_id, e.category_id
            FROM expensePlanner e
            WHERE e.monat = ? AND e.jahr = ? AND e.user_id = ?
            ORDER BY e.day ASC, e.id ASC
            """,
            (int(month), int(year), int(user_id)),
        )
        return self.cursor.fetchall()

    def getCategoryById(self, category_id):
        self.cursor.execute("SELECT id, name, color FROM categories WHERE id = ?", (int(category_id),))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1], "color": row[2]}

    def getTagByExpenseId(self, expense_id):
        """
        Holt alle Tags für einen bestimmten Expenseplanner-Eintrag.
        """
        self.cursor.execute(
            """
            SELECT t.name
            FROM expense_tags et
            LEFT JOIN tags t ON t.id = et.tag_id
            WHERE et.expense_id = ?
            """,
            (int(expense_id),),      
        )
        row = self.cursor.fetchall()
        if not row:
            return None
        return row
        
# *********************************************************************** #
# Write
# *********************************************************************** #

    def doDeleteFromSetBudgetForSelectedMonth(self, user_id, month, year):
        
        self.cursor.execute("DELETE FROM setBudgetForSelectedMonth WHERE user_id = ? AND month = ? AND year = ?", (int(user_id), int(month), int(year)))
        self.connection.commit()

    def doAppendToExpensePlanner(self, day, month, year, betragAusgabe, bezeichnungDerAusgabe, user_id, category_id=None, tags=None):
        
        self.cursor.execute(
            "INSERT INTO expensePlanner (betragAusgabe, bezeichnungDerAusgabe, day, monat, jahr, user_id, category_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (float(betragAusgabe), str(bezeichnungDerAusgabe), int(day), int(month), int(year), int(user_id), int(category_id) if category_id not in (None, "", "0") else None),
        )

        if tags is not None:
            expense_id = self.cursor.lastrowid

            available_tags = self.getTagsByUserId(int(user_id))

            for tag in tags:
                if tag not in available_tags:
                    # Neues Tag erzeugen
                    self.cursor.execute(
                        "INSERT INTO tags (user_id, name) VALUES(?, ?)", 
                        (int(user_id), str(tag))
                    )
                    tag_id = self.cursor.lastrowid
                else:
                    # Existierendes Tag ID aus DB holen
                    self.cursor.execute(
                        "SELECT id FROM tags WHERE user_id = ? AND name = ?",
                        (int(user_id), str(tag))
                    )
                    tag_id = self.cursor.fetchone()[0]
                
                # IMMER die Verknüpfung erstellen
                self.cursor.execute(
                    "INSERT INTO expense_tags (expense_id, tag_id) VALUES(?, ?)",
                    (int(expense_id), int(tag_id))
                )

        self.connection.commit()

    def doDeleteFromExpensePlanner(self, entry_id):
        self.cursor.execute("DELETE FROM expense_tags WHERE expense_id = ?", (int(entry_id),))
        self.cursor.execute("DELETE FROM expensePlanner WHERE id = ?", (int(entry_id),))
        
        self.connection.commit()

    def doAppendToSetBudgetForSelectedMonth(self, user_id, amount, month, year):
        
        self.cursor.execute("INSERT INTO setBudgetForSelectedMonth (user_Id, amount, month, year) VALUES (?, ?, ?, ?)", (int(user_id), float(amount), int(month), int(year)))

        self.connection.commit()
        
    def doUpdateExpensePlannerEntry(self, user_id, betragAusgabe, bezeichnungAusgabe, day, monat, jahr, entry_id, category_id=None, tags=None):
        try:

            self.cursor.execute(
                """
                UPDATE expensePlanner 
                SET betragAusgabe = ?, bezeichnungDerAusgabe = ?, day = ?, monat = ?, jahr = ?, category_id = ? 
                WHERE id = ?
                """,(float(betragAusgabe), 
                    str(bezeichnungAusgabe), 
                    int(day), int(monat), 
                    int(jahr), 
                    int(category_id) if category_id not in (None, "", "0") else None, 
                    int(entry_id)),
            )
            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            return f"Error in doUpdateExpensePlannerEntry: {e}"

        currentEntryTags = [row[0] for row in self.getTagByExpenseId(entry_id) or []]
        updateTags = list( tags )
        availableTags = list( self.getTagsByUserId(user_id) )

        newTags = [tag for tag in updateTags if tag not in currentEntryTags] # Alle Tags aus updateTags (Neu), die nicht in currentEntryTags (Alt) sind
        deletedTags = [tag for tag in currentEntryTags if tag not in updateTags and tag not in newTags] # Alle Tags die in currentEntryTags (Alt) sind aber nicht in updateTags (Neu) und in newTags

        # Fügt Tags der Ausgabe hinzu
        # Erstellt automatisch neue Einträge in Tags falls noch nicht vorhanden
        for tag in newTags:
            if tag is not None:

                if tag not in availableTags:
                    self.doAppendToTags(user_id, tag)

                tag_id = self.getTagIdByNameUserId(user_id, tag)
                self.doAppendTagToExpense(entry_id, tag_id)

        for tag in deletedTags:
            if tag is not None:

                tag_id = self.getTagIdByNameUserId(user_id, tag)
                self.doDeleteTagFromExpense(entry_id, tag_id)
                
# *********************************************************************** #
# Category
# *********************************************************************** #
    # *********************************************************************** #
    # Write
    # *********************************************************************** #
    def setCategoryIdToNull(self, category_id):
        """Setzt category_id für die jeweilige id auf NULL"""
        try:
            self.cursor.execute("UPDATE expensePlanner SET category_id = NULL WHERE category_id = ?", ( int(category_id), ))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            return f"Error in setCategoryIdToNull: {e}"
        

# *********************************************************************** #
# Tags
# *********************************************************************** #
    # *********************************************************************** #
    # Read
    # *********************************************************************** #
    def getTags(self, user_id, tagQuery):
            """
            Holt alle Tags für einen bestimmten Benutzer, die dem Suchbegriff entsprechen.
            """
            
            self.cursor.execute(
                """
                SELECT DISTINCT name 
                FROM tags 
                WHERE user_id = ? AND name LIKE ? 
                ORDER BY usage_count DESC, name ASC 
                LIMIT 8
                """,(int(user_id), f"%{tagQuery}%"))
            
            return [row[0] for row in self.cursor.fetchall()]

    def getTagsByUserId(self, user_id):
        """
        Holt alle Tags, die einem bestimmten Benutzer zugewiesen sind
        """
        self.cursor.execute(
            """
            SELECT name
            FROM tags
            WHERE user_id = ?
            """, (int(user_id),)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def getTagIdByNameUserId(self, user_id, tag_name):
        try:
            self.cursor.execute("SELECT id FROM tags WHERE user_id = ? AND name = ?", ( int(user_id), str(tag_name) ))
            return self.cursor.fetchone()[0] 
        except Exception as e:
            return f"Error in getTagIdByNameUserId: {e}" 
              
    # *********************************************************************** #
    # Write
    # *********************************************************************** #  
    def doAppendToTags(self, user_id, tag_name):
        """Erstellt einen neuen Tag"""
        try:
            self.cursor.execute("INSERT INTO tags (user_id, name) VALUES (?, ?)", (int(user_id), str(tag_name)))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            return f"Error in doAppendToTags: {e}"

    def doAppendTagToExpense(self, expense_id, tag_id):
        """Fügt einen Tag einer Ausgabe hinzu"""
        try:
            self.cursor.execute("INSERT INTO expense_tags (expense_id, tag_id) VALUES (?, ?)", ( int(expense_id), int(tag_id) ))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            return f"Error in doAppendTagToExpense: {e}"

    def doDeleteTagFromExpense(self, expense_id, tag_id):
        """Entfernt einen Tag von einer Ausgabe"""
        try:
            self.cursor.execute("DELETE FROM expense_tags WHERE expense_id = ? and tag_id = ?", ( int(expense_id), int(tag_id) ))   
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            return f"Error in doDeleteTagFromExpense: {e}"
         
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

        self.cursor.execute("SELECT user_id FROM users WHERE (username = ? OR email = ?) AND password = ?", (username, username,password))

        user_row = self.cursor.fetchone()

        if user_row:
            return user_row[0]  # nur die Zahl
        
        return None
    
    def getValidationStateFromUsers(self, user_id):
        self.cursor.execute("SELECT is_verified FROM users WHERE user_id = ?", (int(user_id),))
        return self.cursor.fetchone()
    
    def getUserByUsernameOrEmail(self, username):
        self.cursor.execute("SELECT user_id, password FROM users WHERE username = ? OR email = ?", (username, username))
        return self.cursor.fetchone()
    
    def getAllUserIDsFromUsers(self):
        
        self.cursor.execute("SELECT user_id FROM users")
        
        user_row = self.cursor.fetchall()
        
        return [r[0] for r in user_row]
      
    def getAllUsernamesFromUsers(self):
        self.cursor.execute("SELECT username FROM users")
        user_row = self.cursor.fetchall()
        return [r[0] for r in user_row]    

    def getUserByUserId(self, user_id):
        self.cursor.execute("SELECT username, email FROM users WHERE user_id = ?", (int(user_id),))
        return self.cursor.fetchone()
    
# *********************************************************************** #
# Write
# *********************************************************************** #

    def doAppendToUsers(self, username, hashed_password, email):
        import datetime
        
        self.cursor.execute("INSERT INTO users (username, password, email) VALUES (?,?,?)", (str(username), str(hashed_password), str(email) ))
        self.connection.commit()
        
    def doDeleteFromUsers(self, user_id):
        
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("DELETE FROM users WHERE user_id = ?", (int(user_id),))
        self.connection.commit()
    
    def doUpdateCredentialsUsername(self, user_id, new_username):
        self.cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (str(new_username), int(user_id)))
        self.connection.commit()
        
    def doUpdateCredentialsEmail(self, user_id, new_email):
        self.cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (str(new_email), int(user_id)))
        self.connection.commit()

    def doUpdateCredentialsPassword(self, user_id, new_password_hashed):
        self.cursor.execute("UPDATE users SET password = ? WHERE user_id = ?", (str(new_password_hashed), int(user_id)))
        self.connection.commit()
     
    def doUpdateValidationState(self, user_id, new_state):
        self.cursor.execute("UPDATE users SET is_verified = ? WHERE user_id = ?", (int(new_state), int(user_id)))
        self.connection.commit()
        
    def deleteExpiredUnverifiedUsers(self):
        self.cursor.execute("DELETE FROM users WHERE is_verified = 0 AND created_at < datetime('now', '-24 hours')")
        deleted = self.cursor.rowcount
        self.connection.commit()
        
        return deleted
           
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

class settingsDBOperations():
# *********************************************************************** #
# Konstruktor
# *********************************************************************** #
    def __init__(self):
        
        self.connectToDatabase("finanzapp.db") # Standard Datenbank

    def connectToDatabase(self, DB_NAME):

        self.connection = sqlite3.connect(DB_NAME)
        self.cursor = self.connection.cursor()
        
# *********************************************************************** #
# Categories
# *********************************************************************** #

    # *********************************************************************** #
    # Read
    # *********************************************************************** #
    def getCategoriesForUserId(self, user_id):
        self.cursor.execute("SELECT id, name, color FROM categories WHERE user_id = ?", (int(user_id),))
        return [{"id": row[0], "name": row[1], "color": row[2]} for row in self.cursor.fetchall()]

    def getCategoryById(self, category_id):
        self.cursor.execute("SELECT id, name, color FROM categories WHERE id = ?", (int(category_id),))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1], "color": row[2]}

    # *********************************************************************** #
    # Write
    # *********************************************************************** #    
    def createNewCategorieForUserId(self, categorie_name, categorie_color, user_id):
        self.cursor.execute("INSERT INTO categories (name, color, user_id) VALUES(?,?,?)", (str(categorie_name), str(categorie_color), int(user_id)))
        self.connection.commit()
        
    def updateCategorieEntry(self, categorie_name, categorie_color, categorie_id):
        self.cursor.execute("UPDATE categories SET name = ?, color = ? WHERE id = ?", (str(categorie_name), str(categorie_color), int(categorie_id)))
        self.connection.commit()
    
    def deleteFromCategories(self, categorie_id):
        self.cursor.execute("DELETE FROM categories WHERE id = ?", (int(categorie_id),))
        self.connection.commit()

if __name__ == "__main__":

    Dataprovider = expensePlannerDBOperations()
    Dataprovider.doUpdateExpensePlannerEntry(1, 111, "Test", 7, 9, 2026, 331, 8, ["testTag2", "TestTag"])
    


    
