import sqlite3

db = sqlite3.connect("finanzapp.db")
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS Budget ( float betragAusgabe)""")

class Data_Provider(self):
    
    def __init__(self):
        pass
    


class Budget():
    
    # Constructor: Bevor das Objekt erzeugt wird, wird das hier aufgerufen 
    
    #Note: The self parameter is a reference to the current instance of the 
    #      class, and is used to access variables that belong to the class.
    def __init__(self):
        pass
    
    def doAusgabe(self):
        
        #tbd Datenbank aufruf
        
        
    