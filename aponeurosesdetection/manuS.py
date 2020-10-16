"""
Processing of manual data for simple/standard images
Created on Thu Sep  3 16:52:58 2020

@author: Lisa Paillard
"""

def simpleManu(manu_pts_dict, path_img = None):
    
    import aponeurosesdetection.MUFeaM as MUFeaM
    import numpy as np
    import aponeurosesdetection.FaDe as FaDe
    import fnmatch

    calib = manu_pts_dict['calfct_to_mm']
    
    list_sup = list(manu_pts_dict['aposup']['coords'])
    list_sup.sort(key=lambda x:x[1])
    y_sup = [list_sup[i][1] for i in range(len(list_sup))]
    x_sup = [list_sup[i][0] for i in range(len(list_sup))]
    
    list_inf = list(manu_pts_dict['apoinf']['coords'])
    list_inf.sort(key=lambda x:x[1])
    y_inf = [list_inf[i][1] for i in range(len(list_inf))]
    x_inf = [list_inf[i][0] for i in range(len(list_inf))]

    #interpolation with Bspline        
    polyn_sup = np.polyfit(y_sup, x_sup, deg = 1)
    spline_sup = np.poly1d(polyn_sup)
    polyn_inf = np.polyfit(y_inf, x_inf, deg = 1)
    spline_inf = np.poly1d(polyn_inf)
    
    # features computation
    abscissa, thickness, splineT = MUFeaM.muscleThickness(start = max(min(y_sup), min(y_inf)), end = min(max(y_sup), max(y_inf)), calibV = calib, calibH = calib, spl1 = spline_sup, spl2 = spline_inf)
    manu_pts_dict['MT'] = {'coords': thickness, 'columns interval': [max(min(y_sup), min(y_inf)), min(max(y_sup), max(y_inf))]}
    
    for fsc in fnmatch.filter(manu_pts_dict.keys(), 'fsc_*'):
        fasci = manu_pts_dict[fsc]['coords']        

        #Bspline
        spl = FaDe.approximateFasc(typeapprox = 'polyfit', listF = [fasci], d = 1)
        #find intersection points with aponeuroses
        inters_inf, inters_sup, spl = MUFeaM.findIntersections(spl_inf = spline_inf, spl_sup = spline_sup,\
                                                               listSpl = spl, search_interval = [-200/calib,200/calib], start = 0)
        if len(spl)>0:
            #find pennation angles
            PA_sup = MUFeaM.pennationAngles(spl_a = spline_sup, listS_f = spl, listI = inters_sup, xcalib = calib, ycalib = calib)
            PA_inf = MUFeaM.pennationAngles(spl_a = spline_inf, listS_f = spl, listI = inters_inf, xcalib = calib, ycalib = calib)
            #calculate fascicle length
            FL = MUFeaM.fasciclesLength(listS_f = spl, listIu = inters_sup, listId = inters_inf, xcalib = calib, ycalib = calib)
            loc = MUFeaM.locateFasc(inters_inf, [0,0], calib)
            
            manu_pts_dict[fsc]['dist from (0,0) of RGB image, in mm'] = loc[0]
            manu_pts_dict[fsc]['PAsup'] = {'value in degree' : PA_sup[0],
                         'intersection with apo': inters_sup[0]}
            manu_pts_dict[fsc]['PAinf'] = {'value in degree' : PA_inf[0],
                         'intersection with apo': inters_inf[0]}
            manu_pts_dict[fsc]['FL'] = {'length in mm': FL[0]}
   
    return manu_pts_dict