from cost import Cost_Enum
from scipy.optimize import minimize

from input_function import *
from noises import *
from filter import *
from plot_sig import *
from cost import *

noise_std_dev   = 0.1
alpha           = 0.4


sine    = Input_Function(Input_Enum.SINE, [1, 0.1, 0, 0])
polynom = Input_Function(Input_Enum.POLYNOM, [1,2,3,4]) #coeefs in descending order 2x^2+1 = [2,0,1]
exp     = Input_Function(Input_Enum.EXP, [1,2,0,0]) #coeefs [a,b,c,d]= a*e^(t/b+c)+d
white   = Noise(Noise_Enum.WHITE, noise_std_dev)
pt1     = Filter(Filter_Enum.PT1, 1e2)
wiener  = Filter(Filter_Enum.WIENER, noise_std_dev)
brown   = Filter(Filter_Enum.BROWN_HOLT, alpha)
kalman  = Filter(Filter_Enum.KALMAN, [0, 10])
plot    = Plot_Sig(Plot_Enum.MULTI, "Overview", [])
plot_sub= Plot_Sig(Plot_Enum.SUBPLOT, "Overview", [])
cost    = Cost(Cost_Enum.MSE)
plot_s  = Plot_Sig(Plot_Enum.SLIDER, "Detailed View with Slider",[])
savgol  = Filter(Filter_Enum.SAVGOL, parameters=None)

time, true_sine, true_sine_dot = sine.get_fun()
norm_freq = time[:round(len(time)/2)] / (time[-1] - time[0])
y = white.apply_noise(true_sine)

def filter_cost(para_in, t, y, true_y, filter, cost):
        y_hat_pt1 = filter.filter_fun(t, y, para = para_in)
        return cost.cost(y_hat_pt1, true_y)


def kalman_filter_cost(para_in, t, y, para_filt, true_y, filter, cost):
        y_hat_kalman = filter.filter_fun(t, y, para = para_filt)[0]
        return cost.cost(y_hat_kalman, true_y)

f_min = minimize(filter_cost,0.1,args=(time, y, true_sine, pt1,cost))
print("Minimal solution found. f_min = ")
print(f_min.x)
y_hat_pt1 = pt1.filter_fun(time, y, para = f_min.x)
print(cost.cost(y, true_sine))
print(cost.cost(y_hat_pt1, true_sine))
plot.plot_sig(time, [true_sine, y, y_hat_pt1],["Roh","Rausch", "Filter"])

# differentiate noisy signal
diff_finite = fwd_diff(time, y)
# PT1-smoothing
f_min = minimize(filter_cost,0.1,args=(time, y, true_sine, pt1,cost))
y_hat_pt1 = pt1.filter_fun(time, y, para = f_min.x)
y_hat_dot_pt1 = fwd_diff(time, y_hat_pt1)
f_min = minimize(filter_cost,0.1,args=(time, y_hat_dot_pt1, true_sine_dot, pt1,cost))
y_hat_dot_pt1 = pt1.filter_fun(time, y_hat_dot_pt1, para = f_min.x)


# Wiener-smoothing
# Frage: wie noise std_dev am besten schaetzen, wenn unbekannt?
y_hat_wiener = wiener.filter_fun(time, y, noise_std_dev)
tf_wiener = y_hat_wiener[1]
y_hat_wiener = y_hat_wiener[0]
y_hat_dot_wiener = fwd_diff(time, y_hat_wiener)


# Kalman-smoothing
y_kalman_true = -10*(time-0.5)**2 + 2.5
y_dot_kalman_true = -20*(time-0.5)
y_kalman = white.apply_noise(y_kalman_true)
kalman_process_noise = minimize(kalman_filter_cost, 3e6, args=(time, y_kalman, [np.array([0, 11]).reshape(2, 1), noise_std_dev, 3e6], y_kalman_true, kalman, cost))
kalman_process_noise = kalman_process_noise.x
y_hat_kalman = kalman.filter_fun(time, y_kalman, para=[np.array([0, 11]).reshape(2, 1), noise_std_dev, kalman_process_noise])
y_hat_dot_kalman = y_hat_kalman[1]
tf_kalman = y_hat_kalman[2]
y_hat_kalman = y_hat_kalman[0]

# Brown Holt
alpha_min = minimize(filter_cost,alpha,args=(time, y, true_sine, brown ,cost))
y_hat_brown = brown.filter_fun(time, y, para = alpha_min.x)
y_hat_dot_brown = fwd_diff(time, y_hat_brown)

print(f"Mean Squared Error of Differentials: \n \
        Forward Difference: {cost.cost(diff_finite, true_sine_dot)} \n \
        PT1: {cost.cost(y_hat_dot_pt1, true_sine_dot)} \n \
        Wiener: {cost.cost(y_hat_dot_wiener, true_sine_dot)} \n \
        Kalman: {cost.cost(y_hat_dot_kalman, y_dot_kalman_true)} \n \
        Brown-Holt: {cost.cost(y_hat_dot_brown, true_sine_dot)} \n" )

# plot results
plot.plot_sig(time, [true_sine_dot, y_hat_dot_wiener], ["true diff sine", "diff Wiener"])
plot.plot_sig(norm_freq, [tf_wiener, tf_kalman], ["Wiener TF", "Kalman TF"], time_domain=False)
plot.plot_sig(time, [diff_finite, y_hat_dot_wiener], ["diff unsmoothed", "diff Wiener"])
plot.plot_sig(time, [true_sine, y, y_hat_wiener], ["true sine", "noisy sine", "Wiener smoothed"])
plot.plot_sig(time, [y_kalman, y_hat_kalman, y_hat_dot_kalman], ["y", "Kalman", "dot Kalman"])
plt.show()


'''
#test of slider 
savgol_filter_para=[5,3]
y_hat_savgol=savgol.filter_fun(time,y,para=savgol_filter_para)
plot_s.plot_slider(time,[y, y_hat_savgol],['noisy sine','savgol smoothed'],savgol_filter_para,savgol)
plot_s.plot_slider(time,[y,y_hat_brown],['noisy sine','brown holt smoothed'],alpha_min.x,brown)
plot_s.plot_slider(time,[y,y_hat_pt1],['noisy sine','pt1 smoothed'],f_min.x,pt1)
#test of polynom and exp input
#time_p, true_pol, true_pol_dot = polynom.get_fun()
#plot.plot_sig(time_p, [true_pol, true_pol_dot], ["polynom", "diff polynom"])
#time_exp, true_exp, true_exp_dot = exp.get_fun()
#plot.plot_sig(time_exp, [true_exp, true_exp_dot], ["exponential", "diff exponential"])
plt.show()
'''