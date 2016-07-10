''' Analysis script for 1D 2l plots (RootTools)
'''

#Standard imports
import ROOT
from math import sqrt, cos, sin, pi, acos
import itertools

#RootTools
from RootTools.core.standard import *

# argParser
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', 
      action='store',
      nargs='?',
      choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'],
      default='INFO',
      help="Log level for logging"
)

argParser.add_argument('--mode',
    default='doubleMu',
    action='store',
    choices=['doubleMu', 'doubleEle'])

argParser.add_argument('--zMode',
    default='onZ',
    action='store',
    choices=['onZ', 'offZ', 'allZ']
)

argParser.add_argument('--ttjets',
    default='LO',
    action='store',
    choices=['LO', 'NLO'])

argParser.add_argument('--dy',
    default='HT',
    action='store',
    choices=['LO', 'NLO'])

argParser.add_argument('--pu',
    default="reweightPU",
    action='store',
    choices=["None", "reweightPU", "reweightPUUp", "reweightPUDown", "reweightPUVUp", "reweightPUVDown", "reweightNVTX", "reweightNVTXUp", "reweightNVTXDown", "reweightNVTXVUp", "reweightNVTXVDown"],
    help='PU weight',
)

argParser.add_argument('--small',
    action='store_true',
#    default=True,
    help='Small?',
)

argParser.add_argument('--reversed',
    action='store_true',
    help='Reversed?',
)

argParser.add_argument('--signals',
    action='store',
    nargs='*',
    type=str,
    default=[],
    help="Signals?"
    )

argParser.add_argument('--overwrite',
#    default = False,
    default = True,
    action='store_true',
    help='overwrite?',
)

argParser.add_argument('--plot_directory',
    default='recoil_80X',
    action='store',
)

args = argParser.parse_args()

# Logging
import StopsDilepton.tools.logger as logger
logger = logger.get_logger(args.logLevel, logFile = None )
import RootTools.core.logger as logger_rt
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None )

mcFilterCut   = "Flag_goodVertices&&Flag_HBHENoiseIsoFilter&&Flag_HBHENoiseFilter&&Flag_globalTightHalo2016Filter&&Flag_eeBadScFilter&&Flag_EcalDeadCellTriggerPrimitiveFilter&&Flag_badChargedHadron&&Flag_badMuon"
dataFilterCut = mcFilterCut+"&&weight>0"
postProcessing_directory = "postProcessed_80X_v7/dilepTiny/"
from StopsDilepton.samples.cmgTuples_Spring16_mAODv2_postProcessed import *
postProcessing_directory = "postProcessed_80X_v7/dilepTiny/"
from StopsDilepton.samples.cmgTuples_Data25ns_80X_postProcessed import *

def getZCut(mode):
    mZ = 91.2
    zstr = "abs(dl_mass - "+str(mZ)+")"
    if mode.lower()=="onz": return zstr+"<15"
    if mode.lower()=="offz": return zstr+">15"
    return "(1)"

if args.mode=="doubleMu":
    leptonSelectionString = "&&".join(["isMuMu==1&&nGoodMuons==2&&nGoodElectrons==0", getZCut(args.zMode)])
    data_sample = DoubleMuon_Run2016B
    #qcd_sample = QCD_Mu5 #FIXME
    trigger     = "HLT_mumuIso"
elif args.mode=="doubleEle":
    leptonSelectionString = "&&".join(["isEE==1&&nGoodMuons==0&&nGoodElectrons==2", getZCut(args.zMode)])
    data_sample = DoubleEG_Run2016B
    #qcd_sample = QCD_EMbcToE
    trigger   = "HLT_ee_DZ"
elif args.mode=="muEle":
    leptonSelectionString = "&&".join(["isEMu==1&&nGoodMuons==1&&nGoodElectrons==1", getZCut(args.zMode)])
    data_sample = MuonEG_Run2016B
    #qcd_sample = QCD_Mu5EMbcToE
    trigger    = "HLT_mue"
else:
    raise ValueError( "Mode %s not known"%args.mode )

if args.ttjets == "NLO":
    TTJets_sample = TTJets
elif args.ttjets == "LO":
    TTJets_sample = TTJets_Lep 
else:
    raise ValueError
if args.dy == "NLO":
    dy_sample = DY
elif args.dy == "LO":
    dy_sample = DY_HT_LO
else:
    raise ValueError

#mc = [ DY, TTJets, qcd_sample, singleTop, TTX, diBoson, triBoson, WJetsToLNu]
#mc = [ DY, TTJets, qcd_sample, TTZ]
mc = [ dy_sample, TTJets_sample, singleTop, TTZ, TTXNoZ, multiBoson]
#mc = [ TTX]
if args.small:
    for sample in mc + [ data_sample ]:
        sample.reduceFiles(to = 1)
    #TTJets_Dilep.reduceFiles(to = 1)

data_sample.style = styles.errorStyle( ROOT.kBlack )
lumi_scale = data_sample.lumi/1000

for sample in mc:
    sample.style = styles.fillStyle( sample.color)

from StopsDilepton.tools.user import plot_directory

# official PU reweighting
weight = lambda data:data.weight

cuts=[
#    ("leadingLepIsTight", "l1_miniRelIso<0.4"),
#    ("multiIsoWP", "l1_index>=0&&l1_index<1000&&l2_index>=0&&l2_index<1000&&"+multiIsoWP),
    ("njet1p", "nJetGood>=1"),
#    ("nbtag1", "nBTag>=1"),
#    ("nbtag0", "nBTag==0"),
#    ("mll20", "dl_mass>20"),
#    ("met80", "met_pt>80"),
#    ("metSig5", "met_pt/sqrt(ht)>5"),
#    ("dPhiJet0-dPhiJet1", "cos(met_phi-JetGood_phi[0])<cos(0.25)&&cos(met_phi-JetGood_phi[1])<cos(0.25)"),
    ("lepVeto", "nGoodMuons+nGoodElectrons==2"),
    ("looseLeptonVeto", "Sum$(LepGood_pt>15&&LepGood_miniRelIso<0.4)==2"),

]
                
def drawObjects( dataMCScale ):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(11) # align right

    lines = [ (0.15, 0.95, 'CMS Preliminary') ]
    if dataMCScale is not None: 
        lines.append( (0.45, 0.95, 'L=%3.2f fb{}^{-1} (13 TeV) Scale %3.2f'% ( int(data_sample.lumi/100)/10., dataMCScale ) ) )
    else:
        lines.append( (0.50, 0.95, '13 TeV' ) )
    return [tex.DrawLatex(*l) for l in lines] 

stack = Stack(mc, [data_sample])

sequence = []

def makeQTZ( data ):
     
    data.qx = data.dl_pt*cos(data.dl_phi)  
    data.qy = data.dl_pt*sin(data.dl_phi)

    data.qt = sqrt( data.qx**2 + data.qy**2 )

def makeUParaUPerp( data ):
    mex = data.met_pt*cos(data.met_phi) 
    mey = data.met_pt*sin(data.met_phi)
    ux = -mex - data.qx 
    uy = -mey - data.qy
    data.upara = (ux*data.qx+uy*data.qy)/data.qt
    data.uperp = (ux*data.qy-uy*data.qx)/data.qt
    data.uPlusQPara = -(mex*data.qx + mey*data.qy)/data.qt

sequence.append( makeQTZ )
sequence.append( makeUParaUPerp )


#TTJets_Dilep.read_variables = [
#    Variable.fromString('ngenPartAll/I'),
#    VectorType.fromString('genPartAll[pt/F,eta/F,phi/F,pdgId/I,status/I,charge/F,motherId/I,grandmotherId/I,nMothers/I,motherIndex1/I,motherIndex2/I,nDaughters/I,daughterIndex1/I,daughterIndex2/I]', nMax=200 ),
#]
#def makeTTJetsQT( data ):
#    
#    gPart = getGenPartsAll( data )
#    genW  = filter( lambda p:abs(p['pdgId'])==24 and abs(p['motherId'])==6, gPart)
#    if not len(genW)==2:
#        print "Warning, found %i W from t"%len(genW)
#    qx = sum([p['pt']*cos(p['phi']) for p in genW ],0.) 
#    qy = sum([p['pt']*sin(p['phi']) for p in genW ],0.)
#    qt = sqrt( qx**2 + qy**2 )
#    data.ttjets_qt = qt 
#
#TTJets_Dilep.sequence = [ makeTTJetsQT ]
#
#if len(args.signals)>0:
#    from StopsDilepton.samples.cmgTuples_FullSimTTbarDM_mAODv2_25ns_2l_postProcessed import *
#    from StopsDilepton.samples.cmgTuples_FastSimT2tt_mAODv2_25ns_2l_postProcessed import *
#    for s in args.signals:
#        if "*" in s:
#            split = s.split("*")
#            sig, fac = split[0], int(split[1])
#        else:
#            sig, fac = s, 1
#        try:
#            stack.append( [eval(sig)] )
#            if hasattr(stack[-1][0], "scale"): 
#                stack[-1][0].scale*=fac
#            elif fac!=1:
#                stack[-1][0].scale = fac
#            else: pass
#
#            if fac!=1:
#                stack[-1][0].name+=" x"+str(fac)                
#            logger.info( "Adding sample %s with factor %3.2f", sig, fac)
#        except NameError:
#            logger.warning( "Could not add signal %s", s)



data_sample.setSelectionString([dataFilterCut, trigger])
for sample in mc:
    sample.setSelectionString([ mcFilterCut])

presel = [("isOS","isOS")]
presel.extend( cuts )

ppfixes = [args.mode, args.zMode]
if args.pu != "None": ppfixes.append( args.pu )
if args.ttjets == "NLO": ppfixes.append( "TTJetsNLO" )
if args.ttjets == "LO": ppfixes.append( "TTJetsLO" )
if args.dy == "NLO": ppfixes.append( "DYNLO" )
if args.dy == "LO": ppfixes.append( "DYLO" )
if args.small: ppfixes = ['small'] + ppfixes
prefix = '_'.join( ppfixes + [ '-'.join([p[0] for p in presel ] ) ] )

plot_path = os.path.join(plot_directory, args.plot_directory, prefix)
assert not os.path.exists(plot_path) or args.overwrite, "Path %s not empty. Skipping."

selectionString = "&&".join( [p[1] for p in presel] + [leptonSelectionString] )

logger.info( "Now plotting with prefix %s and selectionString %s", prefix, selectionString )

logger.info( "Calculating normalization constants" )        
#yield_mc    = sum(s.getYieldFromDraw( selectionString = selectionString, weightString = 'weight')['val'] for s in mc)
#yield_data  = data_sample.getYieldFromDraw( selectionString = selectionString, weightString = 'weight')['val']

for sample in mc:
    dataMCScale = 1. #yield_data/(yield_mc*lumi_scale)
    sample.scale = lumi_scale*dataMCScale
    if args.pu != "None": 
        sample.weight = lambda data:getattr(data, args.pu)
        sample.read_variables = [args.pu+'/F']

#logger.info( "Data/MC Scale: %4.4f Yield MC %4.4f Yield Data %4.4f Lumi-scale %4.4f", dataMCScale, yield_mc, yield_data, lumi_scale )

plots = []
plots2D = []


qt  = Plot(
    name = "qt",
    texX = 'q_{T} (GeV)', texY = 'Number of Events / 5 GeV',
    stack = stack, 
    variable = ScalarType.uniqueFloat().addFiller(lambda data:data.qt),
    binning=[400/5,0,200],
    selectionString = selectionString,
    weight = weight,
    ) 
plots.append( qt )

upara  = Plot(
    name = "upara",
    texX = 'u_{\parallel} (GeV)', texY = 'Number of Events / 5 GeV',
   stack = stack, 
    variable = ScalarType.uniqueFloat().addFiller(lambda data:data.upara),
    binning=[400/5,-200,200],
    selectionString = selectionString,
    weight = weight,
    ) 
plots.append( upara )

dl_uPlusQPara  = Plot(
    name = "uPlusQPara",
    texX = '(u+q)_{\parallel} (GeV)', texY = 'Number of Events / 5 GeV',
   stack = stack, 
    variable = ScalarType.uniqueFloat().addFiller(lambda data:data.uPlusQPara),
    binning=[400/5,-200,200],
    selectionString = selectionString,
    weight = weight,
    ) 
plots.append( dl_uPlusQPara )

dl_uperp  = Plot(
    name = "uperp",
    texX = 'u_{\perp} (GeV)', texY = 'Number of Events / 5 GeV',
    stack = stack, 
    variable = ScalarType.uniqueFloat().addFiller(lambda data:data.uperp),
    binning=[400/5,-200,200],
    selectionString = selectionString,
    weight = weight,
    ) 
plots.append( dl_uperp )

metZoomed  = Plot(
    name = "met_pt_zoomed",
    texX = '#slash{E}_{T} (GeV)', texY = 'Number of Events / 10 GeV',
    stack = stack, 
    variable = Variable.fromString( "met_pt/F" ),
    binning=[22,0,220],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( metZoomed )

met  = Plot(
    texX = '#slash{E}_{T} (GeV)', texY = 'Number of Events / 50 GeV',
    stack = stack, 
    variable = Variable.fromString( "met_pt/F" ),
    binning=[1050/50,0,1050],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( met )

metSig  = Plot(
    texX = '#slash{E}_{T}/#sqrt{H_{T}} (GeV^{1/2})', texY = 'Number of Events / 100 GeV',
    stack = stack, 
    variable = Variable.fromString('metSig/F').addFiller (
        helpers.uses( 
            lambda data: data.met_pt/sqrt(data.ht) if data.ht>0 else float('nan') , 
            ["met_pt/F", "ht/F"])
    ), 
    binning=[30,0,30],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( metSig )

ht  = Plot(
    texX = 'H_{T} (GeV)', texY = 'Number of Events / 100 GeV',
    stack = stack, 
    variable = Variable.fromString( "ht/F" ),
    binning=[2600/100,0,2600],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( ht )

ht_zoomed  = Plot(
    name = "ht_zoomed",
    texX = 'H_{T} (GeV)', texY = 'Number of Events / 30 GeV',
    stack = stack, 
    variable = Variable.fromString( "ht/F" ),
    binning=[390/15,0,390],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( ht_zoomed )

cosMetJet0phi = Plot(\
    texX = 'Cos(#phi(#slash{E}_{T}, Jet[0]))', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString('cosMetJet0phi/F').addFiller (
        helpers.uses(lambda data: cos( data.met_phi - data.JetGood_phi[0] ) , ["met_phi/F", "JetGood[phi/F]"] )
    ), 
    binning = [40,-1,1], 
    selectionString = selectionString,
    weight = weight,
)
plots.append( cosMetJet0phi )

cosMetJet1phi = Plot(\
    texX = 'Cos(#phi(#slash{E}_{T}, Jet[1]))', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString('cosMetJet1phi/F').addFiller (
        helpers.uses(lambda data: cos( data.met_phi - data.JetGood_phi[1] ) , ["met_phi/F", "JetGood[phi/F]"] )
    ), 
    binning = [40,-1,1], 
    selectionString = selectionString,
    weight = weight,
)
plots.append( cosMetJet1phi )

#recoil_TT  = Plot(
#    name = "recoil_TT",
#    texX = 'q_{T} (TTJets Dilep)', texY = 'Number of Events / 10 GeV',
#    stack = stack_TTJets_Dilep, 
#    variable = ScalarType.uniqueFloat().addFiller ( lambda data: data.ttjets_qt ),
#    binning=[200/10,0,200],
#    selectionString = selectionString,
#    weight = weight,
#    ) 
#
#mt2ll_vs_recoil_TT  = Plot2D(
#    name = "mt2ll_vs_recoil_TT",
#    texX = 'M_{T2}(ll)', texY = 'q_{T}=|p_{T}(W_{1}) + p_{T}(W_{2})|',
#    stack = stack_TTJets_Dilep, 
#    variables = (
#        ScalarType.uniqueFloat().addFiller ( lambda data: data.dl_mt2ll ),
#        ScalarType.uniqueFloat().addFiller ( lambda data: data.ttjets_qt ),
#    ),
#    binning=[30,0,200, 30,0,100],
#    weight = weight,
#    selectionString = selectionString
#    )
#plots2D.append( mt2ll_vs_recoil_TT )

def qt_cut_weight( qtb ):
    def w( data ):
        if data.qt>qtb[0] and data.qt<qtb[1]:
            return data.weight
        else:
            return 0
    return w

for qtb in [(0,10), (10,20), (20,30), (30,40), (40, 50), (50,60), (60, 70), (80, 90), (90,100), (100,120), (120,150), (150,200), (200,250), (250,350), (350,550)]:
    upara_qt  = Plot(
        name = "upara_qt_%i_%i"%qtb,
        texX = 'u_{\parallel} (GeV)', texY = 'Number of Events / 10 GeV',
        stack = stack, 
        variable = ScalarType.uniqueFloat().addFiller(lambda data:data.upara),
        weight   = qt_cut_weight(qtb),
        binning=[300/10,-150-qtb[0],150-qtb[0]],
        selectionString = selectionString,
        ) 
    plots.append( upara_qt )

    uPlusQPara_qt  = Plot(
        name = "uPlusQPara_qt_%i_%i"%qtb,
        texX = '(u+q)_{\parallel} (GeV)', texY = 'Number of Events / 10 GeV',
        stack = stack, 
        variable = ScalarType.uniqueFloat().addFiller(lambda data:data.uPlusQPara),
        weight   = qt_cut_weight(qtb),
        binning=[300/10,-150,150],
        selectionString = selectionString,
        ) 
    plots.append( uPlusQPara_qt )

    dl_uperp_qt  = Plot(
        name = "uperp_qt_%i_%i"%qtb,
        texX = 'u_{\perp} (GeV)', texY = 'Number of Events / 5 GeV',
        stack = stack, 
        variable = ScalarType.uniqueFloat().addFiller(lambda data:data.uperp),
        weight   = qt_cut_weight(qtb),
        binning=[300/10,-150,150],
        selectionString = selectionString,
        ) 
    plots.append( dl_uperp_qt )

dl_mass  = Plot(
    texX = 'm(ll) (GeV)', texY = 'Number of Events / 3 GeV',
    stack = stack, 
    variable = Variable.fromString( "dl_mass/F" ),
    binning=[150/3,0,150],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_mass )

dl_pt  = Plot(
    texX = 'p_{T}(ll) (GeV)', texY = 'Number of Events / 10 GeV',
    stack = stack, 
    variable = Variable.fromString( "dl_pt/F" ),
    binning=[40,0,400],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_pt )

dl_qt  = Plot(
    name = "qt",
    texX = 'q_{T}(ll) (GeV)', texY = 'Number of Events / 10 GeV',
    stack = stack, 
    variable = ScalarType.uniqueFloat().addFiller(lambda data:data.qt),
    binning=[40,0,400],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_qt )

dl_eta  = Plot(
    texX = '#eta(ll) ', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString( "dl_eta/F" ),
    binning=[30,-3,3],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_eta )

dl_phi  = Plot(
    texX = '#phi(ll) (GeV)', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString( "dl_phi/F" ),
    binning=[30,-pi,pi],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_phi )

dl_mt2ll  = Plot(
    texX = 'MT_{2}^{ll} (GeV)', texY = 'Number of Events / 20 GeV',
    stack = stack, 
    variable = Variable.fromString( "dl_mt2ll/F" ),
    binning=[300/15,0,300],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_mt2ll )

dl_mt2bb  = Plot(
    texX = 'MT_{2}^{bb} (GeV)', texY = 'Number of Events / 20 GeV',
    stack = stack, 
    variable = Variable.fromString( "dl_mt2bb/F" ),
    binning=[300/15,0,300],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( dl_mt2bb )

dl_mt2blbl  = Plot(
    texX = 'MT_{2}^{blbl} (GeV)', texY = 'Number of Events / 20 GeV',
    stack = stack, 
    variable = Variable.fromString( "dl_mt2blbl/F" ),
    binning=[300/15,0,300],
    selectionString = selectionString,
    weight = weight,
    ) 
plots.append( dl_mt2blbl )


nbtags  = Plot(
    texX = 'number of b-tags (CSVM)', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString('nBTag/I'),
    binning=[8,0,8],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( nbtags )

njets  = Plot(
    texX = 'number of jets', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString('nJetGood/I'),
    binning=[14,0,14],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( njets )

nVert  = Plot(
    texX = 'vertex multiplicity', texY = 'Number of Events',
    stack = stack, 
    variable = Variable.fromString( "nVert/I" ),
    binning=[50,0,50],
    selectionString = selectionString,
    weight = weight,
    )
plots.append( nVert )

read_variables = ["weight/F" , "JetGood[pt/F,eta/F,phi/F]", "met_pt/F", "met_phi/F", "dl_pt/F", "dl_phi/F", "dl_mt2ll/F"]
plotting.fill(plots \
#    + [recoil_TT, mt2ll_vs_recoil_TT]
    , read_variables = read_variables, sequence = sequence)
if not os.path.exists( plot_path ): os.makedirs( plot_path )

ratio = {'yRange':(0.8,1.2)}

#plotting.draw(recoil_TT, 
#    plot_directory = plot_path, ratio = None, 
#    logX = False, logY = True, sorting = False, 
#    yRange = (0, "auto"), 
#)

for plot in plots:
    plotting.draw(plot, 
        plot_directory = plot_path, ratio = ratio, 
        logX = False, logY = True, sorting = False, 
        yRange = (0.03, "auto"), 
        drawObjects = drawObjects( dataMCScale ),
    )

for plot in plots2D:
    plotting.draw2D(
        plot = plot,
        plot_directory = plot_path,
        logX = False, logY = False, logZ = True,
    )

logger.info( "Done with prefix %s and selectionString %s", prefix, selectionString )
