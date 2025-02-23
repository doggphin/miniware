class CorrectionProblem(Exception):
    def get_problem(self) -> str:
        return str(self.args[0])