

if __name__ == "__main__":
    
    print(f"Welcome to B.U.D.G.E.T.! \n Please select a Option!")
    #Select Option 1 
    userOption1 = str(input(f"1) Budget Planer \n2) Available Budget Planer"))
    
    match userOption1:
        
        case "1":
            
            #tbd implementation Budget Planer
            pass
        
        case "2":
            
            #tbd implementation Available Budget Planer
            pass
        
        case _:
            
            print(f"Your option [{userOption1}] is not valid!\nPlease try again")