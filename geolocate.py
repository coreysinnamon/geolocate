from parse import *
from hiddenprints import *
import localization as lx
import numpy as np


modes = ["2/3indep", "4/9indep", "bestline", "routers"]
#Use client-independent
#mode = modes[2]
#Use client-dependent
mode = modes[2]

#localization object for performing multilateration
#LSE_GC refers to "least square error with geometric constraints"
#geometric constraints force the solutions to be in the intersection areas of all multilateration circles
P = lx.Project(mode = 'Earth1', solver='LSE_GC')

#reverse switches tuple order of a pair
#useful because localization module uses (long, lat) format
def reverse(pair):
    return (pair[1], pair[0])

#anchor data:
num_anchors = 11
anchor_names = ["prin", "cali", "cana", "ohio", "oreg", "virg", "gcali", "gcaro", "giowa", "goreg", "gvirg"]
anchor_locs = [reverse(here_prin), reverse(here_cali), reverse(here_cana),
                reverse(here_ohio), reverse(here_oreg), reverse(here_virg),
                reverse(here_goog_cali), reverse(here_goog_caro), reverse(here_goog_iowa),
                reverse(here_goog_oreg), reverse(here_goog_virg)]
anchor_outliers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
block_matrix = [blocks_prin, blocks_cali, blocks_cana, blocks_ohio, blocks_oreg, blocks_virg,
                blocks_goog_cali, blocks_goog_caro, blocks_goog_iowa, blocks_goog_oreg, blocks_goog_virg]

#this array allows you to ignore some anchors
used_anchors = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

#add anchors
for a in used_anchors:
   P.add_anchor(anchor_names[a], anchor_locs[a])

#number of targets in data set (roughly 55)
num_targets = len(block_matrix[0])

speed_of_light = 299792458
def estim_dist(anchor, targ):
    #account for inaccurate lat/long
    dist_error = 50000
    too_close = 100000
    if mode == "2/3indep":
        return max(too_close, ((targ.ping_min/1000)/2)*2/3*speed_of_light + dist_error)
    if mode == "4/9indep":
        return max(too_close, ((targ.ping_min/1000)/2)*4/9*speed_of_light + dist_error)
    if mode == "bestline":
        slope = minslope(a, too_close, anchor_outliers[a])
        return max(too_close, targ.ping_min/slope + dist_error)


def minslope(a, too_close, outliers):
    locblocks = block_matrix[a]
    here = anchor_locs[a]
    dist_data = [great_circle_dist(here[0], here[1], block.lon, block.lat) for block in locblocks]
    min_data = [block.ping_min for block in locblocks]
    
    slopes = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close and min_data[i] > 0:
            slopes.append(min_data[i]/dist_data[i])
    return 0.98*sorted(slopes)[outliers]

#this is the Earth-surface distance function used by the localization modules
def great_circle_dist(lon1, lat1, lon2 ,lat2):
    return lx.geometry.E.gcd(lon1, lat1, lon2, lat2)

def actual_dist(anchor, targ):
    here = anchor_locs[anchor]
    return great_circle_dist(here[0], here[1], targ.lon, targ.lat)

#output True if the target specified by targ_index is within the intersection of circles
def targ_lies_in_intersection(targ_index):
    contained = True

    for a in used_anchors:
        targ = block_matrix[a][targ_index]
        #ignore degenerate data blocks blocks
        if good_block(targ) and actual_dist(a, targ) > estim_dist(a, targ):
            contained = False
    return contained


#create targets and input distance estimates from each anchor to each target
targs = [None for i in range(num_targets)]
labels = ["Null" for i in range(num_targets)]
#t is the target object and label is the package provided label for the target.
for i in range(num_targets):
    #creates a target object and adds it to model (localization module)
    targs[i], labels[i] = P.add_target()

    for a in used_anchors:

        #avoids degenerate data points
        if good_block(block_matrix[a][i]):
            targs[i].add_measure(anchor_names[a], estim_dist(anchor_names[a], block_matrix[a][i]))
    
#use localization module to solve for locations of all targets
#suppress print commands in P.solve()
#with HiddenPrints():
P.solve()

#print statistics about the inferred vs actual locations of targets
def show_multilat_data():
    error_list = []
    num_successes = 0

    for i in range(num_targets):
        true_loc = (block_matrix[0][i].lon, block_matrix[0][i].lat)
        #if target could be resolved, then compare actual and inferred locations
        if targs[i] and targs[i].loc:
            dist_error = great_circle_dist(true_loc[0], true_loc[1], targs[i].loc.x, targs[i].loc.y)
            
            error_list.append(dist_error)
        else:
            dist_error = -1
        #print(str(i) + " - " + block_matrix[0][i].loc + " : " + str(targs[i].loc) + "              " + str(true_loc) + "           Error : " + str(round(dist_error/1000)) + " km")
        print(str(i) + " - (" + block_matrix[0][i].loc + ") Error : " + str(round(dist_error/1000)) + " km")

    print("Average Error: " + str(round(sum(error_list)/len(error_list)/1000)) + " km")
    print("Median Error: " + str(round(np.median(error_list)/1000)) + " km")
    #print(error_list)

#print distances between pairs of anchors
def show_pairwise_anchor_distances():
    for a in range(num_anchors):
        for b in range(a+1, num_anchors):
            print(anchor_names[a] + " to " + anchor_names[b] + ": " + str((great_circle_dist(anchor_locs[a][0], anchor_locs[a][1], anchor_locs[b][0], anchor_locs[b][1])/1000)) + " km")

#which targets do not lie in the intersection of circles?
#print some info about these failures
def show_intersection_failures():
    for i in range(num_targets):
        #print(str(i) + ": " + block_matrix[0][i].loc + "    " + str(targ_lies_in_intersection(i)))
        if not(targ_lies_in_intersection(i)):
            print(str(i) + ": " + block_matrix[0][i].loc)
            for a in used_anchors:
                #ignore degenerate data blocks
                if good_block(block_matrix[a][i]):
                    est = estim_dist(a, block_matrix[a][i])
                    act = actual_dist(a, block_matrix[a][i])
                    print("       " + anchor_names[a] + " : Estimated "+ str(est/1000) + " km,  but actual is " + str(act/1000) + " km. Difference: " + str(round((est-act)/1000)) + " km")

#how close are the estimated distances to actual distances?
#for each target, print the estimated distance to anchor a, actual distance to a, and the ratio
def show_estimation_accuracy(a): 
    too_close = 500000
    rat = []
    for i in range(num_targets):
            #ignore degenerate data blocks
        if good_block(block_matrix[a][i]):
            est = estim_dist(a, block_matrix[a][i])
            act = actual_dist(a, block_matrix[a][i])
            if act > too_close:
                #print("Estimate: "+ str(estim_dist(a, block_matrix[a][i])) + "             Actual: " + str(act) + "            Ratio: " +str(est/act))
                rat.append(est/act)

    print(anchor_names[a] + " Average Ratio: " + str(sum(rat)/len(rat)))
    

show_multilat_data()

show_intersection_failures()
