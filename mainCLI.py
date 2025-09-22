from generalOperationClass import GeneralOperations
from DatabaseOperationClass import DatabaseOperations
import os

#To-Do: Fix change Month Bug (ChangeMonth not working correctly) 
#       Erledig: Build summary Function which shows all stats of the current months expenses (Verfügbares Geld | Ausgegebenes Geld | Prozent d. verfügbaren geldes)

DataProvider = DatabaseOperations()
generalOperationClass = GeneralOperations(DataProvider)


def clearScreen():
    try:
        os.system("clear")
        os.system("cls")
    except:
        pass

if __name__ == "__main__":
    
    print(f"Welcome to B.U.D.G.E.T.! \n Please select a Option!")
    #Select Option 1 
    userOption = str(input(f"1) Budget Planer \n2) Available Budget Planer\n"))
    clearScreen()
    
    match userOption:
        
        # Utilisation of Budget Class
        case "1":
            
            while True:

                userOption = str(input(f"Please select mode:\n1) Add Expense \n2) Show all expenses (in the selected month) \n3) Change Date \nQ) Quit \n"))
                clearScreen()

                match userOption.upper():
                    
                    # Add Expense
                    case "1":

                        while True:

                            print(f"Current Selected Month: {generalOperationClass.month}")

                            userOptionBetrag = float(input(f"Money amount: "))
                            userOptionBezeichnung = str(input(f"Name Expense: "))

                            userOption = str(input(f"Is the following information correct? (y/n) \n Amount: {userOptionBetrag} € | {userOptionBezeichnung}  "))
                            clearScreen()

                            match userOption.upper():

                                case "Y":

                                    DataProvider.doAppendToTable(generalOperationClass.day, generalOperationClass.month, generalOperationClass.year, userOptionBetrag, userOptionBezeichnung)
                                    break

                                case "N":

                                    print("Please correct your Statements!")

                    # Show all expenses in the selected month (last tbd)
                    case "2":
                        
                        

                        print("\n-/-/-/-/-/-/-/-/-/-/-/-/-/\n")
                        generalOperationClass.doExpenseSummaryForCLI()
                        print("\n-/-/-/-/-/-/-/-/-/-/-/-/-/")
                        generalOperationClass.doExtendedExpenseInfoForCLI()
                        print("-/-/-/-/-/-/-/-/-/-/-/-/-/\n")

                    # Change current selected Date
                    case "3":
                        
                        while True:
                            
                            try:
                                
                                userOptionChangeDate = str(input(f"Current Selected: Month: {generalOperationClass.month} | Current Selected Year: {generalOperationClass.year} \n1) Change Month \n2) Change Year \nQ) Quit\n"))
                                clearScreen()
                            
                        
                                match userOptionChangeDate.upper():
                                    
                                    case "1":
                                        # Change Month
                                        while True:
                                            
                                            print(f"Current Selected Month: {generalOperationClass.month}")
                                            userOptionChangeMonth = int(input(f"Please select a month: \nJanuary (1)\nFebruary (2)\nMarch (3)\nApril (4)\nMay (5)\nJune (6)\nJuly (7)\nAugust (8)\nSeptember (9)\nOctober (10)\nNovember (11)\nDecember (12)\nQuit (Q)\n"))
                                            clearScreen()
                                            monthArray = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" ]
                                            clearScreen()

                                            try:
                                                userOption = str(input(f"Is the following information correct? (y/n)\nSelected Month: {userOptionChangeMonth} | {monthArray[userOptionChangeMonth-1]} "))
                                            except:
                                                print("ERROR userOptionChangeMonth")

                                            match userOption.upper():

                                                case "Y":
                                                        
                                                    generalOperationClass.month = userOptionChangeMonth
                                                    break

                                                case "N":

                                                    print("Please correct your Statements!")

                                                case "Q":
                                                    
                                                    break
                                    
                                    case "2":
                                        # Change Year
                                        while True:
                                            
                                            print(f"Current Selected Year: {generalOperationClass.year}")
                                            
                                            userOptionChangeYear = int(input(f"Select a year:  "))
                                            clearScreen()
                                            
                                            try:
                                                userOption = str(input(f"Is the following information correct? (y/n)\nSelected Year: {userOptionChangeYear}  "))
                                                clearScreen()
                                            except:
                                                print("ERROR userOptionChangeYear")

                                            match userOption.upper():

                                                case "Y":
                                                        
                                                    generalOperationClass.year = userOptionChangeYear
                                                    break

                                                case "N":

                                                    print("Please correct your Statements!")

                                                case "Q":
                                                    
                                                    break
                                    
                                    case "Q":
                                        
                                        break
                                        
                                    
                                                    
                            except:
                                print("ERROR changeDate")               


                    case "Q":

                        break
        # Available Budget Planer
        case "2":
            
            while True:
                
                try:
                    
                    userInputBudgetPlanerOption = str(input(f"1) Show current Revenue/Expense Balance \n2) Edit current settings \nQ) Quit \n"))
                    clearScreen()
                    
                except:
                    
                    print("ERROR Available Budget Planer")
                
                match userInputBudgetPlanerOption.upper():
                    
                    # Show current Revenue/Expenese Balance
                    case "1":
                        
                        pass
                    
                    # Edit current settings
                    case "2":
                        
                        while True:
                            
                            try:
                                userInputBudgetPlanerEditCurrentSettings = str(input(f"1) Edit Revenue \n2) Edit Expenses \nQ) Quit"))
                                clearScreen()
                            except:
                                print("ERROR userInputBudgetPlanerEditCurrentSettings")
                            
                            match userInputBudgetPlanerEditCurrentSettings.upper():
                                
                                # Edit Revenue
                                case "1":
                                    
                                    userInputBudgetPlanerEditRevenue = str(input(f"1) Add Revenue Entry \n 2) Remove Revenue Entry \n Q) Quit"))
                                    clearScreen()
                                    
                                    match userInputBudgetPlanerEditRevenue.upper():
                                        
                                        # Add Revenue Entry
                                        case "1":
                                            
                                            while True:
                                                
                                                try:
                                                    
                                                    
                                                    userInputAddRevenueAmount = float(input(f"Enter Amount in euro: "))
                                                    userInputAddRevenueDescription = str(input(f"Enter Description for your Entry: "))
                                                    clearScreen()
                                                    userInputAddRevenueConfirmation = str(input(f"You entered the following information: \n Amount: {userInputAddRevenueAmount} | Description: {userInputAddRevenueDescription} \nIst this correct? (y/n): "))
                                                    
                                                    match userInputAddRevenueConfirmation.upper():
                                                        
                                                        case 'Y':
                                                            
                                                            DataProvider.doAppendToMonthlyBudget(userInputAddRevenueAmount, userInputAddRevenueDescription, 'REV')
                                                            break
                                                        
                                                        case 'N':
                                                            
                                                            print(f"Please correct your Statements! ")
                                                            clearScreen()
                                                    
                                                    
                                                except:
                                                    print("ERROR userInputAddRevenue")
                                        # Remove Revenue Entry
                                        case "2":
                                            
                                            userInputBudgetPlanerEditRevenue = str(input(f""))
                                        
                                        # Quit
                                        case "Q":
                                            
                                            break
                                
                                # Edit Expenses   
                                case "2":
                                    
                                    userInputBudgetPlanerEditExpenses = str(input(f"1) Add Expense Entry \n 2) Remove Expense Entry \n Q) Quit"))
                                    
                                    match userInputBudgetPlanerEditExpenses.upper():
                                        
                                        # Add Expense Entry
                                        case "1":
                                            
                                            pass
                                        
                                        # Remove Expense Entry
                                        case "2":
                                            
                                            pass
                                        
                                        # Quit
                                        case "Q":
                                            
                                            break
                                
                                # Quit    
                                case "Q":
                                    
                                    break
                                    
                    
                    # Quit
                    case "Q":
                        
                        break
                        
                
                
            
        
        case _:
            
            print(f"Your option [{userOption}] is not valid!\nPlease try again")