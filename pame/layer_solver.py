import sys
import numpy as np
import math, cmath

def to_rads(angle_in_degrees): 
    return angle_in_degrees*(math.pi/180.0)

def to_degrees(angle_in_rad):  
    return angle_in_rad* (180.0 / math.pi)

def snelly(angle_1, n_arrays, lambdas):
    '''Takes in arrays of index (assuming order from 0 up is left to right);
    computes angles (possibly complex) via Snells'''
    ang_array=np.empty( (len(n_arrays), len(lambdas)), dtype=complex )
    for i in range(len(lambdas)):
        for j in range(len(n_arrays)):
            if j==0:
                ang_array[j, i]=angle_1     #Light always enters at same angle, but will be dispered after entry
            else:
                n0=n_arrays[0, i]
                nj=n_arrays[j, i]
                theta=ang_array[0, i]
                sin_theta=cmath.sin(to_rads(theta) )     
                ang_array[j, i]=to_degrees( cmath.asin(  (n0/nj)  * sin_theta )    )  

    return ang_array

def fressy(ang_array, n_arrays, TM_or_TE, lambdas):
    '''Takes in array of N angles and computes N-1 fres reflection coefficients'''
    fressy=np.empty( ( (len(ang_array)-1), len(lambdas)), dtype=complex) 
    jmax=fressy.shape[0]
    TM_list=['tm', 'TM', 'Tm']
    TE_list=['te', 'TE', 'Te']
    Mixed=['mixed', 'Mixed',]
    valid_list=TM_list+TE_list+Mixed
    if TM_or_TE not in valid_list:
        print '\n Enter TE or TM'
        sys.exit()

    for i in range(len(lambdas)):
        for j in range(jmax):
            n1=n_arrays[j,i]
            n2=n_arrays[j+1, i]
            cang1=cmath.cos(to_rads(ang_array[j, i]))
            cang2=cmath.cos(to_rads(ang_array[j+1, i]))

            # P POLARIZED
            if TM_or_TE in TM_list:
                num=(n1*cang2) - (n2* cang1)
                den=(n1*cang2) + (n2* cang1)		

            # S POLIRZIED
            elif TM_or_TE in TE_list:
                num=(n1*cang1) - (n2*cang2)
                den=(n1*cang1) + (n2*cang2)

            # MIXED / UNPOLARIZED
            elif TM_or_TE in Mixed:
                num1=(n1*cang2) - (n2* cang1)
                num2=(n1*cang2) + (n2* cang1)
                den1=(n1*cang1) - (n2*cang2)
                den2=(n1*cang1) + (n2*cang2)
                num=.5*(num1 + num2)
                den=.5*(den1 + den2)

            fressy[j, i]=num/den
    return fressy

def boundary_crushin(angle_1, ds, n_arrays, TM_or_TE, lambdas):
    '''Determines to call 2 or 3-d boundary'''
    layers=len(ds)
    regions=int(n_arrays.shape[0])   #N regions, N-1 boundaries, N-2 layers
    bounds=regions-1
    if regions - layers != 2:
        print '\nShould always have N-2 layers to regions; you have', str(layers), 'layers and', str(regions), 'regions'
        sys.exit()

    #Why do I take conjugate!?
    for array in n_arrays:
        for i in range(len(lambdas)):
            ai=array[i].imag
            ar=array[i].real
            array[i]=complex(ar, -ai)

    angs = snelly(angle_1, n_arrays, lambdas)  #regions dimensional array
    
    # This computes reflectance (eq 7.4.3 sophoclese)
    # http://en.wikipedia.org/wiki/Fresnel_equations
    fres = fressy(angs, n_arrays, TM_or_TE, lambdas)    #regions-1 dimensional array

    R = np.empty( (len(lambdas)), dtype=complex)   #SHOULD BE REAL NO MATTER WHAT
    Rf = np.empty( (len(fres), len(lambdas)), dtype=complex)

    temp=[]               #Store list for reverse iteration
    for j in range(len(ds)):
        temp.append(j)

    for i in range(len(lambdas)):
        pmax=fres[len(ds), i]   #so len(ds) is actually 1 more than the arrays, as you expect for p
        jmax=len(ds)
        Rf[jmax, i]=pmax                 #RM+1 = pM+1
        for j in reversed(temp):
            Rc=Rf[j+1, i]
            p=fres[j,i]
            kvec=((2.0*math.pi/lambdas[i]) * n_arrays[j+1,i]) #WAVE VECTOR IN THE MEDIUM
            d=ds[j]
            X=(2.0 * kvec *  d * ( cmath.cos(to_rads(angs[j+1,i]) ) ))   #LAYER INDEX
            Z=cmath.exp(complex(0,-X)) #  ALSO WORKS!!!!
            num=(p + (Rc * Z))
            den=(1.0 + (p * Rc * Z) )
            Rf[j,i]=(num/den)             #RECURSIVE

#    return Rf[0,:]

    if layers==1:    #1 layer = 2 boundaries = 3 regions
        for i in range(len(lambdas)):		
            p1=fres[0, i]
            p2=fres[1, i]   #Layer index
            k=(2.0*math.pi/lambdas[i]) * n_arrays[1,i] #WAVE VECTOR IN THE MEDIUM			
            d=ds[0]                    #FIX
            X=2.0 * k *  d * ( cmath.cos(to_rads(angs[1,i]) ) )   #LAYER INDEX
            Z=cmath.exp(complex(0,-X)) #  ALSO WORKS!!!!
            num=(p1 + (p2*Z))
            den=(1.0 + (p1*p2*Z))
            R[i]=(num/den)      #Amplitude reflection coefficient, not intensity reflection coefficient	

    elif layers==2:
        for i in range(len(lambdas)):		
            p1=fres[0, i]
            p2=fres[1, i]   #Layer index
            p3=fres[2, i]
            k1=(2.0*math.pi/lambdas[i]) * n_arrays[1,i] #WAVE VECTOR IN THE MEDIUM 1	
            k2=(2.0*math.pi/lambdas[i]) * n_arrays[2,i] #WAVE VECTOR IN THE MEDIUM 2
            d1=ds[0]                    #FIX
            d2=ds[1]
            X1=2.0 * k1 *  d1 * ( cmath.cos(to_rads(angs[1,i]) ) )   #Region index  CHANGED
            X2=2.0 * k2 *  d2 * ( cmath.cos(to_rads(angs[2,i]) ) )   
            ca1=cmath.cos(X1)   #Unit is in rads, so don't need to convert it before taking angle
            sa1=cmath.sin(X1)
            ca2=cmath.cos(X2)
            sa2=cmath.sin(X2)
            Z1=complex(ca1, -sa1)   #exp(-ix) = cos(x) - i sin(x)
            Z2=complex(ca2, -sa2)
            num=(p1 + p2*Z1 + p1*p2*p3*Z2 + p3*Z1*Z2)
            den=(1.0 + p1*p2*Z1 + p2*p3*Z2 + p1*p3*Z1*Z2)
            R[i]=num/den

    return R