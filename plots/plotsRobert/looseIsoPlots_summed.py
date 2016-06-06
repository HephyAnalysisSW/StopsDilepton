#Standard imports
import ROOT
from math import sqrt, cos, sin, pi, acos
import itertools
import pickle
import os

#user
from StopsDilepton.tools.user import plot_directory

#RootTools
from RootTools.core.standard import *

# Logging
import StopsDilepton.tools.logger as logger

logger = logger.get_logger('INFO', logFile = None )
histos = {}
for m in ['doubleMu', 'doubleEle', 'muEle']:
    plot_path = "png25ns_2l_mAODv2_2100_noPU_new/%s_offZ_standard_isOS-leadingLepIsTight-njet2-nbtag1-met80-metSig5-dPhiJet0-dPhiJet1/" % m
    for fh in ["leadingLepIso"]:
        for swap in ["L1", "L2"]:
            for fs in ["mm","me","em","ee"]:
                ofile = os.path.join(plot_directory, plot_path,  "dl_mt2ll_%s_swap%s_%s.pkl"%(fh, swap, fs))
                if os.path.isfile(ofile):
                    logger.info( "Loading %s", ofile )
                    histos["%s_mt2ll_%s_swap%s_%s"%(m, fh, swap, fs)] = pickle.load( file( ofile) )
                else:
                    logger.warning( "File not found: %s", ofile)

def transpose(l):
    return list(map(list, zip(*l)))

def add_histos( l ):
    res = l[0].Clone()
    for h in l[1:]: res.Add(h)
    return res

for name, fss in [
    ['doubleMu', ['mm']], 
    ['muEle', ['me', 'em']], 
    ['doubleEle', ['ee']]
    ]:
    to_be_added = []
    for key in histos.keys():
        if not any( key.endswith('_'+fs) for fs in fss): continue
        logger.info( "Adding to %s key %s", name, key )
        to_be_added.append( key )

    mc_histos = map( add_histos, transpose( [ histos[key][0] for key in to_be_added ] ) )
    data_histo = add_histos( [ histos[key][1][0] for key in to_be_added ] )
    data_histo.style = styles.errorStyle( ROOT.kBlack )

    dl_mt2ll  = Plot(
        name = "%s_dl_mt2ll"%name,
        texX = 'MT_{2}^{ll} (GeV)', texY = 'Number of Events / 15 GeV',
        stack = None, 
        variable = Variable.fromString( "dl_mt2ll/F" ),
        binning=[300/15,0,300],
        #selectionString = selectionString,
        #weight = weight,
        )
    dl_mt2ll.histos = [mc_histos, [data_histo]]

    ratio = {'yRange':(0.1,1.9)}
    plotting.draw(
        dl_mt2ll,
        plot_directory = plot_directory+'/etc/', ratio = ratio, 
        logX = False, logY = True, sorting = True,
         yRange = (0.003, "auto"), legend = None ,
        # scaling = {0:1},
        # drawObjects = drawObjects( dataMCScale )
    )
 