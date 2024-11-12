import json
import dia_sig
import matplotlib.pyplot as plt
import time

shotn_need = 44015

indexPath = 'Z:/!!!TS_RESULTS/shots/'

with open('%sindex.json' %indexPath, 'r') as indFile:
    index = json.load(indFile)

'''shotn = 40668
print(index[str(shotn)]['err'])
#print(index[str(shotn)]['Bt'])'''

checked_fig, ch_ax = plt.subplots(1, 2, sharex=True, figsize=(14, 2))
print(max([int(i) for i in list(index.keys())]))
for delta in range(2, 500):
    if delta%2:
        shotn = shotn_need + delta//2
    else:
        shotn = shotn_need - delta//2

    if 'err' in list(index[str(shotn)].keys()):
        print(shotn, index[str(shotn)]['err'])
        if 'has suspicious file size' in index[str(shotn)]['err']:
            continue
        #time.sleep(1)

        data = dia_sig.dia_data(shotn_need, shotn, ch_ax, pf2=False)
        if data['error']:
            print(data['error'])
            for i in range(2):
                ch_ax[i].clear()
            continue
        #print(data['error'])
        print('ITF ', data['delta_itf'])
        if abs(data['delta_itf']) < 5000:
            print(shotn)
            print('ITF ', abs(data['delta_itf']))
            delta_dia = []
            for i, t in enumerate(data['delta_dia']['time']):
                #print(t)
                if t < 0.1:
                    delta_dia.append(data['delta_dia']['data'][i])
                elif t > 0.3:
                    delta_dia.append(data['delta_dia']['data'][i])
            print('dia', sum(delta_dia) / len(delta_dia))
            plt.show()
            checked_fig, ch_ax = plt.subplots(1, 2, sharex=True, figsize=(14, 2))
            print('it has been shown')
        #break




