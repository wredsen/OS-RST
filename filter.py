#from curses import window
import numpy as np
from numpy.core.numeric import isscalar
from scipy import signal
from scipy.signal import lfilter, cont2discrete, butter
from scipy.linalg import toeplitz
from enum import Enum

class Filter_Enum(Enum):
    PT1             = 'PT1-Filter'
    SAVGOL          = 'Savitzky Golay Filter'
    WIENER          = 'Wiener Filter'
    DIFF_QUOTIENT   = 'Gleitender Differenzenquotient'
    BROWN_HOLT      ='Lineare Exponentielle Glättung'
    BUTTERWORTH     ='Butterworth Filter'
    CHEBYCHEV       ='Chebychev filter'
    ROB_EX_DIFF     ='Robust Exact Differentiator'
    KALMAN          ='Kalman'


class Filter:
    type                = Filter_Enum.SAVGOL

    def __init__(self,type,parameters):
        self.type               = type
        self.parameters         = parameters

    def filter_fun(self,t,y,para=None):
        para = self.parameters if para is None else para
        match self.type:
            case Filter_Enum.PT1:
                return self.__filter_fun_pt1(t,y,para)
            case Filter_Enum.SAVGOL:
                return self.__filter_fun_savgol(t,y,para)
            case Filter_Enum.WIENER:
                return self.__filter_fun_wiener(t,y,para)
            case Filter_Enum.DIFF_QUOTIENT:
                return self.__filter_fun_diff(t,y,para)
            case Filter_Enum.BROWN_HOLT:
                return self.__filter_fun_brownholt(t,y,para)
            case Filter_Enum.BUTTERWORTH:
                return self.__filter_fun_butterworth(t,y,para)
            case Filter_Enum.CHEBYCHEV:
                return self.__filter_fun_chebychev(t,y,para)
            case Filter_Enum.ROB_EX_DIFF:
                return self.__filter_fun_robexdiff(t,y,para)
            case Filter_Enum.KALMAN:
                return self.__filter_fun_kalman(t,y,para)
                
    def filter_diff(self,t,y,para=None):
        para = self.parameters if para is None else para
        match self.type:
            case Filter_Enum.PT1:
                return self.__filter_diff_pt1(t,y,para)
            case Filter_Enum.SAVGOL:
                return self.__filter_diff_savgol(t,y,para)
            case Filter_Enum.WIENER:
                return self.__filter_diff_wiener(t,y,para)
            case Filter_Enum.DIFF_QUOTIENT:
                return self.__filter_diff_diff(t,y,para)
            case Filter_Enum.BROWN_HOLT:
                return self.__filter_diff_brownholt(t,y,para)
            case Filter_Enum.BUTTERWORTH:
                return self.__filter_diff_butterworth(t,y,para)
            case Filter_Enum.CHEBYCHEV:
                return self.__filter_diff_chebychev(t,y,para)
            case Filter_Enum.ROB_EX_DIFF:
                return self.__filter_diff_robexdiff(t,y,para)
            case Filter_Enum.KALMAN:
                return self.__filter_diff_kalman(t,y,para)

####################################################################
####################### Filter Functions ###########################
####################################################################


    def __filter_fun_pt1(self,t,y,para):
        para = para if isscalar(para) else para[0] # Aus Gründen(TM) wandelt scp.minimize Skalare Werte in Vektoren mit Länge 1 um.
        # Parameter: Cutoff frequency
        T_sample = (t[-1] - t[0]) / (len(t) - 1)
        num_coeff = [T_sample * para]            
        den_coeff = [1, T_sample * para - 1]
        return lfilter(num_coeff, den_coeff, y)

    def __filter_fun_savgol(self,t,y,para): #kausaler savgol filter. point of evluation is end of window_length para=[m,polorder,diff=number]
        ###################################################
        #Compute H Matrix: Only Polyorder and window needed
        m=para[0]
        polyorder=int(para[1])
        if len(para)<3:
            diff=0
        else:
            diff=int(para[2])
        window_length=int(2*m+1)
        if polyorder >= window_length:
            raise ValueError("polyorder must be less than window_length.")
        x_vector = np.arange(-m, window_length-m) #for a=H*x
        order = np.arange(polyorder + 1).reshape(-1, 1)
        A_t = x_vector ** order #for H=(A_trans*A)^-1*A_trans    
        A=np.transpose(A_t)
        B=A_t.dot(A)
        B_inv=np.linalg.inv(B)
        H=B_inv.dot(A_t)
        ###################################################
        #Filter
        y_uneven=[]
        for i in range(0,len(y)-window_length+1):
            y_signal=np.transpose([y[0+i:window_length+i]])
            f=[]
            if diff>0:
                for i in range(0,diff):
                    f.append(0)
            for l in range(diff,polyorder+1):
                f.append((l**diff)*y[window_length+i-1]**(l-diff))
            
            f=np.asarray(f) 
            y_zwischen=f.dot(H.dot(y_signal))
            y_uneven.append(y_zwischen[0])
        if len(t)>len(y_uneven):    
            filler= np.full([1,len(t)-len(y_uneven) ], None)
        y_hat=np.concatenate((filler,y_uneven), axis=None)
        ###################################################
        return y_hat
        

    def __filter_fun_wiener(self,t,y,para):
 
        # Parameter: Noise standard Deviation
        noise_stdev = para[0]
        m = para[1]
        sigma = noise_stdev
        N = m//2  # (half) window length
        
        # unbiased crosscorrelation function
        def xcorr(x, y, M):
            """
            evaluate the cross-correlation of vectors x and y with lags -M+1 to M-1
            :param x:
            :param y:
            :param M: lags to calculate
            :return: rxy: the cross-correlation
            """
            N = len(x)
            rxy = np.zeros(2*M-1)
            for k in range(0, M):
                rxy[M-k-1] = 1/(N-k)*np.inner(x[k:], y[0:N-k])
            for k in range(1, M):
                rxy[M+k-1] = 1/(N-k)*np.inner(x[0:N-k], y[k:])
            return rxy    

        
        y_corr_part = xcorr(y, y, m)[N:3*N-1]  # symmetric part of correlation
        R_part = toeplitz(xcorr(y, y, m)[2*N-1:-1] )
        
        noise_corr_part = -np.ones((2*N-1,)) * 0
        noise_corr_part[N-1] = sigma**2

        h_opt_noncausal = np.matmul(np.linalg.inv(R_part), y_corr_part - noise_corr_part)

        # Apply filter time domain wiener filter
        # with boundary effects:
        s_hat_noncausal_long = np.convolve(y, h_opt_noncausal, mode='full')
        s_hat_noncausal = s_hat_noncausal_long[N-1:-N+1]

        # mitigate boundary effects by padding of initial and last value:
        y_start_pad = y[0]*np.ones(N)
        y_end_pad = y[-1]*np.ones(N)
        s_hat_noncausal_long = np.convolve(np.append(y_start_pad, np.append(y, y_end_pad)), h_opt_noncausal, mode='full')
        s_hat_noncausal = s_hat_noncausal_long[2*N-1:-2*N+1]

        H_opt_noncausal=np.ones(len(s_hat_noncausal))

        return [s_hat_noncausal]


    def __filter_fun_kalman(self,t,y,para):
        # Parameter: x_0 estimation, stdev of output noise, stdev of process noise
        T_sample = (t[-1] - t[0]) / (len(t) - 1)

        # initialization
        filter_order = para[0]
        x_est = para[1]
        output_n_stdev = para[2]
        process_n_stdev = para[3]

        A = np.zeros((filter_order, filter_order))
        for i in range(0, filter_order-1):
            A[i, i+1] = 1
        B = np.zeros((filter_order, 1))
        B[-1] = 1
        C = np.zeros((1, filter_order))
        C[0, 0] = 1
        D = np.array([[0]])

        disc_sys = cont2discrete((A,B,C,D), T_sample)
        F = disc_sys[0]
        B = disc_sys[1]
        H = disc_sys[2]
        Q = B * B.transpose() * process_n_stdev**2
        R = np.array([output_n_stdev**2]).reshape(1, 1)
        P = 1e-3*np.eye(filter_order)

        x_1_list = x_est[0]
        x_2_list = x_est[1]
        k = 1
        while k < len(y):
            x_est_prior = F@x_est
            P_prior = H@P@H.transpose() + Q
            K = P_prior@H.transpose() @ np.linalg.inv(H@P_prior@H.transpose() + R)
            x_est = x_est_prior + K@(y[k] - H@x_est_prior)
            P = (np.eye(len(B)) - K@H)@P_prior
            x_1_list = np.append(x_1_list, x_est[0])
            x_2_list = np.append(x_2_list, x_est[1])
            k = k + 1

        return [x_1_list, x_2_list]
        

    def __filter_fun_diff(self,t,y,para): #kausal definition para=[h], backwards differentiation
        y_uneven=[]
        h=para[0]
        for i in range(h,len(y)):
            y_zwischen=(y[i]-y[i-h])/h
            y_uneven.append(y_zwischen)

        if len(t)>len(y_uneven):    
                filler= np.full([1,len(t)-len(y_uneven) ], None)
        y_hat=np.concatenate((filler,y_uneven), axis=None)
        return y_hat

    def __filter_fun_brownholt(self,t,y,para):
        # Parameter: Alpha, Order, Beta, Startwert
        alpha = para[0]
        order = para[1]
        x_hat = np.zeros(len(y))
        x_hat[0] = para[3] if len(para)==4 else 0 # Startwert für y_hat
        for j in range(order):
            for i in range(1,len(y)):
                x_hat[i] = alpha*y[i] + (1-alpha)*x_hat[i-1]
            y = x_hat
        return x_hat
    def __filter_fun_butterworth(self,t,y,para):
        # Parameter: Filterordnung , Normalisierte Grenzfrequenz
        order = para[0]
        freq = para[1]

        sos = butter(order, freq,output='sos')
        y_hat = signal.sosfilt(sos,y)
        return y_hat

    def __filter_fun_chebychev(self,t,y,para):
        return y
    def __filter_fun_robexdiff(self,t,y,para):
        return y
    

####################################################################
####################### Diff Functions #############################
####################################################################

    def __filter_diff_pt1(self,t,y,para):
        para = para if isscalar(para) else para[0] # Aus Gründen(TM) wandelt scp.minimize Skalare Werte in Vektoren mit Länge 1 um.
            # Parameter: Cutoff frequency
        T_sample = (t[-1] - t[0]) / (len(t) - 1)
        num_coeff = [T_sample * para]
        den_coeff = [1, T_sample * para - 1]
        return lfilter(num_coeff, den_coeff, y)

    def __filter_diff_savgol(self,t,y,para):
        return y
    
    def __filter_diff_wiener(self,t,y,para):
        # Parameter: Noise standard Deviation
        noise_stdev = para[0]
        m = para[1]
        sigma = noise_stdev
        n = len(y)
        N = m//2  # (half) window length
        
        # unbiased crosscorrelation function
        def xcorr(x, y, M):
            """
            evaluate the cross-correlation of vectors x and y with lags -M+1 to M-1
            :param x:
            :param y:
            :param M: lags to calculate
            :return: rxy: the cross-correlation
            """
            N = len(x)
            rxy = np.zeros(2*M-1)
            for k in range(0, M):
                rxy[M-k-1] = 1/(N-k)*np.inner(x[k:], y[0:N-k])
            for k in range(1, M):
                rxy[M+k-1] = 1/(N-k)*np.inner(x[0:N-k], y[k:])
            return rxy    

        
        y_corr_part = xcorr(y, y, m)[N:3*N-1]  # symmetric part of correlation
        R_part = toeplitz(xcorr(y, y, m)[2*N-1:-1] )
        
        noise_corr_part = -np.ones((2*N-1,)) * 0
        noise_corr_part[N-1] = sigma**2

        h_opt_noncausal = np.matmul(np.linalg.inv(R_part), y_corr_part - noise_corr_part)

        # Apply filter time domain wiener filter
        # with boundary effects:
        s_hat_noncausal_long = np.convolve(y, h_opt_noncausal, mode='full')
        s_hat_noncausal = s_hat_noncausal_long[N-1:-N+1]

        # mitigate boundary effects by padding of initial and last value:
        y_start_pad = y[0]*np.ones(N)
        y_end_pad = y[-1]*np.ones(N)
        s_hat_noncausal_long = np.convolve(np.append(y_start_pad, np.append(y, y_end_pad)), h_opt_noncausal, mode='full')
        s_hat_noncausal = s_hat_noncausal_long[2*N-1:-2*N+1]

        H_opt_noncausal=np.ones(len(s_hat_noncausal))
        y_diff = np.diff(s_hat_noncausal, append = 0)/(t[1]-t[0])

        return [y_diff]

    def __filter_diff_kalman(self,t,y,para):
        return y

    def __filter_diff_diff(self,t,y,para):
        return y
    def __filter_diff_brownholt(self,t,y,para):
        # Parameter: Alpha, Order
        alpha   = para[0]
        order   = para[1]
        beta    = para[2]
        a = np.zeros(len(y))
        a[0] = y[0]
        b = np.zeros(len(y))
        b[0] = para[3]*t[1] if len(para)==4 else 0 # Startwert für a
        
        for j in range(order):
            for i in range(1,len(y)):
                a[i] = alpha*y[i] + (1-alpha)*(a[i-1] + b[i-1])
                b[i] = (beta*(a[i]-a[i-1]) + (1-beta)*b[i-1])
            y = a
        return [x / t[1] for x in b] #Divide by stepsize


    def __filter_diff_butterworth(self,t,y,para):
        # Parameter: Filterordnung , Normalisierte Grenzfrequenz
        order = para[0]
        freq = para[1]

        if (True):
        
            sos = butter(order, freq, output='sos')
            derivative = signal.zpk2sos([1],[-1],1/t[1])  # Second order section derivative | s= (z-1)/(z+1)
            sos= np.append(sos,derivative,axis=0)
            # zi = signal.sosfilt_zi(sos)                 # Initial conditions
            # zi = np.multiply(zi,2)
            #y_dot_hat, z_f = signal.sosfilt(sos,y, zi=zi)
            y_dot_hat = signal.sosfilt(sos,y)
            return y_dot_hat # np.diff(y_dot_hat, append = 0)/t[1]
        
        else:
            sos = butter(order, freq, output='sos')            
            y_hat = signal.sosfilt(sos,y)
            #y_dot_hat = np.diff(y_hat, prepend=y_hat[0])
            #y_dot_hat = np.multiply(y_dot_hat,1/t[1])
            return np.diff(y_hat, append = 0)/t[1]
                


    def __filter_diff_chebychev(self,t,y,para):
        return y
    def __filter_diff_robexdiff(self,t,y,para):
        return y

####################################################################
########################## Old Stuff ###############################
####################################################################

# numerical differentiation
def fwd_diff(tt, signal):
    diff = np.zeros(len(tt))
    for i in range(0, len(tt)-1):
        diff[i] = (signal[i+1] - signal[i]) / (tt[1] - tt[0])
    return diff