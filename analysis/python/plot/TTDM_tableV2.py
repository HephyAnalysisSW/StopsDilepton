
import pickle
from StopsDilepton.samples.cmgTuples_FullSimTTbarDM_mAODv2_25ns_postProcessed import *
from StopsDilepton.tools.user import combineReleaseLocation, analysis_results, plot_directory

categories = []
mChi_list = []
mPhi_list = []

nScalar = 0
nPseudo = 0

blinded = False

for s in DMsamples:
    if not s[0] in mChi_list: mChi_list.append(s[0])
    if not s[1] in mPhi_list: mPhi_list.append(s[1])
    if not s[2] in categories: categories.append(s[2])
    if s[2] == 'S':
        nScalar += 1
        

nPseudo = len(categories) - nScalar

#res = pickle.load(file(os.path.join(analysis_results,"aggregated","fitAll","cardFiles","TTbarDM","calculatedLimits.pkl")))
res = pickle.load(file(os.path.join(analysis_results,"fitAll","cardFiles","TTbarDM_EXOapp","calculatedLimits.pkl")))

texdir = os.path.join(plot_directory,'DMLimits_EXOapp')
if not os.path.exists(texdir): os.makedirs(texdir)
if blinded:
    ofile = texdir+'/limits_update_blind.tex'
else:
    ofile = texdir+'/limits_update.tex'

with open(ofile, "w") as f:
    f.write("\\documentclass[a4paper,10pt,oneside]{article} \n \\usepackage{caption} \n \\usepackage{rotating} \n \\usepackage{multirow} \n \\begin{document} \n")
    
    f.write("\n \\begin{table} \n\\begin{tabular}{cc||ccc|ccc} \n")

    f.write("&&\multicolumn{3}{c|}{scalar}&\multicolumn{3}{c}{pseudoscalar}\\\\")
    f.write("$m_{\\chi}$ (GeV) & $m_{\\phi/a}$ (GeV) & exp. & $\pm$ 1 s.d. & obs. & exp. & $\pm$ 1 s.d. & obs. \\\\ \n \\hline \n")
    #for cat in categories:
    #    if cat=='S':
    #        catname = "scalar"
    #        catsymbol = '$\phi$'
    #    elif cat=='PS':
    #        catname = "pseudoscalar"
    #        catsymbol = 'a'
    #    else: catname = "unknown"


    fbase = "{:10}{:10}{:10}{:20}{:10}{:10}{:20}{:10}"
    #line = ["\\multirow{"+str(len(res)/2)+"}{*}{"+catsymbol+"}"]
    for mChi in sorted(mChi_list):
        f.write("\n \\hline \n")
        print mChi
        for mPhi in sorted(mPhi_list):
            print mPhi
            #line += ['& ' + str(mChi),'& ' + str(mPhi)]
            line = [str(mChi),'& ' + str(mPhi)]
            limit = {}

            try:
                lA = res[(mChi,mPhi,'PS')]
            except KeyError:
                lA = None
            #print lA
            try:
                lPhi = res[(mChi,mPhi,'S')]
            except KeyError:
                lPhi = None
            #print lPhi
            if lA:
                try:
                    limit['a_obs'] = lA['-1.000']
                except KeyError:
                    pass
                try:
                    limit['a_exp'] = lA['0.500']
                    if lA['0.160']<1 and lA['0.840']<1:
                        limit['a_exp_band'] = '[%.2g, %.2g]'%(lA['0.160'], lA['0.840'])
                    elif lA['0.160']<1 and lA['0.840']>1:
                        limit['a_exp_band'] = '[%.2g, %.3g]'%(lA['0.160'], lA['0.840'])
                    else:
                        limit['a_exp_band'] = '[%.3g, %.3g]'%(lA['0.160'], lA['0.840'])
                except KeyError:
                    pass
            if lPhi:
                try:
                    limit['phi_obs'] = lPhi['-1.000']
                except KeyError:
                    pass
                try:
                    limit['phi_exp'] = lPhi['0.500']
                    if lPhi['0.160']<1 and lPhi['0.840']<1:
                        limit['phi_exp_band'] = '[%.2g, %.2g]'%(lPhi['0.160'], lPhi['0.840'])
                    elif lA['0.160']<1 and lA['0.840']>1:
                        limit['phi_exp_band'] = '[%.2g, %.3g]'%(lPhi['0.160'], lPhi['0.840'])
                    else:
                        limit['phi_exp_band'] = '[%.3g, %.3g]'%(lPhi['0.160'], lPhi['0.840'])
                except KeyError:
                    pass

            keys = ['phi_exp', 'phi_exp_band', 'phi_obs','a_exp', 'a_exp_band', 'a_obs']
            for k in keys:
                if limit.has_key(k):
                    if blinded and ('obs' in k): line.append("& ")
                    else:
                        if limit[k] < 1000:
                            if limit[k] < 1:    line.append( "& %.2g"%(limit[k]) )
                            else:               line.append( "& %.3g"%(limit[k]) )
                        elif str(limit[k]).startswith('['):
                            line.append( "& %s"%limit[k] )
                        else:
                            line.append("& $\\gg 1$ ")
                else: line.append("& ")
            #if exp:
            #    if obs<1000: line.append("& " + str(round(exp,1)))
            #    else: line.append("& $\\gg 1$ ")
            #else: line.append("& ")
            #if obs:
            #    if obs<1000: line.append("& " + str(round(obs,1)))
            #    else: line.append("& $\\gg 1$ ")
            #else: line.append("& ")
            if limit:
                print fbase.format(*line)
                f.write(fbase.format(*line)+"\\\\ \n") # \n \\hline
            #line = [' ']

    f.write(" \n \\end{tabular}")
    f.write(" \\caption{Observed and expected limits.} \n ")
    f.write(" \\end{table} \n")
        

    f.write(" \\end{document}")

os.system("cd "+texdir+";pdflatex "+ofile)



