     
import html


class Helper():
    
    def generateHash(self, data_string):
        from werkzeug.security import generate_password_hash
        
        hashed_data = generate_password_hash(data_string)
        return hashed_data

    def validateHash(self, input_data, stored_hash):
        from werkzeug.security import check_password_hash
        
        return check_password_hash(stored_hash, input_data)
    
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
        
    def __init__(self, DataProviderClass, Helper, SECRET_KEY):
        from itsdangerous import URLSafeTimedSerializer
        
        self.DataProvider = DataProviderClass
        self.HelperClass  = Helper
        self.serializer = URLSafeTimedSerializer(SECRET_KEY)

    def procValidateLogin(self, username, password):
        # Prüft, ob die Kombination aus Passwort und Username vorhanden ist und gibt die user_id und den state aus 
        # Ebenfalls wird geprüft, ob das Konto verifiziert ist, falls nicht wird ebenfalls false zurückgegeben
        # (User gibt es (true) user gibt es nicht (false))

        user = self.DataProvider.getUserByUsernameOrEmail(username)
        
        if not user:
            return None, False
        
        from werkzeug.security import check_password_hash
        
        if check_password_hash(user[1], password):
            if self.DataProvider.getValidationStateFromUsers(user[0])[0] == 1:
                return user[0], True
            else:
                return None, False
        
        return None, False
            
    def procCreateNewUser(self, username, password, email):
        # Erstellt einen neuen Benutzer in der users Tabelle. 
        # Falls es den Username bereits gibt, wird False ausgegeben, sonst True
        
        # Prüfen, ob der Username bereits in Benutzung ist
            userUsernameRow = self.DataProvider.getAllUsernamesFromUsers()
            
            if username in userUsernameRow:
                
                return False
            
            # Hashed das passwort damit es später in die Datenbank geschrieben werden kann
            hashed_password = self.HelperClass.generateHash(password)
            
            # Schreibt die Daten in die user Datenbank
            self.DataProvider.doAppendToUsers(str(username), str(hashed_password), str(email))
            
            return True
    
    def sentResetPasswordEmail(self, receiver_email, reset_token):

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os

        sender = os.getenv("SMTP_MAIL_SENDER")
        receiver = receiver_email

        # Plain Text Version
        text = f"""
    Hallo,

    du hast ein Passwort-Reset angefordert.

    Dein neues Passwort lautet:
    {reset_token}

    Bitte ändere dieses Passwort so schnell wie möglich.

    Viele Grüße
    Dein B.U.D.G.E.T. Team
    """

        # HTML Version
        with open("templates/components/pwResetMail.html", "r", encoding="utf-8") as file:
            html = file.read()
        html = html.replace("{{reset_token}}", reset_token)
        
        # Multipart Message
        message = MIMEMultipart("alternative")
        message["Subject"] = "B.U.D.G.E.T. - Passwort zurücksetzen"
        message["From"] = sender
        message["To"] = receiver

        # Beide Versionen anhängen
        message.attach(MIMEText(text, "plain", "utf-8"))
        message.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(
            os.getenv("SMTP_MAIL_SERVER"),
            int(os.getenv("SMTP_MAIL_PORT"))
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                os.getenv("SMTP_MAIL_USER"),
                os.getenv("SMTP_MAIL_PASSWORD")
            )

            server.sendmail(
                from_addr=sender,
                to_addrs=receiver,
                msg=message.as_string()
            )

        print("Passwort Reset Email gesendet an:", receiver_email)

    def sendVerficationEmail(self, receiver_email, verification_url):
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os

        sender = os.getenv("SMTP_MAIL_SENDER")
        receiver = receiver_email

        # Plain Text Version
        text = f"""
    Hallo,
    
    du hast dich erfolgreich bei B.U.D.G.E.T. registriert!
    Bitte verifiziere deine E-Mail-Adresse und aktiviere dein Konto mit dem folgenden Link:
    {verification_url}

    Viele Grüße
    Dein B.U.D.G.E.T. Team
    """

        # HTML Version
        with open("templates/components/verificationMail.html", "r", encoding="utf-8") as file:
            html = file.read()
        html = html.replace("{{verification_url}}", verification_url)
        
        # Multipart Message
        message = MIMEMultipart("alternative")
        message["Subject"] = "B.U.D.G.E.T. - E-Mail-Verifizierung"
        message["From"] = sender
        message["To"] = receiver

        # Beide Versionen anhängen
        message.attach(MIMEText(text, "plain", "utf-8"))
        message.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(
            os.getenv("SMTP_MAIL_SERVER"),
            int(os.getenv("SMTP_MAIL_PORT"))
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                os.getenv("SMTP_MAIL_USER"),
                os.getenv("SMTP_MAIL_PASSWORD")
            )

            server.sendmail(
                from_addr=sender,
                to_addrs=receiver,
                msg=message.as_string()
            )

        print("Verifizierungs-Email gesendet an:", receiver_email)
        
    def generate_verification_token(self, email):
        return self.serializer.dumps(email, salt='email-confirmation-salt')
    
    def confirm_verification_token(self, token, expiration=86400):
        try:
            email = self.serializer.loads(token, salt='email-confirmation-salt', max_age=expiration)
            return email
        
        except Exception:
            return None
        
        
           
class SavingPlan():

    def __init__(self, HelperClass, savingPlanDBOperationsClass):

        self.Dataprovider = savingPlanDBOperationsClass
        self.Helper  = HelperClass

    def procCalculateSavedAmount(self, plan_id):

        deposit, expense = self.Helper.procSumList(self.Dataprovider.getSavings(plan_id)), self.Helper.procSumList(self.Dataprovider.getExpenses(plan_id))
        return ( deposit - expense )
        


if __name__ == "__main__":
    
    from DatabaseOperationClasses import userDBOperations
    import os, random, hashlib
    email = "stadlerbenny@gmail.com"
    
    DataProvider = userDBOperations()
    helperObject = Helper()
    loginObject = loginClass(DataProvider, helperObject)
    
    user_id = DataProvider.getUserByUsernameOrEmail(email)[0]
    
    if not user_id:
        print("Nope")
    else:
        token = hashlib.sha512(os.urandom(16) + str(random.randint(0,10000)).encode('utf-8')).hexdigest()
        DataProvider.doUpdateCredentialsPassword(user_id, helperObject.generateHash(token))
        loginObject.sentResetPasswordEmail(email, token)


    

    

        
