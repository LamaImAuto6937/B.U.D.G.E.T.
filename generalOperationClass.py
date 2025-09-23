
class GeneralOperations():
    
    def __init__(self, DataProviderClass):
        
        self.DataProvider = DataProviderClass

        # Helper Konstanten
        self.initializeCurrentDate() # Initialisiert heutiges Datum
        self.monthlyBudget = self.procCalculateMonthlyBudget()
    
    
    
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


    def doMonthlyBudgetOverviewForCLI(self):
        pass
    
    
    # *********************************************************************** #
    
    # *********************************************************************** #
    #                          Processor Methoden                             #
    # *********************************************************************** # 
    
    
    def procCalculateMonthlyExpenses(self):
        
        self.rows = self.DataProvider.getAusgabenFromBudget(self.month, self.day)
        self.monthlyExpenses = 0
        
        for row in self.rows:

            self.monthlyExpenses += row[0]
        
        return self.monthlyExpenses
    
    def procCalculateMonthlyBudget(self):
        
        self.rows = self.DataProvider.getAusgabenFromMonthlyBudget()
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