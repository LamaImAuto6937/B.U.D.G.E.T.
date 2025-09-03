from datetime import date
import DataProcessorClass

class Helper():
    # Helper Klasse für Diverse Tätigkeiten
    # Hält unter anderem Konstanten, die für das Frontend wichtig sein könnten

     def __init__(self):
         
         self.DataProcessor = DataProcessorClass() # Data Processor Klasse

        # Konstanten
         self.budget = 1000

         self.initializeCurrentDate() 
     
     # Ermittelt das heutige Datum und gliedert es in Day/Month/Year
     def initializeCurrentDate(self):
         
         today = date.today()

         self.day = today.day()
         self.month = today.month()
         self.year = today.year()

    # *********************************************************************** #
    #                           Setter Methoden                               #
    # *********************************************************************** # 



    # *********************************************************************** # 

    # *********************************************************************** #
    #                           Getter Methoden                               #
    # *********************************************************************** # 


     def getMonthlyExpenses(self):

        return self.monthlyExpenses


    # *********************************************************************** #

    # *********************************************************************** #
    #                         CLI Helper Methoden                             #
    # *********************************************************************** # 


     def doExpenseSummaryForCLI(self):
        

        for row in self.rows:
            print(f"Betrag: {row[0]} | Bezeichnung: {row[1]} | Datum: {row[2]}.{row[3]}.{row[4]}")


     def doExtendedExpenseInfoForCLI(self):

        print(f"Ausgegeben: {self.monthlyExpenses} | Verfügbar: {self.budget} | % : {(self.monthlyExpenses/self.budget)*100} % | Angespart: {self.budget-self.monthlyExpenses}")


    # *********************************************************************** #