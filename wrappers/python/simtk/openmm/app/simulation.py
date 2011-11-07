"""
simulation.py: Provides a simplified API for running simulations.
"""
__author__ = "Peter Eastman"
__version__ = "1.0"

import simtk.openmm as mm
import simtk.unit as unit
    
class Simulation(object):
    """Simulation provides a simplified API for running simulations with OpenMM and reporting results.
    
    A Simulation ties together various objects used for running a simulation: a Topology, System,
    Integrator, and Context.  To use it, you provide the Topology, System, and Integrator, and it
    creates the Context automatically.
    
    Simulation also maintains a list of "reporter" objects that record or analyze data as the simulation
    runs, such as writing coordinates to files or displaying structures on the screen.  For example,
    the following line will cause a file called "output.pdb" to be created, and a structure written to
    it every 1000 time steps:
    
    simulation.reporters.append(PDBReporter('output.pdb', 1000))
    """
    
    def __init__(self, topology, system, integrator, platform=None, platformProperties=None):
        """Create a Simulation.
        
        Parameters:
         - topology (Topology) A Topology describing the the system to simulation
         - system (System) The OpenMM System object to simulate
         - integrator (Integrator) The OpenMM Integrator to use for simulating the System
         - platform (Platform=None) If not None, the OpenMM Platform to use
         - platformProperties (map=None) If not None, a set of platform-specific properties to pass
           to the Context's constructor
        """
        self.topology = topology
        self.system = system
        self.integrator = integrator
        self.currentStep = 0
        self.reporters = []
        if platform is None:
            self.context = mm.Context(system, integrator)
        elif platformProperties is None:
            self.context = mm.Context(system, integrator, platform)
        else:
            self.context = mm.Context(system, integrator, platform, platformProperties)
    
    def minimizeEnergy(self, tolerance=1*unit.kilojoule/unit.mole, maxIterations=0):
        """Perform a local energy minimization on the system.
        
        Parameters:
         - tolerance (energy=1*kilojoule/mole) The energy tolerance to which the system should be minimized
         - maxIterations (int=0) The maximum number of iterations to perform.  If this is 0, minimization is continued
           until the results converge without regard to how many iterations it takes.
        """
        mm.LocalEnergyMinimizer.minimize(self.context, tolerance, maxIterations)
       
    def step(self, steps):
        """Advance the simulation by integrating a specified number of time steps."""
        stepTo = self.currentStep+steps
        nextReport = [None]*len(self.reporters)
        while self.currentStep < stepTo:
            nextSteps = stepTo-self.currentStep
            anyReport = False
            for i, reporter in enumerate(self.reporters):
                nextReport[i] = reporter.describeNextReport(self)
                if nextReport[i][0] > 0 and nextReport[i][0] <= nextSteps:
                    nextSteps = nextReport[i][0]
                    anyReport = True
            self.integrator.step(nextSteps)
            self.currentStep += nextSteps
            if anyReport:
                getPositions = False
                getVelocities = False
                getForces = False
                getEnergy = False
                for reporter, next in zip(self.reporters, nextReport):
                    if next[0] == nextSteps:
                        if next[1]:
                            getPositions = True
                        if next[2]:
                            getVelocities = True
                        if next[3]:
                            getForces = True
                        if next[4]:
                            getEnergy = True
                state = self.context.getState(getPositions=getPositions, getVelocities=getVelocities, getForces=getForces, getEnergy=getEnergy, getParameters=True)
                for reporter, next in zip(self.reporters, nextReport):
                    if next[0] == nextSteps:
                        reporter.report(self, state)

