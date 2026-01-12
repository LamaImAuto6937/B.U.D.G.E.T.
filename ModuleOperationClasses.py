     
class Helper():
    
    def procHashData(self, data_string):
        import hashlib
        
        hashed_data = hashlib.sha512(str(data_string).encode('utf-8')).hexdigest()
        
        return hashed_data

    def procSumList(self, list):
        # Übergabe einer List, dessen Werte [Erste Spalte! [0]!] addiert wird und die Summe ausgegeben!
        result = 0

        for line in list:

            result += line

        return result

    def convertNestedTupleIntoList(self, tuple):
        result = []
        item = []

        for List in tuple:
            for i in List:
                item.append(i)
            result.append(item)
            item = []
        return result

class expensePlanner():
    
    def __init__(self, monthlyBudgetClass, expensePlannerDBOperationsClass, HelperClass):
        # Helper Objektreferenzen
        self.monthlyBudget = monthlyBudgetClass
        self.Dataprovider = expensePlannerDBOperationsClass
        self.Helper = HelperClass
    
    def procCalculateSaved(self, Budget, ExpensePlannerExpense):
        return ( Budget - ExpensePlannerExpense )
    
    def procCalculateExpense(self, user_id, month, year):
        return ( self.Helper.procSumList(self.Dataprovider.getBetragAusgabe(user_id, month, year)) )

    def procCalculatePercentage(self, Budget, Expense ):
        return ( Expense / Budget * 100)

    def procCheckIfBudgetIsAvailable(self, user_id, month, year):
        # Prüft, ob es bereits einen Eintrag in der setBudgetForSelectedMonth gibt
        # Es wird ein Tuple Ausgegeben: [ Wahrheitswert, Budget ]
        # Der erste Wert gibt an, ob es den Eintrag bereits in der setBudgetForSelectedMonth gibt
        # Der zweite gibt entweder das Budget aus dem Table an oder das globale Budget (monthlyBudget modul)
        
        
        savedAmount = self.Dataprovider.getBudgetFromSetBudgetForSelectedMonth(user_id, month, year)
        
        if savedAmount == None:
            
            return False, self.monthlyBudget.procCalculateBudget(self.monthlyBudget.procCalculateRevenue(user_id), self.monthlyBudget.procCalculateExpense(user_id))
        
        else:
            
            return True, savedAmount[0]
        
    def procCalculateExpenseSummary(self, month, year, user_id):
        # Berechnet die gesamtsumme aller Ausgaben im ausgewählten Zeitraum
        return self.Helper.procSumList(self.DataProvider.getBetragAusgabe(user_id, month, year))
    
class monthlyBudget():
    
    def __init__(self, HelperClass, monthlyBudgetDBOperationsClass):
        # Helper Objektreferenzen
        self.Helper = HelperClass
        self.DataProvider = monthlyBudgetDBOperationsClass


    def procCalculateMonthlyExpenses(self, user_id, month, day):
        
        expenseRows = self.DataProvider.getAusgabenFromBudget(month, day, user_id)
        monthlyExpenses = self.Helper.procSumList(expenseRows)
  
        return monthlyExpenses

    def procCalculateRevenue(self, user_id):
        revenueRows = self.DataProvider.getRevenueRows(int(user_id))
        revenueRowsIncludingDebitRates = []
        for i in revenueRows:
            revenueRowsIncludingDebitRates.append(self.procCalculateDebitRate(i[0],i[1]))
        return self.Helper.procSumList(revenueRowsIncludingDebitRates)
    
    def procCalculateExpense(self, user_id):
        expenseRows = self.DataProvider.getExpenseRows(int(user_id))
        expenseRowsIncludingDebitRates = []
        for i in expenseRows:
            expenseRowsIncludingDebitRates.append(self.procCalculateDebitRate(i[0],i[1]))
        return self.Helper.procSumList(expenseRowsIncludingDebitRates)
    
    def procCalculateBudget(self, Revenue, Expense):
        return (Revenue - Expense)
    
    def procGenerateDurationText(self, duration_in_months):

        match duration_in_months:
            case 1:
                return 'Monatlich'
            case 4:
                return 'Vierteljährlich'
            case 12:
                return 'Jährlich'
            case _:
                return f"Alle {duration_in_months} Monate"
    
    def procCalculateDebitRate(self, Budget, duration_in_months):
        return ( Budget / duration_in_months )
    
    def procCalculateYearlyRate(self, Budget, duration_in_months):
        times_a_year = 12 / duration_in_months
        return ( Budget * times_a_year )
    
class loginClass():
        
    def __init__(self, DataProviderClass, Helper):
        
        self.DataProvider = DataProviderClass
        self.HelperClass  = Helper

    def procValidateLogin(self, username, password):
        # Prüft, ob die Kombination aus Passwort und Username vorhanden ist und gibt die user_id und den state aus 
        # (User gibt es (true) user gibt es nicht (false))


            validation_phase = self.DataProvider.getUserIdFromUsers(username, password)

            if not validation_phase:

                return None, False
            
            else:

                return validation_phase, True
            
    def procCreateNewUser(self, username, password):
        # Erstellt einen neuen Benutzer in der users Tabelle. 
        # Falls es den Username bereits gibt, wird False ausgegeben, sonst True
        
        # Prüfen, ob der Username bereits in Benutzung ist
            userUsernameRow = self.DataProvider.getAllUsernamesFromUsers()
            
            if username in userUsernameRow:
                
                return False
            
            
            # Hashed das passwort damit es später in die Datenbank geschrieben werden kann
            hashed_password = self.HelperClass.procHashData(password)
            
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
    
class SavingPlan():

    def __init__(self, HelperClass, savingPlanDBOperationsClass):

        self.Dataprovider = savingPlanDBOperationsClass
        self.Helper  = HelperClass

    def procCalculateSavedAmount(self, plan_id):

        deposit, expense = self.Helper.procSumList(self.Dataprovider.getSavings(plan_id)), self.Helper.procSumList(self.Dataprovider.getExpenses(plan_id))
        return ( deposit - expense )
        


if __name__ == "__main__":
    from DatabaseOperationClasses import *
    helperops = Helper()
    dataprovider = monthlyBudgetDBOperations()
    budget = monthlyBudget(helperops, dataprovider)

    print(budget.procCalculateRevenue(1))


    

    

        
