jmeVariations = [ "jerUp", "jerDown", "jesTotalUp", "jesTotalDown"]
metVariations = ['unclustEnUp', 'unclustEnDown']

# Standard imports
import os
import abc
from math import sqrt
import json

# StopsDilepton
from StopsDilepton.analysis.Cache import Cache
from StopsDilepton.tools.u_float import u_float
from StopsDilepton.analysis.SetupHelpers import channels

# Logging
import logging
logger = logging.getLogger(__name__)

class SystematicEstimator:
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, cacheDir=None):
        self.name = name
        self.initCache(cacheDir)
        self.isSignal = False

    def initCache(self, cacheDir):
        if cacheDir:
            self.cacheDir       = cacheDir
            try:    os.makedirs(cacheDir)
            except: pass

            cacheFileName       = os.path.join(cacheDir, self.name)
            helperCacheFileName = os.path.join(cacheDir, self.name+'_helper')

            self.cache       = Cache(cacheFileName,       verbosity=1)
            self.helperCache = Cache(helperCacheFileName, verbosity=1) if self.name.count('DD') else None
        else:
            self.cache=None
            self.helperCache=None

    # For the datadriven subclasses which often need the same getYieldFromDraw we write those yields to a cache
    def yieldFromCache(self, setup, sample, c, selectionString, weightString):
        s = (sample, c, selectionString, weightString)
        if self.helperCache and self.helperCache.contains(s):
          return self.helperCache.get(s)
        else:
          yieldFromDraw = u_float(**setup.sample[sample][c].getYieldFromDraw(selectionString, weightString))
          if self.helperCache: self.helperCache.add(s, yieldFromDraw, overwrite=True)
          return yieldFromDraw

    def uniqueKey(self, region, channel, setup):
        sysForKey = setup.sys.copy()
        sysForKey['reweight'] = 'TEMP'
        reweightKey ='["' + '", "'.join(sorted([i for i in setup.sys['reweight']])) + '"]' # little hack to preserve order of list when being dumped into json
        return region, channel, json.dumps(sysForKey, sort_keys=True).replace('"TEMP"',reweightKey), json.dumps(setup.parameters, sort_keys=True), json.dumps(setup.lumi, sort_keys=True)
        #return '_'.join([str(region), channel, json.dumps(sysForKey, sort_keys=True).replace('"TEMP"',reweightKey), json.dumps(setup.parameters, sort_keys=True), json.dumps(setup.lumi, sort_keys=True)]) # this should give one string

    def replace(self, i, r):
        try:
          if i.count('reweight'): return i.replace(r[0], r[1])
          else:                   return i
        except:                   return i

    def cachedEstimate(self, region, channel, setup, save=True, overwrite=False):
        key =  self.uniqueKey(region, channel, setup)
        if (self.cache and self.cache.contains(key)) and not overwrite:# and not (channel == 'SF' or channel == 'all') :
            res = self.cache.get(key)
            logger.debug( "Loading cached %s result for %r : %r"%(self.name, key, res) )
        elif self.cache:
            logger.debug( "Calculating %s result for %r"%(self.name, key) )
            res = self._estimate( region, channel, setup)
            _res = self.cache.add( key, res, overwrite=True)
            logger.debug( "Adding cached %s result for %r : %r" %(self.name, key, res) )
        else:
            res = self._estimate( region, channel, setup)
        return res if res > 0 else u_float(0,0)

    @abc.abstractmethod
    def _estimate(self, region, channel, setup):
        '''Estimate yield in 'region' using setup'''
        return

    def PUSystematic(self, region, channel, setup, puUpOrDown=False):
        ref  = self.cachedEstimate(region, channel, setup)

        if not puUpOrDown:
            puUpOrDown = ['VVUp','Up'] if setup.year == 2018 else ['Up','Down']

        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightPU'+puUpOrDown[0]]}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightPU'+puUpOrDown[1]]}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up,down)

    def topPtSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightTopPt']}))
        return abs((up-ref)/ref) if ref > 0 else up

    def leptonSIP3DSFSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'remove':['reweightLeptonSip3dSF']}))
        return abs((up-ref)/ref) if ref > 0 else up

    def leptonHit0SFSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'remove':['reweightLeptonHit0SF']}))
        return abs((up-ref)/ref) if ref > 0 else up

    def JERSystematic(self, region, channel, setup):
        # assigns the difference between smearing and not smearing
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jerUp'}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jerDown'}))
        return min(abs(0.5*(up+down)/ref-1.),u_float(0.95)) if ref > 0 else max(up, down)

    def JERSystematicAsym(self, region, channel, setup):
        # uses the up and down variation around the average
        # this is in fact symmetric by construction, but since we don't use smearing this is one of the possible uncertainties to use
        up   = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jerUp'}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jerDown'}))
        ref = (up+down)/2.
        if ref.val>0:
            return (down.val/ref.val), (up.val/ref.val)
        else:
            return 0,0

    def JECSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jesTotalUp'}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jesTotalDown'}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def JECSystematicAsym(self, region, channel, setup):
        up   = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jesTotalUp'}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'jesTotalDown'}))
        ref = (up+down)/2.
        if ref.val>0:
            return (down.val/ref.val), (up.val/ref.val)
        else:
            return 0,0

    def unclusteredSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'unclustEnUp'}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'unclustEnDown'}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def unclusteredSystematicAsym(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'unclustEnUp'}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'unclustEnDown'}))
        ref=(up+down)/2. ## test!!
        if ref.val>0:
            return (down.val/ref.val), (up.val/ref.val)
        else:
            return 0,0

    def leptonFSSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightLeptonFastSimSF']}))
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightLeptonFastSimSFUp']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightLeptonFastSimSFDown']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def L1PrefireSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightL1PrefireUp']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightL1PrefireDown']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def nISRSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweight_nISRUp']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweight_nISRDown']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)
    
    def btaggingSFbSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightBTag_SF_b_Up']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightBTag_SF_b_Down']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def btaggingSFlSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightBTag_SF_l_Up']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightBTag_SF_l_Down']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def btaggingSFFSSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightBTag_SF_FS_Up']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightBTag_SF_FS_Down']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def leptonSFSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightLeptonSFUp']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightLeptonSFDown']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def triggerSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        up   = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightDilepTriggerUp']}))
        down = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['reweightDilepTriggerDown']}))
        return abs(0.5*(up-down)/ref) if ref > 0 else max(up, down)

    def fastSimMETSystematic(self, region, channel, setup):
        ref  = self.cachedEstimate(region, channel, setup)
        gen  = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'GenMET'}))
        assert ref+gen > 0, "denominator > 0 not fulfilled, this is odd and should not happen!"
        return abs(ref-gen)/(ref+gen)

    def fastSimPUSystematic(self, region, channel, setup):
        ''' implemented based on the official SUSY recommendation https://twiki.cern.ch/twiki/bin/viewauth/CMS/SUSRecommendationsMoriond17#Pileup_lumi
        '''
        incl        = self.cachedEstimate(region, channel, setup.sysClone())
        incl_nvert  = self.cachedEstimate(region, channel, setup.sysClone({'reweight':['nVert']}))
        if incl.val > 0:
            exp_nvert = int(incl_nvert.val/incl.val)
            incl_nvert = incl_nvert/incl
        else:
            return u_float(1) # Use 100% uncertainty until we have a better idea
        hiPU        = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'nVert>='+str(exp_nvert)}))
        hiPU_nvert  = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'nVert>='+str(exp_nvert), 'reweight':['nVert']}))
        loPU        = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'nVert<'+str(exp_nvert)}))
        loPU_nvert  = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'nVert<'+str(exp_nvert), 'reweight':['nVert']}))
        if loPU.val > 0 and hiPU.val > 0:
            loPU_nvert = loPU_nvert/loPU
            hiPU_nvert = hiPU_nvert/hiPU
        else:
            return u_float(1) # Use 100% uncertainty until we have a better idea

        k_central   = (loPU.val - hiPU.val)/(loPU_nvert.val - hiPU_nvert.val)
        k_loUp      = ((loPU.val + loPU.sigma) - (hiPU.val - hiPU.sigma))/(loPU_nvert.val - hiPU_nvert.val)
        k_loDown    = ((loPU.val - loPU.sigma) - (hiPU.val + hiPU.sigma))/(loPU_nvert.val - hiPU_nvert.val)
        
        d_central   = loPU.val - k_central*(loPU_nvert.val - incl_nvert.val)
        d_loUp      = loPU.val + loPU.sigma - k_loUp*(loPU_nvert.val - incl_nvert.val)
        d_loDown    = loPU.val - loPU.sigma - k_loDown*(loPU_nvert.val - incl_nvert.val)
        
        data_PU = setup.dataPUHistForSignal
        fold_loUp   = 0.
        fold_loDown = 0.
        for i in range(1,data_PU.GetNbinsX()+1):
            fold = (k_loUp*(i - incl_nvert.val) + d_loUp) * data_PU.GetBinContent(i)
            if fold > 0:
                fold_loUp += fold
            fold = (k_loDown*(i - incl_nvert.val) + d_loDown) * data_PU.GetBinContent(i)
            if fold > 0:
                fold_loDown += fold
        ref  = self.cachedEstimate(region, channel, setup)
        gen  = self.cachedEstimate(region, channel, setup.sysClone({'selectionModifier':'GenMET'}))
        unc = min([abs(fold_loDown - fold_loUp)/(0.5*(ref.val+gen.val)), 1.])
        return u_float(unc)

    def getBkgSysJobs(self, region, channel, setup, puUpOrDown=False):
        if not puUpOrDown:
            puUpOrDown = ['VVUp','Up'] if setup.year == 2018 else ['Up','Down']
        setup.sysClone({'reweight':['reweightPU'+puUpOrDown[0]]})
        l = [
            (region, channel, setup.sysClone({'reweight':['reweightPU'+puUpOrDown[0]]})),
            (region, channel, setup.sysClone({'reweight':['reweightPU'+puUpOrDown[1]]})),

            (region, channel, setup.sysClone({'reweight':['reweightTopPt']})),

            (region, channel, setup.sysClone({'selectionModifier':'jerUp'})),
            (region, channel, setup.sysClone({'selectionModifier':'jerDown'})),

            (region, channel, setup.sysClone({'selectionModifier':'jesTotalUp'})),
            (region, channel, setup.sysClone({'selectionModifier':'jesTotalDown'})),

            (region, channel, setup.sysClone({'selectionModifier':'unclustEnUp'})),
            (region, channel, setup.sysClone({'selectionModifier':'unclustEnDown'})),

            (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_b_Up']})),
            (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_b_Down']})),
            (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_l_Up']})),
            (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_l_Down']})),

            (region, channel, setup.sysClone({'reweight':['reweightLeptonSFDown']})),
            (region, channel, setup.sysClone({'reweight':['reweightLeptonSFUp']})),

            (region, channel, setup.sysClone({'reweight':['reweightDilepTriggerDown']})),
            (region, channel, setup.sysClone({'reweight':['reweightDilepTriggerUp']})),

            (region, channel, setup.sysClone({'reweight':['reweightL1PrefireDown']})),
            (region, channel, setup.sysClone({'reweight':['reweightL1PrefireUp']})),

            (region, channel, setup.sysClone({'remove':['reweightLeptonSip3dSF']})),
            (region, channel, setup.sysClone({'remove':['reweightLeptonHit0SF']})),
        ]
        return l

    def getSigSysJobs(self, region, channel, setup, isFastSim = False):
        if isFastSim:
            l = [
                (region, channel, setup.sysClone({'reweight':['reweightTopPt']})),

                (region, channel, setup.sysClone({'selectionModifier':'jerUp'})),
                (region, channel, setup.sysClone({'selectionModifier':'jerDown'})),

                (region, channel, setup.sysClone({'selectionModifier':'jesTotalUp'})),
                (region, channel, setup.sysClone({'selectionModifier':'jesTotalDown'})),

                (region, channel, setup.sysClone({'selectionModifier':'unclustEnUp'})),
                (region, channel, setup.sysClone({'selectionModifier':'unclustEnDown'})),

                (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_b_Up']})),
                (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_b_Down']})),
                (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_l_Up']})),
                (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_l_Down']})),

                (region, channel, setup.sysClone({'reweight':['reweightLeptonSFDown']})),
                (region, channel, setup.sysClone({'reweight':['reweightLeptonSFUp']})),

                (region, channel, setup.sysClone({'reweight':['reweightDilepTriggerBackupDown']})),
                (region, channel, setup.sysClone({'reweight':['reweightDilepTriggerBackupUp']})),

                (region, channel, setup.sysClone({'reweight':['reweight_nISRDown']})),
                (region, channel, setup.sysClone({'reweight':['reweight_nISRUp']})),

                (region, channel, setup.sysClone({'reweight':['reweightL1PrefireDown']})),
                (region, channel, setup.sysClone({'reweight':['reweightL1PrefireUp']})),

                (region, channel, setup.sysClone({'remove':['reweightLeptonSip3dSF']})),
                (region, channel, setup.sysClone({'remove':['reweightLeptonHit0SF']})),
            ]
            l.extend( [\
                (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_FS_Up']})),
                (region, channel, setup.sysClone({'reweight':['reweightBTag_SF_FS_Down']})),
                (region, channel, setup.sysClone({'reweight':['reweightLeptonFastSimSFUp']})),
                (region, channel, setup.sysClone({'reweight':['reweightLeptonFastSimSFDown']})),
                (region, channel, setup.sysClone({'selectionModifier':'GenMET'})),
                (region, channel, setup.sysClone({'selectionModifier':'highPU'})),
                (region, channel, setup.sysClone({'selectionModifier':'lowPU'})),

            ] )
        else:
            l = self.getBkgSysJobs(region = region, channel = channel, setup = setup)
        return l

    def getTexName(self, channel, rootTex=True):
        try:
          name = self.texName
        except:
          try:
            name = self.sample[channel].texName
          except:
            try:
              texNames = [self.sample[c].texName for c in channels]                # If all, only take texName if it is the same for all channels
              if texNames.count(texNames[0]) == len(texNames):
                name = texNames[0]
              else:
                name = self.name
            except:
              name = self.name
        if not rootTex: name = "$" + name.replace('#','\\') + "$" # Make it tex format
        return name
