from Analysis.Tools.cardFileWriter.CombineResults import CombineResults
cardFile = "/afs/hephy.at/data/cms05/StopsDileptonLegacy/results/v7/COMBINED/fitAll/cardFiles/T2tt/observed/T2tt_800_100.txt"
plotDirectory = "/afs/hephy.at/user/r/rschoefbeck/www/StopsDilepton/postFit"

Results = CombineResults( cardFile=cardFile, plotDirectory=plotDirectory, year=0, bkgOnly=True, isSearch=True )
yields = Results.getEstimates( postFit=True )

#L1p=Results.getNuisanceYields("L1prefire", postFit=True)
#SFb   =Results.getNuisanceYields("SFb_2016", postFit=True)
Lumi_2016 = Results.getNuisanceYields("Lumi_2016", postFit=True)

#unc    = Results.getUncertainties( postFit=True)


#cardFile  = "/afs/hephy.at/data/cms05/StopsDileptonLegacy/results/v7/2016/fitAll/cardFiles/T2tt/observed/T2tt_800_100.txt"
#cardFile = "/afs/hephy.at/data/llechner01/TTGammaEFT/cache/analysis/2016/limits/cardFiles/defaultSetup/observed/SR4pM3_VG4p_misDY4p_misTT2_incl.txt"


#signal         TTZ            TTJets         TTXNoZ         DY             multiBoson