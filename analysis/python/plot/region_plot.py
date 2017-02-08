#!/usr/bin/env python
#Standard imports
import ROOT, os
ROOT.gROOT.SetBatch(True)

from math                                   import sqrt
from RootTools.core.standard                import *
from StopsDilepton.analysis.estimators      import setup, constructEstimatorList, MCBasedEstimate
from StopsDilepton.analysis.DataObservation import DataObservation
from StopsDilepton.analysis.regions         import regionsO as regions
from StopsDilepton.analysis.regions         import noRegions
from StopsDilepton.tools.user               import plot_directory
from StopsDilepton.samples.color            import color
from StopsDilepton.analysis.SetupHelpers    import channels, allChannels

# argParser
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', action='store',      default='INFO', nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], help="Log level for logging")
argParser.add_argument("--signal",   action='store',      default='T2tt', nargs='?', choices=["T2tt","TTbarDM"],                                                   help="Which signal to plot?")
argParser.add_argument("--control",  action='store',      default=None,   nargs='?', choices=[None, "DY", "VV", "DYVV","TTZ"],                                     help="For CR region?")
argParser.add_argument("--scale",    action='store_true', default=False,  help="Scale CR using pulls from nuisance table? (not yet for TTZ)")
argParser.add_argument("--labels",   action='store_true', default=False,  help="Plot labels?")
argParser.add_argument("--ratio",    action='store_true', default=True,   help="Plot ratio?")
argParser.add_argument("--noData",   action='store_true', default=False,  help="Do not plot data?")
args = argParser.parse_args()

# Logging
import StopsDilepton.tools.logger as logger
import RootTools.core.logger      as logger_rt
logger    = logger.get_logger(   args.logLevel, logFile = None )
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None )

channels = ['all','SF','EE','EMu','MuMu']

# alternative setups for control region
if args.control:
  if   args.control == "DY":   setup = setup.sysClone(parameters={'nBTags':(0,0 ), 'dPhi': False, 'dPhiInv': True,  'zWindow': 'onZ'}) 
  elif args.control == "VV":   setup = setup.sysClone(parameters={'nBTags':(0,0 ), 'dPhi': True,  'dPhiInv': False, 'zWindow': 'onZ'})
  elif args.control == "DYVV": setup = setup.sysClone(parameters={'nBTags':(0,0 ), 'dPhi': False, 'dPhiInv': False, 'zWindow': 'onZ'})
  elif args.control == "TTZ":
    setups   = [setup.sysClone(parameters={'triLep': True, 'zWindow' : 'onZ', 'mllMin': 0, 'metMin' : 0, 'metSigMin' : 0, 'nJets':(2,2), 'nBTags':(2,2), 'dPhi': False, 'dPhiInv': False}),
                setup.sysClone(parameters={'triLep': True, 'zWindow' : 'onZ', 'mllMin': 0, 'metMin' : 0, 'metSigMin' : 0, 'nJets':(3,3), 'nBTags':(1,1), 'dPhi': False, 'dPhiInv': False}),
                setup.sysClone(parameters={'triLep': True, 'zWindow' : 'onZ', 'mllMin': 0, 'metMin' : 0, 'metSigMin' : 0, 'nJets':(3,3), 'nBTags':(2,2), 'dPhi': False, 'dPhiInv': False}),
                setup.sysClone(parameters={'triLep': True, 'zWindow' : 'onZ', 'mllMin': 0, 'metMin' : 0, 'metSigMin' : 0, 'nJets':(4,4), 'nBTags':(1,1), 'dPhi': False, 'dPhiInv': False}),
                setup.sysClone(parameters={'triLep': True, 'zWindow' : 'onZ', 'mllMin': 0, 'metMin' : 0, 'metSigMin' : 0, 'nJets':(4,4), 'nBTags':(2,2), 'dPhi': False, 'dPhiInv': False})]
    channels = ['all'] # only make plot in channel all for TTZ CR

# define order of estimators
if not args.control:         detailedEstimators = constructEstimatorList(['TTJets-DD', 'TTZ', 'multiBoson', 'other', 'DY'])  # use DD Top prediction when we are in SR
elif args.control == "DY":   detailedEstimators = constructEstimatorList(['DY', 'multiBoson', 'TTJets', 'TTZ', 'other'])
elif args.control == "VV":   detailedEstimators = constructEstimatorList(['multiBoson', 'DY', 'TTJets', 'TTZ', 'other'])
elif args.control == "DYVV": detailedEstimators = constructEstimatorList(['DY', 'multiBoson', 'TTJets', 'TTZ', 'other'])
elif args.control == "TTZ":  detailedEstimators = constructEstimatorList(['TTZ', 'TTJets', 'multiBoson', 'DY', 'other'])

for estimator in detailedEstimators:
    estimatorColor = getattr( color, estimator.name.split('-')[0] ) 
    estimator.style = styles.fillStyle(estimatorColor, lineColor = estimatorColor )


# signals and blindings
scale = 1
if not args.control:
  if args.signal == "T2tt":
    from StopsDilepton.samples.cmgTuples_FastSimT2tt_mAODv2_25ns_postProcessed    import T2tt_650_1, T2tt_500_250
    signals        = [T2tt_650_1, T2tt_500_250]
    setup.blinding = "(evt%15==0)"
    scale          = 1./15.
    signalSetup    = setup
  elif args.signal == "TTbarDM":
    from StopsDilepton.samples.cmgTuples_FullSimTTbarDM_mAODv2_25ns_postProcessed import TTbarDMJets_scalar_Mchi_1_Mphi_10, TTbarDMJets_pseudoscalar_Mchi_1_Mphi_10
    signals        = [TTbarDMJets_scalar_Mchi_1_Mphi_10, TTbarDMJets_pseudoscalar_Mchi_1_Mphi_10]
    setup.blinding = "(run<=276811||(run>=277820&&run<=279931))"
    scale          = 17.3/36.4
    signalSetup    = setup.sysClone(sys = {'reweight':['reweightLeptonFastSimSF']})

 
# no signals if we are looking at CR
if args.control:
  signals = []
  postfix = 'controlRegions_' + args.control + ('_scaled' if args.scale else '')


# signals style
signalEstimators = [ MCBasedEstimate(name=s.name,  sample={channel:s for channel in allChannels}, cacheDir=setup.defaultCacheDir() ) for s in signals]
for i, estimator in enumerate(signalEstimators):
  estimator.style = styles.lineStyle( ROOT.kBlack, width=2, dotted=(i==1), dashed=(i==2))
  estimator.isSignal=True
 
estimators = detailedEstimators + signalEstimators
for e in estimators: e.initCache(setup.defaultCacheDir())

# data
observation       = DataObservation(name='Data', sample=setup.sample['Data'], cacheDir=setup.defaultCacheDir())
observation.style = styles.errorStyle( ROOT.kBlack, markerSize = 1.5 )

# define the systemativ variations
systematics = { 'JEC' :        ['JECUp', 'JECDown'],
       #         'JER' :        ['JERUp', 'JERDown'],
                'PU' :         ['reweightPU36fbUp', 'reweightPU36fbDown'],
                'stat' :       ['statLow', 'statHigh'],
                'topPt' :      ['reweightTopPt', None],
                'b-tag-b' :    ['reweightBTag_SF_b_Up','reweightBTag_SF_b_Down'],
                'b-tag-l' :    ['reweightBTag_SF_l_Up','reweightBTag_SF_l_Down'],
                'trigger' :    ['reweightDilepTriggerBackupUp', 'reweightDilepTriggerBackupDown'],
                'leptonSF' :   ['reweightLeptonSFUp','reweightLeptonSFDown'],
                'TTJets' :     ['shape-TTJetsUp', 'shape-TTJetsDown'],
                'TTZ' :        ['shape-TTZUp', 'shape-TTZDown'],
                'other' :      ['shape-other', 'shape-other'],
                'multiBoson' : ['shape-multiBosonUp', 'shape-multiBosonDown'],
                'DY' :         ['shape-DYUp', 'shape-DYDown'],
}

sysVariations = [None]
for var in systematics.values():
  sysVariations += var

# Function to get the sample uncertainty from the card and nuisance files
from StopsDilepton.analysis.infoFromCards import getPreFitUncFromCard, getPostFitUncFromCard, applyNuisance, getBinNumber

cardFile = '/user/tomc/StopsDilepton/results_80X_v24/fitAll/cardFiles/T2tt/T2tt_550_350.txt' 
#if args.control:
#  if args.control == "TTZ":  cardFile = '/user/tomc/StopsDilepton/results_80X_v24/controlTTZ/cardFiles/T2tt/T2tt_550_350.txt' # Warning: need to have a card where there is at least a little bit of signal, otherwise the nuisance file is not derived correctly
#  if args.control == "DYVV": cardFile = '/user/tomc/StopsDilepton/results_80X_v24/controlDYVV/cardFiles/T2tt/T2tt_550_350.txt'

def getSampleUncertainty(cardFile, res, var, estimate, binName):
    if   estimate.name.count('TTZ'):    uncName = 'ttZ'
    elif estimate.name.count('TTJets'): uncName = 'top'
    else:                               uncName = estimate.name
    if var and var.count(estimate.name):
      if   args.scale and args.control == "DYVV" and estimate.name in ["DY","multiBoson"]: unc = getPostFitUncFromCard(cardFile, estimate.name, uncName, binName);
      elif args.scale and args.control == "TTZ"  and estimate.name in ["TTZ"]:             unc = getPostFitUncFromCard(cardFile, estimate.name, uncName, binName);
      else:                                                                                unc = getPreFitUncFromCard(cardFile,  estimate.name, uncName, binName);
      if   var.count('Up'):   return res*(1.+unc)
      elif var.count('Down'): return res*(1.-unc)
    return res

# Histogram style
def applyStyle(hist, estimate):
    if estimate.name == "Data":
      if channel == "all":  hist.legendText = "Data"
      if channel == "EE":   hist.legendText = "Data (2e)"
      if channel == "MuMu": hist.legendText = "Data (2#mu)"
      if channel == "EMu":  hist.legendText = "Data (1e, 1#mu)"
      if channel == "SF":   hist.legendText = "Data (SF)"
    else:
      hist.legendText = estimate.getTexName(channel)

    hist.style = estimate.style
    hist.GetXaxis().SetLabelOffset(99)
    hist.GetXaxis().SetTitleOffset(1.5)
    hist.GetXaxis().SetTitleSize(2)
    hist.GetYaxis().SetTitleSize(2)
    hist.GetYaxis().SetLabelSize(0.7)


# For TTZ CR we work with setups instead of regions
def getRegionHistoTTZ(estimate, channel, setups, variations = [None]):
    h = {}
    for var in variations:
      h[var] = ROOT.TH1F(estimate.name + channel + (var if var else ""), estimate.name, len(setups), 0, len(setups))

    for i, s in enumerate(setups):
      binName = ' '.join([channel, noRegions[0].__str__()]) + "_controlTTZ" + str(i+1)

      estimate.initCache(s.defaultCacheDir())
      for var in variations:
        if var in ['statLow', 'statHigh']: continue

        setup_ = s if not var or var.count('shape') else s.sysClone({'selectionModifier': var}) if var.count('JE') else s.sysClone({'reweight':[var]})
        res = estimate.cachedEstimate(noRegions[0], channel, setup_, save=True)
        if args.control == 'TTZ' and estimate.name == "TTZ" and args.scale: res = applyNuisance(cardFile, estimate, res, binName)
        res = getSampleUncertainty(cardFile, res, var, estimate, binName)
        h[var].SetBinContent(i+1, res.val)
        h[var].SetBinError(i+1, res.sigma)

        if not var and ('statLow' in variations or 'statHigh' in variations):
          h['statLow'].SetBinContent(i+1,  res.val-res.sigma)
          h['statHigh'].SetBinContent(i+1, res.val+res.sigma)

    applyStyle(h[None], estimate)

    if not estimate.name == "Data":
      for hh in h.values(): hh.Scale(scale)
    return h


def getRegionHisto(estimate, regions, channel, setup, variations = [None]):
    if args.control and args.control == "TTZ": return getRegionHistoTTZ(estimate, channel=channel, setups = setups, variations = variations)

    h = {}
    for var in variations:
      h[var] = ROOT.TH1F(estimate.name + channel + (var if var else ""), estimate.name, len(regions), 0, len(regions))

    for i, r in enumerate(regions):
      binName = ' '.join(['SF', r.__str__()]) + ("_controlDYVV" if args.control and args.control=="DYVV" else "") #always take SF here (that's allways available for DYVV)
      for var in variations:
        if var in ['statLow', 'statHigh']: continue

        setup_ = setup if not var or var.count('shape') else setup.sysClone({'selectionModifier': var}) if var.count('JE') else setup.sysClone({'reweight':[var]})
        res = estimate.cachedEstimate(r, channel, setup_, save=True)
        if args.control == 'DYVV' and estimate.name in ['DY', 'multiBoson'] and args.scale: res = applyNuisance(cardFile, estimate, res, binName)
        res = getSampleUncertainty(cardFile, res, var, estimate, binName)
        h[var].SetBinContent(i+1, res.val)
        h[var].SetBinError(i+1, res.sigma)

        if not var and ('statLow' in variations or 'statHigh' in variations):
          h['statLow'].SetBinContent(i+1,  res.val-res.sigma)
          h['statHigh'].SetBinContent(i+1, res.val+res.sigma)

    applyStyle(h[None], estimate)

    if not estimate.name == "Data":
      for hh in h.values(): hh.Scale(scale)
    return h



def drawLabels( regions ):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.015)
    tex.SetTextAngle(90)
    tex.SetTextAlign(12) # align right
    min = 0.15
    max = 0.95
    diff = (max-min) / len(regions)
    lines =  [(min+(i+0.5)*diff, 0.005,  r.texStringForVar('dl_mt2ll'))   for i, r in enumerate(regions)]
    lines += [(min+(i+0.5)*diff, 0.145,  r.texStringForVar('dl_mt2blbl')) for i, r in enumerate(regions)]
    lines += [(min+(i+0.5)*diff, 0.285,  r.texStringForVar('dl_mt2bb'))   for i, r in enumerate(regions)]
    return [tex.DrawLatex(*l) for l in lines] 

def drawBinNumbers(numberOfBins):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.1 if args.ratio else 0.04)
    tex.SetTextAlign(23) # align right
    min = 0.15
    max = 0.95
    diff = (max-min) / numberOfBins
    lines = [(min+(i+0.5)*diff, 0.25 if args.ratio else .12,  str(i)) for i in range(numberOfBins)]
    return [tex.DrawLatex(*l) for l in lines]

def drawDivisions(regions):
    if args.control and args.control=="TTZ": return []
    min = 0.15
    max = 0.95
    diff = (max-min) / len(regions)
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(23) # align right
    tex.SetTextSize(0.03)
    tex.SetTextColor(38)

    lines  = [(min+3*diff,  .9, '100 GeV < M_{T2}(ll) < 140 GeV')]
    lines += [(min+9*diff, .9, '140 GeV < M_{T2}(ll) < 240 GeV')]

    tex2= tex.Clone()
    tex2.SetTextAngle(90)
    tex2.SetTextAlign(31)
    lines2 = [(min+12.5*diff, .9, 'M_{T2}(ll) > 240 GeV')]

    line = ROOT.TLine()
    line.SetLineColor(38)
    line.SetLineWidth(2)
    line.SetLineStyle(3)
    line1 = (min+6*diff,  0.13, min+6*diff, 0.93);
    line2 = (min+12*diff, 0.13, min+12*diff, 0.93);
    return [line.DrawLineNDC(*l) for l in [line1, line2]] + [tex.DrawLatex(*l) for l in lines] + [tex2.DrawLatex(*l) for l in lines2]


def drawLumi( lumi_scale ):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(11) # align right
    lines = [
      (0.15, 0.95, 'CMS Preliminary'),
      (0.71, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV)' % (lumi_scale/1000.*scale))
    ]
    return [tex.DrawLatex(*l) for l in lines]



# Main code
for channel in channels:

    regions_ = regions[1:]

    bkg_histos = {}
    for e in detailedEstimators:
      histos = getRegionHisto(e, regions=regions_, channel=channel, setup = setup, variations = sysVariations)
      for k in set(sysVariations):
        if k in bkg_histos: bkg_histos[k].append(histos[k])
        else:               bkg_histos[k] = [histos[k]]

    # Get summed histos for the systematics
    histos_summed = {k: bkg_histos[k][0].Clone() for k in set(sysVariations)}
    for k in set(sysVariations):
      for i in range(1, len(bkg_histos[k])):
        histos_summed[k].Add(bkg_histos[k][i])

    # Get up-down for each of the systematics
    h_sys = {}
    for sys, vars in systematics.iteritems():
        h_sys[sys] = histos_summed[vars[0]].Clone()
        h_sys[sys].Scale(-1)
        h_sys[sys].Add(histos_summed[vars[1] if len(vars) > 1 else None])

    h_rel_err = histos_summed[None].Clone()
    h_rel_err.Reset()

    # Adding the systematics in quadrature
    for k in h_sys.keys():
        for ib in range( 1 + h_rel_err.GetNbinsX() ):
            h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (h_sys[k].GetBinContent(ib)/2)**2 )

    for ib in range( 1 + h_rel_err.GetNbinsX() ):
        h_rel_err.SetBinContent(ib, sqrt( h_rel_err.GetBinContent(ib) ) )

    # Divide by the summed hist to get relative errors
    h_rel_err.Divide(histos_summed[None])

    # For signal histos we don't need the systematics, so only access the "None"
    sig_histos = [ [getRegionHisto(e, regions=regions_, channel=channel, setup = signalSetup)[None]] for e in signalEstimators ]
    data_histo = [ [getRegionHisto(observation, regions=regions_, channel=channel, setup=setup)[None]]] if not args.noData else []

    if not args.noData:
      data_histo[0][0].Sumw2(ROOT.kFALSE)
      data_histo[0][0].SetBinErrorOption(ROOT.TH1.kPoisson) # Set poissonian errors

    region_plot = Plot.fromHisto(name = channel, histos = [ bkg_histos[None] ] + data_histo + sig_histos, texX = ("control" if args.control else "signal") + " region number", texY = "Events" )

    boxes = []
    ratio_boxes = []
    for ib in range(1, 1 + h_rel_err.GetNbinsX() ):
        val = histos_summed[None].GetBinContent(ib)
        if val<0: continue
        sys = h_rel_err.GetBinContent(ib)
        box = ROOT.TBox( h_rel_err.GetXaxis().GetBinLowEdge(ib),  max([0.006, (1-sys)*val]), h_rel_err.GetXaxis().GetBinUpEdge(ib), max([0.006, (1+sys)*val]) )
        box.SetLineColor(ROOT.kBlack)
        box.SetFillStyle(3444)
        box.SetFillColor(ROOT.kBlack)
        r_box = ROOT.TBox( h_rel_err.GetXaxis().GetBinLowEdge(ib),  max(0.1, 1-sys), h_rel_err.GetXaxis().GetBinUpEdge(ib), min(1.9, 1+sys) )
        r_box.SetLineColor(ROOT.kBlack)
        r_box.SetFillStyle(3444)
        r_box.SetFillColor(ROOT.kBlack)

        boxes.append( box )
        ratio_boxes.append( r_box )


    if args.signal == "T2tt":      legend = (0.55,0.85-0.013*(len(bkg_histos) + len(sig_histos)), 0.9, 0.85)
    elif args.signal == "TTbarDM": legend = (0.55,0.85-0.010*(len(bkg_histos) + len(sig_histos)), 0.9, 0.85)

    def setRatioBorder(c, y_border):
      topPad = c.GetPad(1)
      topPad.SetPad(topPad.GetX1(), y_border, topPad.GetX2(), topPad.GetY2())
      bottomPad = c.GetPad(2)
      bottomPad.SetPad(bottomPad.GetX1(), bottomPad.GetY1(), bottomPad.GetX2(), y_border)

    canvasModifications = []
    if args.labels: canvasModifications = [lambda c: c.SetWindowSize(c.GetWw(), int(c.GetWh()*2)), lambda c : c.GetPad(0).SetBottomMargin(0.5)]
    if args.ratio:  canvasModifications = [lambda c: setRatioBorder(c, 0.2), lambda c : c.GetPad(2).SetBottomMargin(0.27)]

    if args.control and args.control=="TTZ": numberOfBins = len(setups)
    else:                                    numberOfBins = len(regions_)

    drawObjects = boxes + drawLumi(setup.dataLumi[channel] if channel in ['EE','MuMu','EMu'] else setup.dataLumi['EE'])
    if not (args.control and args.control=="TTZ"): drawObjects += drawDivisions(regions_)

    if args.ratio:
      ratio = {'yRange':(0.1,1.9), 'drawObjects': ratio_boxes + drawBinNumbers(numberOfBins)}
    else:
      drawObjects += drawLabels(regions_) if args.labels else drawBinNumbers(numberOfBins)
      drawObjects += drawBinNumbers(numberOfBins)
      ratio = None

    if not args.control:       yRange = (0.006, 'auto')
    elif args.control=='DYVV': yRange = (0.006, 2000000)
    elif args.control=='TTZ':  yRange = (0.6, 20000)

    plotting.draw( region_plot, \
        plot_directory = os.path.join(plot_directory, postfix),
        logX = False, logY = True,
        sorting = False,
        ratio = ratio,
        extensions = ["pdf", "png", "root","C"],
        yRange = yRange,
        widths = {'x_width':1000, 'y_width':700},
        drawObjects = drawObjects,
        legend = legend,
        canvasModifications = canvasModifications
    )
