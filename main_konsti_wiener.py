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

step_size       = 1e-3

noise_std_dev   = 0.1

bounds_fun          = ((0.0001, 0.9999),)
bounds_diff          = ((0.0001, 0.9999),(0.0001, 0.9999),)

# 1. Filtereigenschaften auf Sinus / Polynom

sine    = Input_Function(Input_Enum.SINE, [1, 0.5, 0, 0], sampling_period = step_size)
polynome = Input_Function(Input_Enum.POLYNOM, [100,-150,50,0]) #coefs in descending order 2x^2+1 = [2,0,1]
input_func = sine

wiener   = Filter(Filter_Enum.WIENER, noise_std_dev)

white   = Noise(Noise_Enum.WHITE, noise_std_dev)
brown   = Noise(Noise_Enum.BROWN, noise_std_dev)
quant   = Noise(Noise_Enum.QUANT, noise_std_dev)

cost    = Cost(Cost_Enum.MSE)

plot1  = Plot_Sig(Plot_Enum.FILTER1, "Filterung",[])

t, x, x_dot = input_func.get_fun()
y_white = white.apply_noise(x)
y_brown = brown.apply_noise(x)
y_quant = quant.apply_noise(x)

x_hat_min_white = wiener.filter_fun(t,y_white,noise_std_dev)[0]
cost_white = cost.cost(x_hat_min_white,x)
standard_cost_white = cost.cost(y_white,x)

x_hat_min_brown = wiener.filter_fun(t,y_brown,noise_std_dev)[0]
cost_brown = cost.cost(x_hat_min_brown,x)
standard_cost_brown = cost.cost(y_brown,x)

x_hat_min_quant = wiener.filter_fun(t,y_quant,noise_std_dev)[0]
cost_quant = cost.cost(x_hat_min_quant,x)
standard_cost_quant = cost.cost(y_quant,x)

box_label_white = '\n'.join((
        r'White Noise',
        r'$\sigma_{Noise}=%.2f$' % (noise_std_dev, ),
        r'$MSE_{Noise}=%.5f$' % (standard_cost_white, ),
        r'$MSE_{Filter}=%.5f$' % (cost_white, ),
        r'$r_{MSE}=%.2f$ %%' % (100*cost_white/standard_cost_white, )))

box_label_brown = '\n'.join((
        r'Brown Noise',
        r'$\sigma_{Noise}=%.2f$' % (noise_std_dev, ),
        r'$MSE_{Noise}=%.5f$' % (standard_cost_brown, ),
        r'$MSE_{Filter}=%.5f$' % (cost_brown, ),
        r'$r_{MSE}=%.2f$ %%' % (100*cost_brown/standard_cost_brown, )))

box_label_quant = '\n'.join((
        r'Quantisation Noise',
        r'$stepsize=%.2f$' % (noise_std_dev, ),
        r'$MSE_{Noise}=%.5f$' % (standard_cost_quant, ),
        r'$MSE_{Filter}=%.5f$' % (cost_quant, ),
        r'$r_{MSE}=%.2f$ %%' % (100*cost_quant/standard_cost_quant, )))

plot1.plot_sig(t,[x,y_white,y_brown,y_quant,x_hat_min_white,x_hat_min_brown,x_hat_min_quant],['Input Signal',
'Signal with White Noise',
'Signal with Brown Noise',
'Signal with Quantisation Noise',
'Wiener Smoothing (White Noise)',
'Wiener Smoothing (Brown Noise)',
'Wiener Smoothing (Quantisation)',
box_label_white,box_label_brown,box_label_quant],True)

# 2. Ableitungseigenschaften auf Sinus / Polynom

y_white_dot = np.diff(y_white, append = 0)/step_size
y_brown_dot = np.diff(y_brown, append = 0)/step_size
y_quant_dot = np.diff(y_quant, append = 0)/step_size

plot2  = Plot_Sig(Plot_Enum.FILTER2, "Filterung",[])

x_hat_dot_white = np.diff(x_hat_min_white, append = 0)/step_size
cost_white = cost.cost(x_hat_dot_white,x_dot)
standard_cost_white = cost.cost(y_white_dot,x_dot)

x_hat_dot_brown = np.diff(x_hat_min_brown, append = 0)/step_size
cost_brown = cost.cost(x_hat_dot_brown,x_dot)
standard_cost_brown = cost.cost(y_brown_dot,x_dot)

x_hat_dot_quant = np.diff(x_hat_min_quant, append = 0)/step_size
cost_quant = cost.cost(x_hat_dot_quant,x_dot)
standard_cost_quant = cost.cost(y_quant_dot,x_dot)

box_label_white = '\n'.join((
        r'White Noise',
        r'$\sigma_{Noise}=%.2f$' % (noise_std_dev, ),
        r'$MSE_{Noise}=%.2f$' % (standard_cost_white, ),
        r'$MSE_{Filter}=%.2f$' % (cost_white, ),
        r'$r_{MSE}=%.2f$ %%' % (100*cost_white/standard_cost_white, )))

box_label_brown = '\n'.join((
        r'Brown Noise',
        r'$\sigma_{Noise}=%.2f$' % (noise_std_dev, ),
        r'$MSE_{Noise}=%.2f$' % (standard_cost_brown, ),
        r'$MSE_{Filter}=%.2f$' % (cost_brown, ),
        r'$r_{MSE}=%.2f$ %%' % (100*cost_brown/standard_cost_brown, )))

box_label_quant = '\n'.join((
        r'Quantisation Noise',
        r'$stepsize=%.2f$' % (noise_std_dev, ),
        r'$MSE_{Noise}=%.2f$' % (standard_cost_quant, ),
        r'$MSE_{Filter}=%.2f$' % (cost_quant, ),
        r'$r_{MSE}=%.2f$ %%' % (100*cost_quant/standard_cost_quant, )))

plot2.plot_sig(t,[x_dot,y_white_dot,y_brown_dot,y_quant_dot,x_hat_dot_white,x_hat_dot_brown,x_hat_dot_quant],['Input Signal',
'Diff of signal with White Noise',
'Diff of signal with Brown Noise',
'Diff of signal with Quantisation Noise',
'Wiener Smoothing and Differentation',
'Wiener Smoothing and Differentation',
'Wiener Smoothing and Differentation',
box_label_white,box_label_brown,box_label_quant],True)

plt.show()