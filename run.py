import dia_sig
import matplotlib.pyplot as plt

shotn = 44330
rec = 44235

time_start = 0.190#s
time_end = 0.191 #s
time_step = 10 #ms

checked_fig, ch_ax = plt.subplots(1,2, sharex=True, figsize=(14,2))
data = dia_sig.dia_data(shotn, rec, ch_ax, pf2=True)

plt.show()

with open('c:/work/equilibrium/dia_data/my/%s.txt' %shotn, 'w') as file:
    file.write('time,')
    file.write('psidia,')
    file.write('Ip,')
    file.write('Bt,')
    file.write('Rav,')
    file.write('pf2Up,')
    file.write('betadia')
    file.write('\n')
    count = 0
    for i, t in enumerate(data['data']['time']):
        if time_end >= t >= time_start:
            if (t - time_start) >= count * time_step/1000:
                file.write('%4.1f,' % (t*1000))
                file.write('%5.4f,' % data['data']['data']['dia_sig'][i])
                file.write('%5.4f,' % (data['data']['data']['Ipl'][i]/1e6))
                file.write('%5.4f,' % data['data']['data']['Bt'][i])
                file.write('%5.4f,' % data['data']['data']['Rav'][i])
                file.write('%5.4f,' % data['data']['data']['pf2_up'][i])
                file.write('%5.4f' % data['data']['data']['beta_dia'][i])
                file.write('\n')
                count+=1
