
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


        validation_phase = self.DataProvider.getAusgabenFromUsers(username, password)

        if not validation_phase:

            return None, False
        
        else:

            return validation_phase, True
        