"""
A class to perform Approximate Bayesian Computation Sequential Monte Carlo which simulates observations
from a posterior distribution without the use of liklihoods.
"""
import os
import logging
import numpy
import multiprocessing
import zipfile 
import shutil 
from datetime import datetime
from sandbox.util.Util import Util 
from sandbox.util.Parameter import Parameter 

def loadThetaArray(N, thetaDir, t): 
    """
    Load the thetas from a particular directory. 
    """
    currentThetas = [] 
    dists = []
        
    for i in range(N): 
        fileName = thetaDir + "theta_t="+str(t)+"_"+str(i)+".npz"
        if os.path.exists(fileName):   
            try: 
                data = numpy.load(fileName)
                currentThetas.append(data["arr_0"])
                dists.append(data["arr_1"])
            except IOError as e: 
                logging.debug("Error whilst loading: " + str(e))
            except zipfile.BadZipfile: 
                logging.warn("BadZipfile error whilst loading " + fileName)
                badFileDir = thetaDir + "debug/"
                if not os.path.exists(badFileDir): 
                    os.mkdir(badFileDir)
                shutil.copy(fileName, badFileDir)
                os.remove(fileName)
                logging.warn("Moved " + fileName + " to " + badFileDir)
            except:
                logging.error("Unexpected error whilst loading " + fileName)
                raise
            
    return numpy.array(currentThetas), numpy.array(dists)

def runModel(args):
    theta, createModel, t, epsilon, N, thetaDir = args     
    currentTheta = loadThetaArray(N, thetaDir, t)[0].tolist()
    
    if len(currentTheta) < N:     
        logging.debug("Using theta value : " + str(theta)) 
        model = createModel(t)
        model.setParams(theta)
        model.simulate()
        dist = model.objective() 
        del model 
        
        currentTheta = loadThetaArray(N, thetaDir, t)[0].tolist()                
        
        if dist <= epsilon and len(currentTheta) < N:    
            logging.debug("Accepting " + str(len(currentTheta)) + " pop. " + str(t) + " " + str(theta)  + " dist=" + str(dist))
            fileName = thetaDir + "theta_t="+str(t)+"_"+str(len(currentTheta)) + ".npz" 
            
            distArray = numpy.array([dist])   

            try:
               with open(fileName, "w") as fileObj:
                   numpy.savez(fileObj, theta, distArray)
            except IOError:
               logging.debug("File IOError (probably a collision) occured with " + fileName)           
            
            currentTheta.append(theta)
            
            return 1, 1
            
        return 1, 0 
    return 0, 0 
            
class ABCSMC(object):
    def __init__(self, epsilonArray, createModel, paramsObj, thetaDir, autoEpsilon=False, minEpsilon=0.1, thetaUniformChoice=False):
        """
        Create a multiprocessing SMCABC object with the given arguments. The aim
        is to estimate a posterior pi(theta| x) propto f(x|theta) pi(theta) without
        requiring an explicit form of the likelihood. Here, theta is a set of
        parameters and x is a data observation. The algorithm can be run in a
        multiprocessing system.
        
        :param epsilonArray: an array of successively smaller minimum distances
        :type epsilonArray: `numpy.ndarray` 
   
        :param createModel: A function to create a new stochastic model. The model must have a distance function with returns the distance to the target theta. 

        :param paramsObj: An object which stores information about the parameters of the model 
        
        :param thetaDir: The directory to store theta values 
        
        :param autoEpsilon: If autoEpsilon is true then the first value in epsilonArray is used as epsilon, and epsilonArray[t+1] is computed as the min dist for particles at t
        
        :param minEpsilon: This is the minumum value of epsilon allowed, and we stop if it goes beyond this number 
        """
        dt = datetime.now()
        numpy.random.seed(dt.microsecond)
        self.epsilonArray = epsilonArray
        self.createModel = createModel
        self.abcParams = paramsObj 
        self.thetaDir = thetaDir 
        self.autoEpsilon = autoEpsilon
        self.minEpsilon = minEpsilon

        #Number of particles
        self.T = epsilonArray.shape[0]
        #Size of population
        self.N = 10
        self.numProcesses = multiprocessing.cpu_count() 
        self.batchSize = self.numProcesses*2
        self.numRuns = numpy.zeros(self.T) 
        self.numAccepts = numpy.zeros(self.T)
        self.maxRuns = 1000
        self.pertScale = 2.0
        
        self.thetaUniformChoice = thetaUniformChoice

    def setPosteriorSampleSize(self, posteriorSampleSize):
        """
        Set the sample size of the posterior distribution (population size).
        
        :param posteriorSampleSize: The size of the population 
        :type posteriorSampleSize: `int`
        """
        Parameter.checkInt(posteriorSampleSize, 0, numpy.float('inf'))
        self.N = posteriorSampleSize

    def loadThetas(self, t): 
        """
        Load all thetas saved for particle t. 
        """
        return loadThetaArray(self.N, self.thetaDir, t)
        
    def findThetas(self, lastTheta, lastWeights, t): 
        """
        Find a theta to accept. 
        """
        tempTheta = self.abcParams.sampleParams()
        currentTheta, dists = self.loadThetas(t)
        
        while len(currentTheta) < self.N:
            paramList = []   
            
            for i in range(self.batchSize):             
                if t == 0:
                    tempTheta = self.abcParams.sampleParams()
                    paramList.append((tempTheta.copy(), self.createModel, t, self.epsilonArray[t], self.N, self.thetaDir))
                else:  
                    while True:
                        if self.thetaUniformChoice: 
                            tempTheta = lastTheta[numpy.random.randint(self.N), :]   
                        else: 
                            tempTheta = lastTheta[Util.randomChoice(lastWeights)[0], :]
                        tempTheta = self.abcParams.perturbationKernel(tempTheta, numpy.std(lastTheta, 0)/self.pertScale)
                        if self.abcParams.priorDensity(tempTheta) != 0: 
                            break 
                    paramList.append((tempTheta.copy(), self.createModel, t, self.epsilonArray[t], self.N, self.thetaDir))

            pool = multiprocessing.Pool(processes=self.numProcesses)               
            resultsIterator = pool.map(runModel, paramList)     
            #resultsIterator = map(runModel, paramList)     

            for result in resultsIterator: 
                self.numRuns[t] += result[0]
                self.numAccepts[t] += result[1]
            
            if self.numRuns[t] >= self.maxRuns:
                logging.debug("Maximum number of runs exceeded.")
                break 
            
            currentTheta, dists = self.loadThetas(t)                 
            pool.terminate()
            
        if self.autoEpsilon and t!=self.T-1:
            self.epsilonArray[t+1] = numpy.mean(dists)
            logging.debug("Found new epsilon: " + str(self.epsilonArray[0:t+2]))
            
        logging.debug("Num accepts: " + str(self.numAccepts))
        logging.debug("Num runs: " + str(self.numRuns))
        logging.debug("Acceptance rate: " + str(self.numAccepts/(self.numRuns + numpy.array(self.numRuns==0, numpy.int))))
              
        return currentTheta

    def run(self):
        """
        Make the estimation for a set of parameters theta close to the summary
        statistics S for a real dataset. 
        """
        logging.debug("Parent PID: " + str(os.getppid()) + " Child PID: " + str(os.getpid()))
        currentTheta = []
        currentWeights = numpy.zeros(self.N)
        
        os.system('taskset -p 0xffffffff %d' % os.getpid())

        for t in range(self.T):
            logging.debug("Particle number : " + str(t))
            
            if self.autoEpsilon and t!=self.T-1 and self.epsilonArray[t] < self.minEpsilon:
                logging.debug("Epsilon threshold became too small")
                break             
            
            lastTheta = currentTheta
            lastWeights = currentWeights
            currentWeights = numpy.zeros(self.N)
            
            if t != 0: 
                logging.debug("Perturbation sigma for t = " + str(t) +  " : " + str(numpy.std(lastTheta, 0)/self.pertScale))            

            currentTheta = self.findThetas(lastTheta, lastWeights, t)

            if len(currentTheta) != self.N: 
                break 
                   
            for i in range(self.N):
                theta = currentTheta[i]                
                
                if t == 0:
                    currentWeights[i] = 1
                else:
                    normalisation = 0
                    for j in range(self.N):
                        normalisation += lastWeights[j]*self.abcParams.perturbationKernelDensity(lastTheta[j], theta, numpy.std(lastTheta, 0)/self.pertScale)
                    
                    if abs(normalisation) >= 10**-9:     
                        currentWeights[i] = self.abcParams.priorDensity(theta)/normalisation
            
            currentWeights = currentWeights/numpy.sum(currentWeights)
            logging.debug("ABC weights are " + str(currentWeights))
        
        logging.debug("Finished ABC procedure") 
        
        return currentTheta 
        
    def setNumProcesses(self, numProcesses): 
        self.numProcesses = numProcesses 
