"""Learn a finite model from a supplied program path using the R11 learner."""
from .path_program import PathProgram
from kairo_r11.learn import Learner


def learn_path(program_path, protocol):
    with PathProgram(program_path) as program:
        alphabet = program.describe()

        def query(word):
            program.reset()
            return [program.step(action) for action in word]

        learner = Learner(alphabet, query, protocol)
        result = learner.run()
        result["program_path"] = str(program.path)
        result["alphabet"] = list(alphabet)
        return result
