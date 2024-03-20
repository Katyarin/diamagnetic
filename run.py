import dia_sig
import matplotlib.pyplot as plt

shotn = 43922
rec = 43941

time_start = 0.1703 #s
time_end = 0.1885 #s
time_step = 3.03 #ms

checked_fig, ch_ax = plt.subplots(1,2, sharex=True, figsize=(14,2))
data = dia_sig.dia_data(shotn, rec, ch_ax)

plt.show()

with open('c:/work/equilibrium/dia_data/my/%s.txt' %shotn, 'w') as file:
    file.write('time,')
    file.write('psidia,')
    file.write('Ip,')
    file.write('Bt,')
    file.write('Rav,')
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
                file.write('%5.4f' % data['data']['data']['beta_dia'][i])
                file.write('\n')
                count+=1
