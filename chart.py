import re
import geopy.distance
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from parse import *
import localization as lx

def great_circle_dist(lon1, lat1, lon2 ,lat2):
    return lx.geometry.E.gcd(lon1, lat1, lon2, lat2)/1000

def minslope(locblocks, here):
    dist_data = [great_circle_dist(here[1], here[0], block.lon, block.lat) for block in locblocks]
    min_data = [block.ping_min for block in locblocks]
    too_close = 100
    slopes = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close and min_data[i] > 0:
            slopes.append(min_data[i]/dist_data[i])
    return sorted(slopes)[0]

def chart(locblocks, here, title, outliers):
    plt.figure()
    dist_data = [dist(here, (block.lat, block.lon)) for block in locblocks]
    min_data = [block.ping_min for block in locblocks]
    
    too_close = 400
    dist_error = 10
    slope = minslope(locblocks, here)
    
    xs = []
    ys = []
    outxs = []
    outys = []

    too_close = 100
    for i in range(0, len(min_data)):
        if True or (min_data[i] > slope*dist_data[i]) or dist_data[i] < too_close:
            xs.append(dist_data[i])
            ys.append(min_data[i])
        else:
            outxs.append(dist_data[i])
            outys.append(min_data[i])
    plt.scatter(xs, ys)
    #plt.scatter(outxs, outys)
    plt.xlim(0,4500)
    plt.ylim(0,100)
    plt.title(title)
    plt.xlabel('Geographical Distance (km)')
    plt.ylabel('Minimum RTT (ms)')
    # lower bound line
    plt.plot([0,5500],[0, slope*5500], color='black')
    # best fit line
    # bestfit = np.poly1d(np.polyfit(xs, ys, 1))
    # plt.plot([0,5500], bestfit([0, 5500]), color='red')
    speed_of_light = 299792458
    plt.plot([0,5500],[0, 1000000/(2/9*speed_of_light)*5500], 'r--')

def chart3d(locblocks, here, title, z_max, outliers):
    dist_data = [dist(here, (block.lat, block.lon)) for block in locblocks]
    min_data = [block.ping_min for block in locblocks]
    num_data = [block.trace_num for block in locblocks]

    
    too_close = 2000
    dist_error = 100
    slopes = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close:
            slopes.append(min_data[i]/(dist_data[i] + dist_error))
    slope = sorted(slopes)[outliers]
    
    xs = []
    ys = []
    zs = []
    outxs = []
    outys = []
    outzs = []

    for i in range(0, len(min_data)):
        if min_data[i] > slope*dist_data[i] or dist_data[i] < too_close:
            xs.append(dist_data[i])
            ys.append(num_data[i])
            zs.append(min_data[i])
        else:
            outxs.append(dist_data[i])
            outys.append(num_data[i])
            outzs.append(min_data[i])
            
    
    #plt.plot([0,5500],[0, 0.97*slope*5500])
    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('Geographical Distance (km)')
    ax.set_ylabel('Number of Routers')
    ax.set_zlabel('Minimum RTT (ms)')
    ax.set_xlim(0,4500)
    ax.set_ylim(0,30)
    ax.set_zlim(0,z_max)
    ax.set_title(title)
    
    ax.scatter(xs,ys,zs)
    
    # create x,y
    xx, yy = np.meshgrid(range(4501), range(31))

    # calculate corresponding z
    z = slope*xx

    # plot the surface
    ax.plot_surface(xx, yy, z, color='red', alpha=0.1)

#for block in blocks_cali:
#   if dist(here_cali, (block.lat, block.lon)) > 300 and block.ping_min<25:
#       print(block.loc + ": " + str(dist(here_cali, (block.lat, block.lon)))+", "+str(block.ping_min))


from scipy.stats import norm
from sklearn.neighbors import KernelDensity

def fit_distr(locblocks, here, title, outliers):
    
    dist_data = [dist(here, (block.lat, block.lon)) for block in locblocks]
    min_data = [block.ping_min for block in locblocks]

    too_close = 2000
    dist_error = 100
    slopes = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close:
            slopes.append(min_data[i]/(dist_data[i] + dist_error))
    slope = sorted(slopes)[outliers]
    
    xs = []
    ys = []
    outxs = []
    outys = []

    too_close = 500
    for i in range(0, len(min_data)):
        if min_data[i] > slope*dist_data[i] or dist_data[i] < too_close:
            xs.append(dist_data[i])
            ys.append(min_data[i])
        else:
            outxs.append(dist_data[i])
            outys.append(min_data[i])
            

    bestfit = np.poly1d(np.polyfit(xs, ys, 1))

   
    x_min = 1.2
    x_max = 1.6
    x_delta = x_max - x_min
    smooth = 0.5
    intercept = bestfit(0)
    distortion = 50
    rescaling = 450
    res = 1000
    too_close = 500
    angles = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close:
            angles.append(np.arctan(max(0, min_data[i]-intercept)*rescaling/dist_data[i])*distortion)
    angles = sorted(angles)[outliers:]
    X = [[a] for a in angles]
    X_plot = np.linspace(x_min*distortion, x_max*distortion, res)[:, np.newaxis]

    # Gaussian KDE
    kde = KernelDensity(kernel='gaussian', bandwidth=0.9).fit(X)
    log_dens = kde.score_samples(X_plot)

    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111)
   
    log_dens = kde.score_samples(X_plot)
    ax.fill(X_plot[:, 0], np.exp(log_dens), fc='#AAAAFF')
    #ax.text(-3.5, 0.4, "Gaussian Kernel Density")

    ax.set_ylabel('Normalized Density')
    ax.set_xlabel(r'RTT/Distance ($\mu$sec/km)')
    ax.set_title(title)
    ax.scatter(angles, [-0.001 for i in angles], color='black', marker='+')


def distr_chart(locblocks, here, title, outliers):
    plt.figure()
    dist_data = [dist(here, (block.lat, block.lon)) for block in locblocks]
    min_data = [block.ping_min for block in locblocks]
    
    too_close = 2000
    dist_error = 100
    slopes = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close:
            slopes.append(min_data[i]/(dist_data[i] + dist_error))
    slope = sorted(slopes)[outliers]
    
    xs = []
    ys = []
    outxs = []
    outys = []

    too_close = 500
    for i in range(0, len(min_data)):
        if min_data[i] > slope*dist_data[i] or dist_data[i] < too_close:
            xs.append(dist_data[i])
            ys.append(min_data[i])
        else:
            outxs.append(dist_data[i])
            outys.append(min_data[i])
            
    plt.scatter(xs, ys)
    #plt.scatter(outxs, outys)
    plt.xlim(0,4500)
    plt.ylim(0,100)
    plt.title(title)
    plt.xlabel('Geographical Distance (km)')
    plt.ylabel('Minimum RTT (ms)')
    # lower bound line
    plt.plot([0,5500],[0, 0.97*slope*5500], color='black')
    # best fit line
    bestfit = np.poly1d(np.polyfit(xs, ys, 1))
    plt.plot([0,5500], bestfit([0, 5500]), color='red')


    x_min = 1
    x_max = 1.8
    x_delta = x_max - x_min
    smooth = 1
    intercept = bestfit(0)
    distortion = 50
    rescaling = 450
    res = 5000
    too_close = 500
    angles = []
    for i in range(0,len(dist_data)):
        if dist_data[i] > too_close:
            angles.append(np.arctan(max(0, min_data[i]-intercept)*rescaling/dist_data[i])*distortion)
    angles = sorted(angles)[outliers:]
    X = [[a] for a in angles]
    X_plot = np.linspace(x_min*distortion, x_max*distortion, res)[:, np.newaxis]

    # Gaussian KDE
    kde = KernelDensity(kernel='gaussian', bandwidth=0.9).fit(X)
    log_dens = kde.score_samples(X_plot)

    fullres = int(np.pi/2*res/x_delta)+1
    density = []
    for i in range(0,fullres):
      if i >= x_min/(np.pi/2)*fullres and  i <= x_max/(np.pi/2)*fullres:
        density.append(np.exp(log_dens[int((i - x_min/(np.pi/2)*fullres)/(x_delta/(np.pi/2)*fullres)*res)])**smooth)
      else:
        density.append(0)
  
    d = [i for i in range(1, 4501, 3)]
    t = [i for i in range(1, 101, 1)]
    c = [[density[int(np.arctan(max(0, t[j]-intercept)*rescaling/d[i])/(np.pi/2)*fullres)] for i in range(1, len(d))] for j in range(1, len(t))]
    #c = [[np.exp(log_dens[int((np.arctan(b[j]*rescaling/a[i])*distortion)*fullres)]) for i in range(1, len(a))] for j in range(1, len(b))]
    #d = np.random.random_integers(0, 1, (100, 4500))
    #cmap = mpl.colors.ListedColormap()#['b', 'y', 'r'])
    #bounds = [0., 0.1, 1.]
    #norm = mpl.colors.BoundaryNorm(bounds, 2)
    plt.imshow(c, interpolation='nearest', cmap='YlOrRd', aspect='auto', origin='lower', extent=[0, 4500, 0, 100], alpha=0.65)

def chart_routers(locblocks, here, title, outliers):
    plt.figure()
    dist_data = [dist(here, (block.lat, block.lon)) for block in locblocks]
    router_data = [block.trace_num for block in locblocks]
        
    xs = dist_data
    ys = router_data
    
    plt.scatter(xs, ys)
    #plt.scatter(outxs, outys)
    plt.xlim(0,4500)
    plt.ylim(0,35)
    plt.title(title)
    plt.xlabel('Geographical Distance (km)')
    plt.ylabel('Number of Routers')

#CHART RTT AGAINST DISTANCE
# chart(blocks_prin, here_prin, "Princeton",  0)
# chart(blocks_cali, here_cali, "Amazon California",  0)
# chart(blocks_cana, here_cana, "Amazon Quebec", 0)
# chart(blocks_ohio, here_ohio, "Amazon Ohio", 0)
# chart(blocks_oreg, here_oreg, "Amazon Oregon", 0)
# chart(blocks_virg, here_virg, "Amazon Virginia", 0)

# chart(blocks_goog_cali, here_goog_cali, "Google California",  0)
# chart(blocks_goog_caro, here_goog_caro, "Google Carolina", 0)
# chart(blocks_goog_iowa, here_goog_iowa, "Google Iowa", 0)
# chart(blocks_goog_oreg, here_goog_oreg, "Google Oregon", 0)
# chart(blocks_goog_virg, here_goog_virg, "Google Virginia",0)

#3-DIMENSION USING ROUTERS AND RTT
#chart3d(blocks_cali, here_cali, "California", 100, 5)
#chart3d(blocks_cana, here_cana, "Canada", 100, 2)
#chart3d(blocks_ohio, here_ohio, "Ohio", 100, 2)
#chart3d(blocks_oreg, here_oreg, "Oregon", 100, 3)
#chart3d(blocks_virg, here_virg, "Virginia", 100, 2)

#ROUTERS
# chart_routers(blocks_prin, here_prin, "Princeton",  0)
# chart_routers(blocks_cali, here_cali, "California",  4)
# chart_routers(blocks_cana, here_cana, "Canada", 0)
# chart_routers(blocks_ohio, here_ohio, "Ohio", 0)
# chart_routers(blocks_oreg, here_oreg, "Oregon", 4)
# chart_routers(blocks_virg, here_virg, "Virginia", 0)

# chart_routers(blocks_goog_cali, here_goog_cali, "Google California",  5)
# chart_routers(blocks_goog_caro, here_goog_caro, "Google Carolina", 2)
# chart_routers(blocks_goog_iowa, here_goog_iowa, "Google Iowa", 1)
# chart_routers(blocks_goog_oreg, here_goog_oreg, "Google Oregon", 3)
# chart_routers(blocks_goog_virg, here_goog_virg, "Google Virginia",0)


#DISTRIBUTIONAL (not in the paper)
#fit_distr(blocks_cana, here_cana, "Canada", 2)
#fit_distr(blocks_cali, here_cali, "California", 5)
#fit_distr(blocks_ohio, here_ohio, "Ohio", 2)
#fit_distr(blocks_oreg, here_oreg, "Oregon", 3)
#fit_distr(blocks_virg, here_virg, "Virginia", 2)


#DISTRIBUTIONAL (not in the paper)
#distr_chart(blocks_cali, here_cali, "California",  5)
#distr_chart(blocks_cana, here_cana, "Canada", 2)
#distr_chart(blocks_ohio, here_ohio, "Ohio", 2)
#distr_chart(blocks_oreg, here_oreg, "Oregon", 3)
#distr_chart(blocks_virg, here_virg, "Virginia",2)




plt.show()