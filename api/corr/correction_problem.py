class GenericProblem(Exception):
    def get_problem(self) -> str:
        return str(self.args[0])
    

#class UnexpectedExtension(Exception):
#    def get_problem(self) -> str:
#        got_
#       return(self.args[0])
