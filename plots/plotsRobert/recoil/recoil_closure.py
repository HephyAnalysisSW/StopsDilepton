#!/usr/bin/env python
''' Analysis script for standard plots
'''
#
# Standard imports and batch mode
#
import ROOT, os
ROOT.gROOT.SetBatch(True)
import itertools
import pickle
from math                                import sqrt, cos, sin, pi

# RootTools
from RootTools.core.standard             import *

# StopsDilepton
from StopsDilepton.tools.user            import plot_directory
from StopsDilepton.tools.helpers         import deltaPhi, map_level
from Analysis.Tools.metFilters            import getFilterCut
from StopsDilepton.tools.cutInterpreter  import cutInterpreter
from StopsDilepton.tools.GaussianFit     import GaussianFit
from StopsDilepton.tools.RecoilCorrector import RecoilCorrector

#
# Arguments
# 
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',           action='store',      default='INFO',          nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], help="Log level for logging")
argParser.add_argument('--small',                                   action='store_true',     help='Run only on a small subset of the data?', )
argParser.add_argument('--fine',                                    action='store_true',     help='Fine binning?', )
argParser.add_argument('--mode',               action='store',      default="mumu",          nargs='?', choices=["mumu", "ee", "SF"], help="Lepton flavor")
argParser.add_argument('--overwrite',                               action='store_true',     help='Overwrite?', )
argParser.add_argument('--plot_directory',     action='store',      default='StopsDilepton/recoil_v3')
argParser.add_argument('--year',               action='store', type=int,      default=2016)
argParser.add_argument('--selection',          action='store',      default='lepSel-btag0-relIso0.12-looseLeptonVeto-mll20-dPhiJet0-dPhiJet1-onZ')
argParser.add_argument('--preHEM',             action='store_true', default=False)
argParser.add_argument('--postHEM',            action='store_true', default=False)
args = argParser.parse_args()

#
# Logger
#
import StopsDilepton.tools.logger as logger
import RootTools.core.logger as logger_rt
logger    = logger.get_logger(   args.logLevel, logFile = None)
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None)

if args.small:                        args.plot_directory += "_small"
if args.fine:                        args.plot_directory += "_fine"
#
# Make samples, will be searched for in the postProcessing directory
#
from Analysis.Tools.puReweighting import getReweightingFunction

if args.year == 2016:
    data_directory = "/afs/hephy.at/data/dspitzbart01/nanoTuples/"
    postProcessing_directory = "stops_2016_nano_v0p3/dilep/"
    from StopsDilepton.samples.nanoTuples_Summer16_postProcessed import *
    postProcessing_directory = "stops_2016_nano_v0p3/dilep/"
    from StopsDilepton.samples.nanoTuples_Run2016_17Jul2018_postProcessed import *
    mc             = [ Top_pow_16, TTXNoZ_16, TTZ_16, multiBoson_16, DY_LO_16]
    if args.reweightPU:
        nTrueInt_puRW = getReweightingFunction(data="PU_2016_35920_XSec%s"%args.reweightPU, mc="Summer16")
    recoilCorrector = RecoilCorrector( 2016 )
elif args.year == 2017:
    data_directory = "/afs/hephy.at/data/dspitzbart03/nanoTuples/"
    postProcessing_directory = "stops_2017_nano_v0p4/dilep/"
    from StopsDilepton.samples.nanoTuples_Fall17_postProcessed import *
    postProcessing_directory = "stops_2017_nano_v0p4/dilep/"
    from StopsDilepton.samples.nanoTuples_Run2017_31Mar2018_postProcessed import *
    mc             = [ Top_pow_17, TTXNoZ_17, TTZ_17, multiBoson_17, DY_LO_17]
    if args.reweightPU:
        nTrueInt_puRW = getReweightingFunction(data="PU_2017_41860_XSec%s"%args.reweightPU, mc="Fall17")
    recoilCorrector = RecoilCorrector( 2017 )
elif args.year == 2018:
    data_directory = "/afs/hephy.at/data/dspitzbart03/nanoTuples/"
    postProcessing_directory = "stops_2018_nano_v0p4/dilep/"
    from StopsDilepton.samples.nanoTuples_Autumn18_postProcessed import *
    postProcessing_directory = "stops_2018_nano_v0p4/dilep/"
    from StopsDilepton.samples.nanoTuples_Run2018_PromptReco_postProcessed import *
    mc             = [ Top_pow_18, TTXNoZ_18, TTZ_18, multiBoson_18, DY_LO_18]
    #nTrueInt_puRW = getReweightingFunction(data="PU_2018_58830_XSec%s"%args.reweightPU, mc="Autumn18")
    if args.reweightPU:
        nTrueInt_puRW = getReweightingFunction(data="PU_2018_58830_XSec%s"%args.reweightPU, mc="Autumn18")
    if args.preHEM:
        recoilCorrector = RecoilCorrector( 2018, "preHEM")
    elif args.postHEM:
        recoilCorrector = RecoilCorrector( 2018, "postHEM")
    else:
        recoilCorrector = RecoilCorrector( 2018 )

for sample in mc: sample.style = styles.fillStyle(sample.color)

# output directory
postfix = ''
if args.year==2018:
    if args.preHEM:
        postfix = '_preHEM'
    elif args.postHEM:
        postfix = '_postHEM'

output_directory = os.path.join(plot_directory, args.plot_directory, str(args.year)+postfix, args.selection )

# Text on the plots
tex = ROOT.TLatex()
tex.SetNDC()
tex.SetTextSize(0.04)
tex.SetTextAlign(11) # align right

def defDrawObjects( plotData, dataMCScale, lumi_scale ):
    lines = [
      (0.15, 0.95, 'CMS Preliminary' if plotData else 'CMS Simulation'), 
      (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV) Scale %3.2f'% ( lumi_scale, dataMCScale ) ) if plotData else (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV)' % lumi_scale)
    ]
    return [tex.DrawLatex(*l) for l in lines] 

def drawPlots(plots, mode, dataMCScale, drawObjects = None):
  for log in [False, True]:
    plot_directory_ = os.path.join(output_directory, mode + ("_log" if log else ""))
    for plot in plots:
      if not max(l[0].GetMaximum() for l in plot.histos): continue # Empty plot
      if mode == "all": plot.histos[1][0].legendText = "Data"
      if mode == "SF":  plot.histos[1][0].legendText = "Data (SF)"

      plotting.draw(plot,
	    plot_directory = plot_directory_,
	    ratio = {'yRange':(0.1,1.9)},
	    logX = False, logY = log, sorting = True,
	    yRange = (0.03, "auto") if log else (0.001, "auto"),
	    scaling = {},
	    legend = (0.15,0.88-0.04*sum(map(len, plot.histos)),0.65,0.88),
	    drawObjects = defDrawObjects( True, dataMCScale , lumi_scale ) + ( drawObjects if drawObjects is not None else [] ) ,
        copyIndexPHP = True,
      )

#
# Read variables and sequences
#
read_variables = ["weight/F", "l1_eta/F" , "l1_phi/F", "l2_eta/F", "l2_phi/F", "JetGood[pt/F,eta/F,phi/F]", "dl_mass/F", "dl_eta/F", "dl_mt2ll/F", "dl_mt2bb/F", "dl_mt2blbl/F",
                  "met_pt/F", "met_phi/F", "MET_significance/F", "metSig/F", "ht/F", "nBTag/I", "nJetGood/I"]

# default offZ for SF
offZ = "&&abs(dl_mass-91.1876)>15" if not (args.selection.count("onZ") or args.selection.count("allZ") or args.selection.count("offZ")) else ""
def getLeptonSelection( mode ):
  if   mode=="mumu": return "nGoodMuons==2&&nGoodElectrons==0&&isOS&&isMuMu" + offZ
  elif mode=="mue":  return "nGoodMuons==1&&nGoodElectrons==1&&isOS&&isEMu"
  elif mode=="ee":   return "nGoodMuons==0&&nGoodElectrons==2&&isOS&&isEE" + offZ
  elif mode=="SF":   return "nGoodMuons+nGoodElectrons==2&&isOS&&(isEE||isMuMu)" + offZ

sequence = []

def corr_recoil( event, sample ):

    mt2Calculator.reset()
    if not sample.isData: 

        # Parametrisation vector - # define qt as GenMET + leptons
        qt_px = event.l1_pt*cos(event.l1_phi) + event.l2_pt*cos(event.l2_phi) + event.GenMET_pt*cos(event.GenMET_phi)
        qt_py = event.l1_pt*sin(event.l1_phi) + event.l2_pt*sin(event.l2_phi) + event.GenMET_pt*sin(event.GenMET_phi)

        qt = sqrt( qt_px**2 + qt_py**2 )
        qt_phi = atan2( qt_py, qt_px )

        # compute fake MET 
        fakeMET_x = event.met_pt*cos(event.met_phi) - event.GenMET_pt*cos(event.GenMET_phi)
        fakeMET_y = event.met_pt*sin(event.met_phi) - event.GenMET_pt*sin(event.GenMET_phi)

        fakeMET = sqrt( fakeMET_x**2 + fakeMET_y**2 )
        fakeMET_phi = atan2( fakeMET_y, fakeMET_x )

        # project fake MET on qT
        fakeMET_para = fakeMET*cos( fakeMET_phi - qt_phi ) 
        fakeMET_perp = fakeMET*cos( fakeMET_phi - ( qt_phi - pi/2) ) 
        
        # FIXME: signs should be negative for v3 and positive for v2 
        fakeMET_para_corr = - recoilCorrector.predict_para( event.nJetGood, qt, -fakeMET_para ) 
        fakeMET_perp_corr = - recoilCorrector.predict_perp( event.nJetGood, qt, -fakeMET_perp )

        # rebuild fake MET vector
        fakeMET_px_corr = fakeMET_para_corr*cos(qt_phi) + fakeMET_perp_corr*cos(qt_phi - pi/2) 
        fakeMET_py_corr = fakeMET_para_corr*sin(qt_phi) + fakeMET_perp_corr*sin(qt_phi - pi/2) 

        #print "%s qt: %3.2f para %3.2f->%3.2f perp %3.2f->%3.2f fakeMET(%3.2f,%3.2f) -> (%3.2f,%3.2f)" % ( sample.name, qt, fakeMET_para, fakeMET_para_corr, fakeMET_perp, fakeMET_perp_corr, fakeMET, fakeMET_phi, sqrt( fakeMET_px_corr**2+fakeMET_py_corr**2), atan2( fakeMET_py_corr, fakeMET_px_corr) )
   
        met_px_corr = event.met_pt*cos(event.met_phi) - fakeMET_x + fakeMET_px_corr 
        met_py_corr = event.met_pt*sin(event.met_phi) - fakeMET_y + fakeMET_py_corr
    
        event.met_pt_corr  = sqrt( met_px_corr**2 + met_py_corr**2 ) 
        event.met_phi_corr = atan2( met_py_corr, met_px_corr ) 

    else:
        event.met_pt_corr  = event.met_pt 
        event.met_phi_corr = event.met_phi

    mt2Calculator.setLeptons(event.l1_pt, event.l1_eta, event.l1_phi, event.l2_pt, event.l2_eta, event.l2_phi)
    mt2Calculator.setMet(event.met_pt_corr, event.met_phi_corr)
    event.dl_mt2ll_corr =  mt2Calculator.mt2ll()

    #print event.dl_mt2ll, event.dl_mt2ll_corr

sequence.append( corr_recoil )

# qT + ETmiss + u = 0
u_para = "-met_pt*cos(met_phi-dl_phi)"        # u_para is actually (u+qT)_para = -ET.n_para
u_perp = "-met_pt*cos(met_phi-(dl_phi-pi/2.))"# u_perp = -ET.n_perp (where n_perp is n with phi->phi-pi/2) 

nJetGood_binning = [1, 2, 3, 4, 10 ]
qt_binning    = [0, 50, 100, 150, 200, 300 ]
u_para_binning   = [ i for i in range(-200, 201) ] if args.fine else [ i*5 for i in range(-40, 41) ]

nJetGood_bins = [ (nJetGood_binning[i],nJetGood_binning[i+1]) for i in range(len(nJetGood_binning)-1) ]
qt_bins = [ (qt_binning[i],qt_binning[i+1]) for i in range(len(qt_binning)-1) ]

#
# Loop over channels
#

# Selection & weights 
if args.year == 2016:
  data_sample = Run2016
  data_sample.texName = "data (2016)"
elif args.year == 2017:
  data_sample = Run2017
  data_sample.texName = "data (2017)"
elif args.year == 2018:
  data_sample = Run2018
  data_sample.texName = "data (2018)"

data_sample.name           = "data"
data_sample.style          = styles.errorStyle(ROOT.kBlack)

# Data weight & cut 
weightString =  "weight"
data_sample.setSelectionString([getFilterCut(isData=True, year=args.year), getLeptonSelection(args.mode), cutInterpreter.cutString(args.selection)])
data_sample.setWeightString( weightString )

# HEM flag
if args.preHEM:
    data_sample.addSelectionString("run<319077")
if args.postHEM:
    data_sample.addSelectionString("run>=319077")

# MC weight & cut
for sample in mc:
  weightString =  "weight*reweightPU36fb*reweightDilepTrigger*reweightLeptonSF*reweightBTag_SF*reweightLeptonTrackingSF"
  sample.setSelectionString([getFilterCut(isData=False, year=args.year), getLeptonSelection(args.mode), cutInterpreter.cutString(args.selection)])
  sample.setWeightString(weightString)

stack = Stack(mc, data_sample)

lumi_scale                 = data_sample.lumi/1000
if args.preHEM:   lumi_scale *= 0.37
if args.postHEM:  lumi_scale *= 0.63

data_sample.scale          = 1.

for sample in mc:
    sample.scale          = lumi_scale

# small 
if args.small:
    for sample in stack.samples:
        sample.normalization = 1.
        sample.reduceFiles( factor = 40 )
        sample.scale /= sample.normalization

pickle_file = os.path.join(output_directory, 'recoil_%s.pkl'%args.mode )
if not os.path.exists( output_directory ): 
    os.makedirs( output_directory )
if not os.path.isfile( pickle_file ) or args.overwrite:
    # Make 3D plot to get u_para/u_perp for in nJet and qt bins
    h3D_u_para = {}
    h3D_u_perp = {}
    for sample in stack.samples:
        h3D_u_para[sample.name] = sample.get3DHistoFromDraw("nJetGood:dl_pt:"+u_para, [u_para_binning,qt_binning,nJetGood_binning], binningIsExplicit=True)
        h3D_u_perp[sample.name] = sample.get3DHistoFromDraw("nJetGood:dl_pt:"+u_perp, [u_para_binning,qt_binning,nJetGood_binning], binningIsExplicit=True)
        h3D_u_para[sample.name].Scale(sample.scale)
        h3D_u_perp[sample.name].Scale(sample.scale)

    # Projections and bookkeeping
    u_para_proj = {}
    u_perp_proj = {}
    for prefix, u_proj, h3D_u in  [ [ "para", u_para_proj, h3D_u_para], [ "perp", u_perp_proj, h3D_u_perp ] ]:
        for h_name, h in h3D_u.iteritems():
            u_proj[h_name] = {}
            for nJetGood_bin in nJetGood_bins:
                u_proj[h_name][nJetGood_bin] = {}
                i_jet_min = h.GetZaxis().FindBin(nJetGood_bin[0]) 
                i_jet_max = h.GetZaxis().FindBin(nJetGood_bin[1]) 
                for qt_bin in qt_bins:
                    i_qt_min = h.GetYaxis().FindBin(qt_bin[0]) 
                    i_qt_max = h.GetYaxis().FindBin(qt_bin[1]) 
                    u_proj[h_name][nJetGood_bin][qt_bin] = h.ProjectionX("Proj_%s_%s_%i_%i_%i_%i"%( h_name, prefix, i_qt_min, i_qt_max-1, i_jet_min, i_jet_max-1), i_qt_min, i_qt_max-1, i_jet_min, i_jet_max-1) 

    pickle.dump( [u_para_proj, u_perp_proj], file( pickle_file, 'w' ) )
    logger.info( "Written pkl %s", pickle_file )
else:
    logger.info( "Loading pkl %s", pickle_file )
    u_para_proj, u_perp_proj = pickle.load( file( pickle_file ) )

fitResults = {}
for nJetGood_bin in nJetGood_bins:
    fitResults[nJetGood_bin] = {}
    for qt_bin in qt_bins:
        fitResults[nJetGood_bin][qt_bin] = {}
        for prefix, u_proj in  [ [ "para", u_para_proj], [ "perp", u_perp_proj ] ]:
            fitResults[nJetGood_bin][qt_bin][prefix] = {'mc':{},'data':{}}
            # Get histos
            histos =  map_level( lambda s: u_proj[s.name][nJetGood_bin][qt_bin], stack, 2 )
            # Transfer styles & text
            for i_l, l in enumerate(stack):
                for i_s, s in enumerate(l):
                    histos[i_l][i_s].style      = s.style
                    histos[i_l][i_s].legendText = s.texName

#            name = "u_%s_nJet_%i_%i_qt_%i_%i"%( prefix, nJetGood_bin[0], nJetGood_bin[1], qt_bin[0], qt_bin[1] )
#            if name!="u_para_nJet_0_1_qt_150_200":continue

            # make plot
            name = "u_%s_nJet_%i_%i_qt_%i_%i"%( prefix, nJetGood_bin[0], nJetGood_bin[1], qt_bin[0], qt_bin[1] )
            plot =  Plot.fromHisto( name = name, 
                    histos = histos, 
                    texX = "u_{#parallel}" if prefix == "para" else "u_{#perp}" ) 
            # fit
            h_mc   = plot.histos_added[0][0].Clone()
            h_data = plot.histos_added[1][0].Clone()
            h_mc.Scale(h_data.Integral()/h_mc.Integral())

            drawObjects = []
            f_mc = ROOT.TF1(name+'_mc', "[3]+[0]*exp(-0.5*((x-[1])/[2])**2)")
            f_mc.SetParameter(0, 1)
            f_mc.SetParameter(1, 0)
            #f_mc.SetParLimits(1,-20,20)
            f_mc.SetParameter(2, 20)
            #f_mc.SetParLimits(2,10,50)
            f_mc.SetParameter(3, 0)

            ##f_mc = ROOT.TF1(name+'_mc', "[3]+[0]*((1+(x-[1])**2/((2+6/[4])*[2]**2))**(-2.5-3/[4])*ROOT::Math::tgamma(2.5+3/[4]))/-(sqrt(pi)*sqrt(2+6/[4])*[2]*ROOT::Math::tgamma(2+3/[4]))" )
            ##f_mc = ROOT.TF1(name+'_mc', "[3]+[0]*((1+(x-[1])**2/((2.+6./[4])*[2]**2))**(-2.5-3./[4])*ROOT::Math::tgamma(2.5+3./[4]))/(sqrt(pi)*sqrt(2.+6./[4])*[2]*ROOT::Math::tgamma(2.+3./[4]))",-70,70)
            #f_mc = ROOT.TF1(name+'_mc', "[3]+[0]*((1+(x-[1])**2/((2+6*[4])*[2]**2))**(-2.5-3*[4])*ROOT::Math::tgamma(2.5+3*[4]))/(sqrt(pi)*sqrt(2+6*[4])*[2]*ROOT::Math::tgamma(2+3*[4]))")
            ##f_mc = ROOT.TF1(name+'_mc', "[3]+[0]*exp(-0.5*((x-[1])/[2])**2)")
            #f_mc.SetParameter(0, 100)
            #f_mc.SetParameter(1, 0)
            ##f_mc.SetParLimits(1,-20,20)
            #f_mc.SetParameter(2, 20)
            ##f_mc.SetParLimits(2,10,50)
            #f_mc.SetParameter(3, 0)
            #f_mc.SetParameter(4, 20)
            #f_mc.SetParLimits(4,1,20)

            if h_mc.Integral()>0:
                fitResult = h_mc.Fit(f_mc,"S")
                if fitResult:
                    fr = fitResult.Get()
                    fitResults[nJetGood_bin][qt_bin][prefix]['mc'] = {'mean':fr.GetParams()[1], 'sigma':fr.GetParams()[2], 'mean_error':fr.GetErrors()[1], 'sigma_error':fr.GetErrors()[2]} 
                h_mc_fit = h_mc.Clone()
                h_mc_fit.Reset()
                for i in range(1, 1+h_mc_fit.GetNbinsX()):
                    h_mc_fit.SetBinContent( i, f_mc.Eval(h_mc_fit.GetBinCenter(i)) )
                h_mc_fit.style = styles.lineStyle( ROOT.kRed )
                h_mc_fit.legendText = "fit (MC)"
                plot.histos.append( [h_mc_fit] )
                fitResults[nJetGood_bin][qt_bin][prefix]['mc']['TF1']      = f_mc 
                fitResults[nJetGood_bin][qt_bin][prefix]['mc']['TH1F']     = h_mc 
                fitResults[nJetGood_bin][qt_bin][prefix]['mc']['TH1F_fit'] = h_mc_fit 

            f_data = ROOT.TF1(name+'_data', "[3]+[0]*exp(-0.5*((x-[1])/[2])**2)")
            f_data.SetParameter(0, 1)
            f_data.SetParameter(1, 0)
            #f_data.SetParLimits(1,-20,20)
            f_data.SetParameter(2, 20)
            #f_data.SetParLimits(2,10,50)
            f_data.SetParameter(3, 0)
            #f_data = ROOT.TF1(name+'_data', "[3]+[0]*((1+(x-[1])**2/((2+6*[4])*[2]**2))**(-2.5-3*[4])*ROOT::Math::tgamma(2.5+3*[4]))/(sqrt(pi)*sqrt(2+6*[4])*[2]*ROOT::Math::tgamma(2+3*[4]))")
            ##f_data = ROOT.TF1(name+'_data', "[3]+[0]*exp(-0.5*((x-[1])/[2])**2)")
            #f_data.SetParameter(0, 100)
            #f_data.SetParameter(1, 0)
            ##f_data.SetParLimits(1,-20,20)
            #f_data.SetParameter(2, 20)
            ##f_data.SetParLimits(2,10,50)
            #f_data.SetParameter(3, 0)
            #f_data.SetParameter(4, 20)
            #f_data.SetParLimits(4,1,30)
            if h_data.Integral()>0:
                fitResult = h_data.Fit(f_data,"S")
                if fitResult:
                    fr = fitResult.Get()
                    fitResults[nJetGood_bin][qt_bin][prefix]['data'] = {'mean':fr.GetParams()[1], 'sigma':fr.GetParams()[2], 'mean_error':fr.GetErrors()[1], 'sigma_error':fr.GetErrors()[2]} 
                h_data_fit = h_data.Clone()
                h_data_fit.Reset()
                for i in range(1, 1+h_data_fit.GetNbinsX()):
                    h_data_fit.SetBinContent( i, f_data.Eval(h_data_fit.GetBinCenter(i)) )
                h_data_fit.style = styles.lineStyle( ROOT.kBlue )
                h_data_fit.legendText = "fit (Data)"
                plot.histos.append( [h_data_fit] )
                fitResults[nJetGood_bin][qt_bin][prefix]['data']['TF1']      = f_data 
                fitResults[nJetGood_bin][qt_bin][prefix]['data']['TH1F']     = h_data 
                fitResults[nJetGood_bin][qt_bin][prefix]['data']['TH1F_fit'] = h_data_fit 
 
                #mean_data, mean_error_data, sigma_data, sigma_error_data, pdf = GaussianFit( h_data, isData = True, var_name = "u_%s"%prefix )
                #f_data = ROOT.TF1("gauss","gaus(0)",u_para_binning[0],u_para_binning[-1])
                #f_data.SetParameter(0, h_data.Integral() ) 
                #f_data.SetParameter(1, mean_data ) 
                #f_data.SetParameter(2, sigma_data ) 
                #extraDrawObjects.append( f_data )

            drawObjects.append( tex.DrawLatex(0.5, 0.85, 'data: #mu=% 3.2f #sigma=% 3.2f'%( f_data.GetParameter(1), f_data.GetParameter(2)) ) )
            drawObjects.append( tex.DrawLatex(0.5, 0.80, 'MC:  #mu=% 3.2f #sigma=% 3.2f'%( f_mc.GetParameter(1), f_mc.GetParameter(2)) ) )

            #drawObjects.append( tex.DrawLatex(0.5, 0.85, 'data: #mu=% 3.2f #sigma=% 3.2f'%( mean_data, sigma_data) ) )
            #drawObjects.append( tex.DrawLatex(0.5, 0.80, 'MC:  #mu=% 3.2f #sigma=% 3.2f'%( mean_mc, sigma_mc) ) )
            # draw
            drawPlots( [ plot ],  mode = args.mode, dataMCScale = -1, drawObjects = drawObjects )

pickle_file = os.path.join(output_directory, 'recoil_fitResults_%s.pkl'%args.mode )
pickle.dump( fitResults, file( pickle_file, 'w' ) )
logger.info( "Written pkl %s", pickle_file )
