

class GeneralOperations():
    
    def __init__(self, DataProviderClass):
        
        self.DataProvider = DataProviderClass

        # Helper Konstanten
        self.initializeCurrentDate() # Initialisiert heutiges Datum
        #self.monthlyBudget = self.procCalculateMonthlyBudget()[2]
    
    
    
    # Ermittelt das heutige Datum und gliedert es in Day/Month/Year
    def initializeCurrentDate(self):
         
        from datetime import date
         
        today = date.today()

        self.day = today.day
        self.month = today.month
        self.year = today.year
        
        
    # *********************************************************************** #
    #                           Setter Methoden                               #
    # *********************************************************************** # 


    def setMonth(self, month):
        
        self.month = month


    def setYear(self, year):
        
        self.year = year
        
        
    # *********************************************************************** # 

    # *********************************************************************** #
    #                           Getter Methoden                               #
    # *********************************************************************** # 


    def getMonthlyExpenses(self):

        return self.procCalculateMonthlyExpenses(self.month, self.day)
            

    # *********************************************************************** #

    # *********************************************************************** #
    #                         CLI Helper Methoden                             #
    # *********************************************************************** # 


    def doExpenseSummaryForCLI(self):
        
        self.rows = self.DataProvider.getAusgabenFromBudget(self.month, self.day)
        
        for row in self.rows:
            print(f"Betrag: {row[0]} | Bezeichnung: {row[1]} | Datum: {row[2]}.{row[3]}.{row[4]}")


    def doExtendedExpenseInfoForCLI(self):
        self.monthlyExpenses = self.procCalculateMonthlyExpenses()
        
        print(f''' 
Ausgegeben: {self.monthlyExpenses} | Verfügbar: {self.monthlyBudget} | % : {(self.monthlyExpenses/self.monthlyBudget)*100} % | Angespart: {self.monthlyBudget-self.monthlyExpenses}
Selektiertes Jahr: {self.year} | Selektierter Monat: {self.month}
             ''')


    # *********************************************************************** #

    # *********************************************************************** #
    #                       WebApp Helper Methoden                            #
    # *********************************************************************** # 


    def expensePlannerSummaryHelpValues(self, month, year, user_id):
        
        self.monthlyBudget = self.procCalculateMonthlyBudget(int(user_id))[2]

        monthlyExpense = self.procCalculateExpenseSummary(int(month), int(year), int(user_id))
        monthlySaved = self.monthlyBudget - monthlyExpense
        monthlyExpensePercentage = (monthlyExpense / self.monthlyBudget) * 100


        return self.monthlyBudget, monthlyExpense, monthlySaved, monthlyExpensePercentage

    # *********************************************************************** #
    
    # *********************************************************************** #
    #                          Processor Methoden                             #
    # *********************************************************************** # 
    
    
    def procCalculateMonthlyExpenses(self, user_id):
        
        self.rows = self.DataProvider.getAusgabenFromBudget(self.month, self.day, user_id)
        self.monthlyExpenses = 0
        
        for row in self.rows:

            self.monthlyExpenses += row[0]
        
        return self.monthlyExpenses
    
    def procCalculateMonthlyBudget(self, user_id):
        
        self.rows = self.DataProvider.getAusgabenFromMonthlyBudget(user_id)
        monthlyBudget = 0
        monthlyExpense = 0
        monthlyRevenue = 0
        
        for row in self.rows:
            
            match row[2]:
                
                case "REV": # Berechnet das monatliche Einkommen
                    
                    monthlyRevenue += row[0]
                    
                case "EXP": # Berechnet die monatlichen Ausgaben
                    
                    monthlyExpense += row[0]
        
        monthlyBudget = monthlyRevenue - monthlyExpense # Berechnet das monatliche Budget
                
        return monthlyRevenue, monthlyExpense, monthlyBudget
    
    def procCalculateExpenseSummary(self, month, year, user_id):
        # Berechnet die gesamtsumme aller Ausgaben im ausgewählten Zeitraum
        expenseSummaryGesamt = 0

        self.rows = self.DataProvider.getAusgabenFromExpensePlanner(month, year, user_id)

        for row in self.rows:

            expenseSummaryGesamt += row[0]

        return expenseSummaryGesamt
    
    def procValidateLogin(self, username, password):
        # Prüft, ob die Kombination aus Passwort und Username vorhanden ist und gibt die user_id und den state aus 
        # (User gibt es (true) user gibt es nicht (false))


        validation_phase = self.DataProvider.getUserIdFromUsers(username, password)

        if not validation_phase:

            return None, False
        
        else:

            return validation_phase, True
        
    def procHashData(self, data_string):
        import hashlib
        
        hashed_data = hashlib.sha512(str(data_string).encode('utf-8')).hexdigest()
        
        return hashed_data
    
    def procCreateNewUser(self, username, password):
        # Erstellt einen neuen Benutzer in der users Tabelle. 
        # Falls es den Username bereits gibt, wird False ausgegeben, sonst True
        
        # Prüfen, ob der Username bereits in Benutzung ist
        userUsernameRow = self.DataProvider.getAllUsernamesFromUsers()
        
        if username in userUsernameRow:
            
            return False
        
        
        # Hashed das passwort damit es später in die Datenbank geschrieben werden kann
        hashed_password = self.procHashData(password)
        
        # Ermittelt die UserID, damit keine Doppelt vorkommt
        userTableUserIDs = self.DataProvider.getAllUserIDsFromUsers()
        
        # Wenn noch kein User angelegt ist, soll einer mit der ID 1 angelegt werden
        if userTableUserIDs:
            user_id = max(userTableUserIDs) + 1
        else:
            user_id = 1
        
        
        # Schreibt die Daten in die user Datenbank
        self.DataProvider.doAppendToUsers(int(user_id), str(username), str(hashed_password))
        
        return True
        

if __name__ == "__main__":
    
    from DatabaseOperationClass import DatabaseOperations
    
    DataProvider = DatabaseOperations()
    ops = GeneralOperations(DataProvider)
    
    print(ops.procCreateNewUser("Test123456", "Test123"))