import budget
import os

if __name__ == "__main__":
    
    print(f"Welcome to B.U.D.G.E.T.! \n Please select a Option!")
    #Select Option 1 
    userOption = str(input(f"1) Budget Planer \n2) Available Budget Planer\n"))
    os.system("cls")
    
    match userOption:
        
        # Utilisation of Budget Class
        case "1":
            
            while True:

                userOption = str(input(f"Please select mode:\n1) Add Expense \n2) Show all expenses (in the selected month) \n3) Change month \nQ) Quit \n"))
                os.system("cls")
                BudgetPlaner = budget.Budget()

                match userOption.upper():
                    
                    # Add Expense
                    case "1":

                        print(f"Current Selected Month: ")
                        
                        while True:

                            userOptionBetrag = int(input(f"Money amount: "))
                            userOptionBezeichnung = str(input(f"Name Expense: "))

                            userOption = str(input(f"Is the following information correct? (y/n) \n Amount: {userOptionBetrag} € | {userOptionBezeichnung}  "))
                            os.system("cls")

                            match userOption.upper():

                                case "Y":

                                    BudgetPlaner.doAppendToTable(userOptionBetrag, userOptionBezeichnung)
                                    break

                                case "N":

                                    print("Please correct your Statements!")

                    # Show all expenses in the selected month (last tbd)
                    case "2":
                        
                        print("\n-/-/-/-/-/-/-/-/-/-/-/-/-/\n")
                        BudgetPlaner.doAusgabe()
                        print("\n-/-/-/-/-/-/-/-/-/-/-/-/-/\n")
            
                    # Quit
                    case "Q":

                        break
        # Coming soon...
        case "2":
            
            #tbd implementation Available Budget Planer
            pass
        
        case _:
            
            print(f"Your option [{userOption}] is not valid!\nPlease try again")