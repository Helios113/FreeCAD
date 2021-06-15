## \addtogroup FEM
#  @{
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
import FreeCAD


"""
Document object visible in the tree-view.
Implemented in python via a document proxy and view proxy.
"""

def create(doc, name="MoFEMSolver"):
    return femutils.createObject(
        doc, name, Proxy, ViewProxy)

# Types of supported analysis
# For MoFEM these are:
#TODO get all analysis tipes
# for not just do linear elastic
ANALYSIS_TYPES = ["elastic"]


class Proxy(solverbase.Proxy):
    """Proxy for FemSolverMoFEM
    Define the parameters for anaysis
    
    """

    Type = "FEM::SolverMoFEM" # Name of command which is called
                              # Has to be the same as in GUI/workbench.cpp

    # Ad the properties needed to solve the mesh

    def __init__(self, obj):
        super(Proxy, self).__init__(obj)
        ccx_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/MoFEM")
        add_attributes(obj)

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


def add_attributes(obj):
    obj.addProperty(
        "App::PropertyEnumeration",
        "AnalysisType",
        "Fem",
        "Type of the analysis"
    )
    obj.AnalysisType = ANALYSIS_TYPES

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "IterationsThermoMechMaximum",
        "Fem",
        "Maximum iterations"
    )



class ViewProxy(solverbase.ViewProxy):
    """Proxy for FemSolverMoFEMs View Provider."""

    def getIcon(self):
        return ":/icons/FEM_SolverMoFEM.svg"

##  @}
