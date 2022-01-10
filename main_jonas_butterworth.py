from re import S
from matplotlib.pyplot import show
from matplotlib import ticker, cm
from scipy.optimize import minimize
from scipy.fft import fft, ifft, fftfreq
from scipy import signal
from numpy import ma

from input_function import *
from noises import *
from filter import *
from plot_sig import *
from cost import *


noise_std_dev   = 0.1
freq            = 10 / (1000 / 2) # Normalisierte Grenzfrequenz mit w = fc / (fs / 2)

bounds          = ((0.0001, 0.9999),) # Komische Tupeldarstellung damit Minimize Glücklich ist.

# 1. Filtereigenschaften auf Sinus
for order in range(1,5):
        sine    = Input_Function(Input_Enum.SINE, [1, 0.4, 0, 0])

        butter   = Filter(Filter_Enum.BUTTERWORTH, [order,freq])
        
        white   = Noise(Noise_Enum.WHITE, noise_std_dev)
        brown   = Noise(Noise_Enum.BROWN, noise_std_dev)
        quant   = Noise(Noise_Enum.QUANT, noise_std_dev)

        cost    = Cost(Cost_Enum.MSE)

        plot  = Plot_Sig(Plot_Enum.FILTER1, "Filterung",[])

        def filter_cost(para_in, t, y, x, filter, cost):
                y_hat = filter.filter_fun(t, y, para = [filter.parameters[0], para_in])
                return cost.cost(y_hat, x)
        def filter_cost_diff(para_in, t, y, x_dot, filter, cost):
                y_hat_dot = filter.filter_diff(t, y, para = [filter.parameters[0], para_in])
                return cost.cost(y_hat_dot, x_dot)

        t, x, x_dot = sine.get_fun()
        y_white = white.apply_noise(x)
        y_brown = brown.apply_noise(x)
        y_quant = quant.apply_noise(x)

        freq_min_white = minimize(filter_cost,freq,args=(t, y_white, x, butter ,cost), bounds= bounds)
        x_hat_min_white = butter.filter_fun(t,y_white,para = [butter.parameters[0],freq_min_white.x])
        cost_white = cost.cost(x_hat_min_white,x)
        standard_cost_white = cost.cost(y_white,x)

        freq_min_brown = minimize(filter_cost,freq,args=(t, y_brown, x, butter ,cost), bounds= bounds)
        x_hat_min_brown = butter.filter_fun(t,y_brown,para = [butter.parameters[0],freq_min_brown.x])
        cost_brown = cost.cost(x_hat_min_brown,x)
        standard_cost_brown = cost.cost(y_brown,x)

        freq_min_quant = minimize(filter_cost,freq,args=(t, y_quant, x, butter ,cost), bounds= bounds)
        x_hat_min_quant = butter.filter_fun(t,y_quant,para = [butter.parameters[0],freq_min_quant.x])
        cost_quant = cost.cost(x_hat_min_quant,x)
        standard_cost_quant = cost.cost(y_quant,x)

        box_label_white = '\n'.join((
                r'White Noise',
                r'$\sigma_{Noise}=%.2f$' % (noise_std_dev, ),
                r'$f=%.2f$' % (freq_min_white.x, ),
                r'$MSE_{Noise}=%.5f$' % (standard_cost_white, ),
                r'$MSE_{Filter}=%.5f$' % (cost_white, ),
                r'$r_{MSE}=%.2f$ %%' % (100*cost_white/standard_cost_white, )))

        box_label_brown = '\n'.join((
                r'Brown Noise',
                r'$\sigma_{Noise}=%.2f$' % (noise_std_dev, ),
                r'$f=%.2f$' % (freq_min_brown.x, ),
                r'$MSE_{Noise}=%.5f$' % (standard_cost_brown, ),
                r'$MSE_{Filter}=%.5f$' % (cost_brown, ),
                r'$r_{MSE}=%.2f$ %%' % (100*cost_brown/standard_cost_brown, )))

        box_label_quant = '\n'.join((
                r'Quantisation Noise',
                r'$stepsize=%.2f$' % (noise_std_dev, ),
                r'$f=%.2f$' % (freq_min_quant.x, ),
                r'$MSE_{Noise}=%.5f$' % (standard_cost_quant, ),
                r'$MSE_{Filter}=%.5f$' % (cost_quant, ),
                r'$r_{MSE}=%.2f$ %%' % (100*cost_quant/standard_cost_quant, )))

        plot.plot_sig(t,[x,y_white,y_brown,y_quant,x_hat_min_white,x_hat_min_brown,x_hat_min_quant],['Input Signal',
        'Signal with White Noise',
        'Signal with Brown Noise',
        'Signal with Quantisation Noise',
        'Butterworth Filter order: '+ str(order) +' (White Noise)',
        'Butterworth Filter order: '+ str(order) +' (Brown Noise)',
        'Butterworth Filter order: '+ str(order) +' (Quantisation)',
        box_label_white,box_label_brown,box_label_quant],True)
plt.show()