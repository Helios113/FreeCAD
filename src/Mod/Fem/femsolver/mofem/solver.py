
from . import tasks
from .equations import elasticity
from .equations import electrostatic
from .equations import flow
from .equations import flux
from .equations import electricforce
from .equations import heat
from .. import run
from .. import solverbase
from femtools import femutils


def create(doc, name="MoFEMSOlver"):
    return femutils.createObject(
        doc, name, Proxy, ViewProxy)


class Proxy(solverbase.Proxy):
    """Proxy for FemSolverElmers Document Object."""
    # Proxy for FemSolverMo

    #Type = "Fem::SolverElmer"
    Type = "FEM::SolverMo"

    _EQUATIONS = {
        "Heat": heat,
        "Elasticity": elasticity,
        "Electrostatic": electrostatic,
        "Flux": flux,
        "Electricforce": electricforce,
        "Flow": flow,
    }

    def __init__(self, obj):
        super(Proxy, self).__init__(obj)

        obj.addProperty(
            "App::PropertyInteger",
            "SteadyStateMaxIterations",
            "Steady State",
            ""
        )
        obj.SteadyStateMaxIterations = 1

        obj.addProperty(
            "App::PropertyInteger",
            "SteadyStateMinIterations",
            "Steady State",
            ""
        )
        obj.SteadyStateMinIterations = 0

        obj.addProperty(
            "App::PropertyLink",
            "ElmerResult",
            "Base",
            "",
            4 | 8
        )

        obj.addProperty(
            "App::PropertyLink",
            "ElmerOutput",
            "Base",
            "",
            4 | 8
        )

    def createMachine(self, obj, directory, testmode=False):
        return run.Machine(
            solver=obj, directory=directory,
            check=tasks.Check(),
            prepare=tasks.Prepare(),
            solve=tasks.Solve(),
            results=tasks.Results(),
            testmode=testmode)

    def createEquation(self, doc, eqId):
        return self._EQUATIONS[eqId].create(doc)

    def isSupported(self, eqId):
        return eqId in self._EQUATIONS


class ViewProxy(solverbase.ViewProxy):
    """Proxy for FemSolverMos View Provider."""

    def getIcon(self):
        return ":/icons/FEM_SolverMo.svg"

##  @}
