import json
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import numpy as np
import scipy

path = "//172.16.12.127/Pub/!diamagnetic_data/"

shotn = 45589
Tplato_S = 0.16
Tplato_E = 0.26
with open('%sjson/%i.json' %(path, shotn), 'r') as file:
    diaData = json.load(file)

print(diaData['data'].keys())

P_smooth = savgol_filter(diaData['data']['psiRes'], window_length=51, polyorder=2)

plt.figure()
plt.plot(diaData['time'], diaData['data']['psiRes'], '.')
plt.plot(diaData['time'], P_smooth)

dP_dt = np.gradient(P_smooth, diaData['time'])
boundares = []
previous = 0
for i in range(3, len(dP_dt) - 1):
    # print(abs(dP_dt[i+1] - dP_dt[i]))
    if abs(dP_dt[i + 1] - dP_dt[i - 3]) > abs(dP_dt[i]*0.3):
        if abs(i - previous) > 40:
            boundares.append(i)
            previous = i
for i, t in enumerate(diaData['time'][:-1]):
    #print(t, Tplato_S, diaData['time'][i + 1])
    if t < Tplato_S < diaData['time'][i + 1]:
        #print('yessss')
        #print(i - boundares[0])
        if abs(i - boundares[0]) > 50:
            boundares.insert(0, i)
            break

for i, t in enumerate(diaData['time'][:-1]):
    if t < Tplato_E < diaData['time'][i + 1]:
        if abs(boundares[-1] - (i + 1)) > 50:
            boundares.append(i + 1)
            break
print(boundares)
dP_dt_smooth = savgol_filter(dP_dt, window_length=61, polyorder=2)
ddP_dt = np.gradient(dP_dt_smooth, diaData['time'])
ddP_dt_smooth = savgol_filter(ddP_dt, window_length=61, polyorder=2)


for i in boundares:
    plt.axvline(diaData['time'][i])



for i, ind in enumerate(boundares[:-1]):
    if diaData['time'][ind] >= Tplato_S - 0.005 and diaData['time'][boundares[i+1]] <= Tplato_E + 0.005:
        coef, cov = np.polyfit(diaData['time'][ind:boundares[i+1]], diaData['data']['psiRes'][ind:boundares[i+1]], 1, cov=True)
        Ures, b = coef[0], coef[1]
        errs = np.sqrt(np.diag(cov))
        dUres = errs[0]
        plt.plot(diaData['time'][ind:boundares[i+1]], [i * Ures + b for i in diaData['time'][ind:boundares[i+1]]], color='g')
        Ip = sum(diaData['data']['Ipl'][ind:boundares[i+1]]) / len(diaData['data']['Ipl'][ind:boundares[i+1]])
        dIp = (sum([(diaData['data']['Ipl'][i] - Ip)**2]) / (len(diaData['data']['Ipl'][ind:boundares[i+1]])-1))**0.5
        Poh = Ures*Ip*1e-6
        dPoh = Poh * ((dUres/Ures)**2 + (dIp/Ip)**2)**0.5
        print('t1=%.3f, t2=%.3f, Ures=%.3f+-%.3f V, Ip=%.2f A, Poh=%.4f+-%.4f MW' %(diaData['time'][ind], diaData['time'][boundares[i+1]], Ures, dUres, Ip, Poh, dPoh))



plt.figure()



plt.plot(diaData['time'], dP_dt)


plt.plot(diaData['time'], dP_dt_smooth, color='r')
for i in boundares:
    plt.axvline(diaData['time'][i])


plt.figure()
plt.plot(diaData['time'], ddP_dt)

plt.plot(diaData['time'], ddP_dt_smooth, color='r')



plt.show()