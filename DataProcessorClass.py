import DatabaseOperationClass

class DataProcessor():

    def __init__(self):
        pass


    def calculateMonthlyExpenses(self):

        for row in self.rows:

            self.monthlyExpenses += row[0]