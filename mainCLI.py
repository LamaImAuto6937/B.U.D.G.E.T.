import DatabaseOperationClass
import os

#To-Do: Fix change Month Bug (ChangeMonth not working correctly) 
#       Erledig: Build summary Function which shows all stats of the current months expenses (Verfügbares Geld | Ausgegebenes Geld | Prozent d. verfügbaren geldes)




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

                userOption = str(input(f"Please select mode:\n1) Add Expense \n2) Show all expenses (in the selected month) \n3) Change month \nQ) Quit \n"))
                clearScreen()
                BudgetPlaner = DatabaseOperationClass.Budget()

                match userOption.upper():
                    
                    # Add Expense
                    case "1":

                        while True:

                            print(f"Current Selected Month: {BudgetPlaner.month}")

                            userOptionBetrag = float(input(f"Money amount: "))
                            userOptionBezeichnung = str(input(f"Name Expense: "))

                            userOption = str(input(f"Is the following information correct? (y/n) \n Amount: {userOptionBetrag} € | {userOptionBezeichnung}  "))
                            clearScreen()

                            match userOption.upper():

                                case "Y":

                                    BudgetPlaner.doAppendToTable(userOptionBetrag, userOptionBezeichnung)
                                    break

                                case "N":

                                    print("Please correct your Statements!")

                    # Show all expenses in the selected month (last tbd)
                    case "2":
                        
                        

                        print("\n-/-/-/-/-/-/-/-/-/-/-/-/-/\n")
                        BudgetPlaner.doExpenseSummaryForCLI()
                        print("\n-/-/-/-/-/-/-/-/-/-/-/-/-/")
                        BudgetPlaner.doExtendedExpenseInfoForCLI()
                        print("-/-/-/-/-/-/-/-/-/-/-/-/-/\n")

                    # Change current selcted Month
                    case "3":
                        
                        while True:

                            print(f"Current Selected Month: {BudgetPlaner.month}")
                            userOptionChangeMonth = int(input(f"Please select a month: \nJanuary (1)\nFebruary (2)\nMarch (3)\nApril (4)\nMay (5)\nJune (6)\nJuly (7)\nAugust (8)\nSeptember (9)\nOctober (10)\nNovember (11)\nDecember (12)\n"))
                            monthArray = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" ]
                            clearScreen()

                            try:
                                userOption = str(input(f"Is the following information correct? (y/n)\nSelected Month: {userOptionChangeMonth} | {monthArray[userOptionChangeMonth-1]} "))
                            except:
                                print("ERROR userOptionChangeMonth")

                            match userOption.upper():

                                case "Y":
                                        
                                    BudgetPlaner.month = userOptionChangeMonth
                                    break

                                case "N":

                                    print("Please correct your Statements!")

                    case "Q":

                        break
        # Coming soon...
        case "2":
            
            #tbd implementation Available Budget Planer
            pass
        
        case _:
            
            print(f"Your option [{userOption}] is not valid!\nPlease try again")