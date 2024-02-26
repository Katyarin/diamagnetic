import shtRipper
import matplotlib.pyplot as plt
import numpy as np
import json
import math
pi = 3.14159265359
mu0 = 4*pi*1e-7


def li(Bv, R, Ip, a, k, beta_dia):
    beta_li = (Bv * 4 * pi * R) / (mu0 * Ip) - math.log(8*R/a/math.sqrt(k)) + 3/2
    return (beta_li - beta_dia) * 2

def Lp(li, R, a, k):
    return (mu0 * R) * (math.log(8*R/a/math.sqrt(k)) - 2 + li/2)


def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth


def average_1ms(listTime, listData, time):
    av = 0
    len_av = 0
    for i, t in enumerate(listTime):
        if abs(time-t) < 0.001:
            av+= listData[i]
            len_av+=1
    return av/len_av


def get_sht_data(Shotn, data_name):
    with open('settings.json', 'r') as set_file:
        settings = json.load(set_file)
    filename = settings['path_in'] % Shotn
    res = shtRipper.ripper.read(filename, data_name)
    if 'err' in list(res.keys()):
        filename = settings['path_in_new'] % Shotn
        res = shtRipper.ripper.read(filename, data_name)

    if 'err' in list(res.keys()):
        return {'err': res['err']}
    smooth_res = {}
    for key in res.keys():
        if key != 'nl 42 cm (1.5мм) 64pi':
            baseline = sum(res[key]['y'][:1000]) / len(res[key]['y'][:1000])
            res[key]['y'] = [i - baseline for i in res[key]['y']]
        smooth_res[key] = {}
        if key == 'Ip внутр.(Пр2ВК) (инт.18)':
            smooth_res[key] = {}
            smooth_res[key]['data'] = list(smooth(res[key]['y'][5:-1:10], 31))
            smooth_res[key]['time'] = res[key]['x'][5:-1:10]
        else:
            smooth_res[key]['data'] = list(smooth(res[key]['y'], 95))
            smooth_res[key]['time'] = res[key]['x']
    return smooth_res


def dia_data(shot, recoupment, ax):

    data_name_need = ['Ip внутр.(Пр2ВК) (инт.18)', 'Itf (2TF)(инт.23)', 'Диамагнитный сигнал (новый инт.)', 'Ics (4CS) (инт.22)',
                  'Up (внутреннее 175 петля)', 'Программа тока Ip']


    data = get_sht_data(shot, data_name_need)
    recoupment_data = get_sht_data(recoupment, data_name_need)

    if 'err' in list(data.keys()):
        return {'data': {}, 'error': data['err']}

    if 'err' in list(recoupment_data.keys()):
        return {'data': {}, 'error': recoupment_data['err']}

    #fig, ax = plt.subplots(2,1, sharex=True, figsize=(7,5))
    for i in [1,2]:
        ax[i-1].set_title(data_name_need[i])
        ax[i-1].plot(data[data_name_need[i]]['time'], data[data_name_need[i]]['data'], label='plasma shot')
        ax[i-1].plot(recoupment_data[data_name_need[i]]['time'], recoupment_data[data_name_need[i]]['data'], label='without plasma')
        ax[i-1].grid()
        ax[i-1].set_ylabel('Signal, V', fontsize=16)
        ax[i-1].legend()
        ax[i-1].set_xlim(0, 0.4)
    ax[1].set_xlabel('time, s', fontsize=16)
    ax[1].set_ylim(-1, 3)

    dia_sig1 = [data['Диамагнитный сигнал (новый инт.)']['data'][i] + data['Ics (4CS) (инт.22)']['data'][i] * 8e-6 for i
                in range(len(data['Ics (4CS) (инт.22)']['data']))]
    dia_sig2 = [
        recoupment_data['Диамагнитный сигнал (новый инт.)']['data'][i] + recoupment_data['Ics (4CS) (инт.22)']['data'][
            i] * 8e-6 for i in range(len(data['Ics (4CS) (инт.22)']['data']))]

    diamagnetic_sig = {'time': data['Диамагнитный сигнал (новый инт.)']['time'],
                       'data': [(dia_sig1[i] - dia_sig2[i]) * 2.915 for i in range(len(dia_sig1))]}

    Ip_all = [data['Ip внутр.(Пр2ВК) (инт.18)']['data'][i] - data['Up (внутреннее 175 петля)']['data'][i] * 370 -
              recoupment_data['Ip внутр.(Пр2ВК) (инт.18)']['data'][i] for i in
              range(len(data['Ip внутр.(Пр2ВК) (инт.18)']['data']))]

    '''current fillament method'''

    f = '//172.16.12.127/Pub/!!!CURRENT_COIL_METHOD/V3_zad7_mcc/mcc_%d.json' % shot
    try:
        with open(f, 'r') as file:
            data_mcc = json.load(file)
    except FileNotFoundError:
        return {'data': {}, 'error': "MCC file does not exist"}
    time = []
    Bzav = []
    r_c = []
    rb = []
    zb = []
    Ip = []
    I_c = []
    Psav = []
    Vp = []
    #min_ind = [abs(i) for i in data_mcc['Psav']['variable']].index(min([abs(i) for i in data_mcc['Psav']['variable']]))
    #max_ind = [abs(i) for i in data_mcc['Psav']['variable']].index(max([abs(i) for i in data_mcc['Psav']['variable']]))
    for i, el in enumerate([-i for i in data_mcc['Psav']['variable']]):
        time.append(data_mcc['time']['variable'][i])
        if abs(el) > 10:
            Bzav.append(data_mcc['lp']['variable'][i])
            Psav.append(-data_mcc['Bzav']['variable'][i] + data_mcc['Bzav']['variable'][0])
        else:
            Bzav.append(data_mcc['Bzav']['variable'][i])
            Psav.append(el + data_mcc['Psav']['variable'][0])
        r_c.append(data_mcc['current_coils']['r']['variable'][i])
        rb.append(data_mcc['boundary']['rbdy']['variable'][i])
        zb.append(data_mcc['boundary']['zbdy']['variable'][i])
        Ip.append(data_mcc['Ipl']['variable'][i])
        I_c.append(data_mcc['current_coils']['I']['variable'][i])
        Vp.append(data_mcc['Vp']['variable'][i])

    Rav = [sum([r_c[index_time][i] * I_c[index_time][i] for i in range(len(r_c[index_time]))]) / Ip[index_time] / 100 for index_time in range(len(time))]

    k = [(max(zb[index_time][1:]) - min(zb[index_time])) / (max(rb[index_time]) - min(rb[index_time])) for index_time in range(len(time))]

    a = [(max(rb[index_time][1:]) - min(rb[index_time][1:])) / 200 for index_time in range(len(time))]

    tr_up = [(Rav[i] - rb[i][zb[i].index(max(zb[i]))]/100)/a[i] for i in range(len(time))]

    tr_down = [(Rav[i] - rb[i][zb[i].index(min(zb[i]))]/100)/a[i] for i in range(len(time))]

    Bt_list = []
    beta_dia_list = []
    W_dia_list = []
    li_list = []
    dia_sig_mcc = []
    Li_list = []
    beta_t_list = []
    beta_N_list = []
    psi_res_list = []
    psi_ind_list = []
    Ipl_list = []
    for j, p in enumerate(time):
        Itf = average_1ms(diamagnetic_sig['time'], data['Itf (2TF)(инт.23)']['data'], p)
        Bt = 0.2 * 16 * Itf / 1e6 / Rav[j]
        Bt_list.append(Bt)
        dia = average_1ms(diamagnetic_sig['time'], diamagnetic_sig['data'], p)
        dia_sig_mcc.append(dia)
        Ipl = average_1ms(diamagnetic_sig['time'], Ip_all, p)
        Ipl_list.append(Ipl)
        #print(Ipl)
        beta_dia = 1 - (k[j] * k[j] + 1) / (2 * k[j]) * Bt * dia / (20 * pi * Ipl / 1e6 * Ipl / 1e6)
        beta_dia_list.append(beta_dia)
        W = 3/2 * beta_dia * (mu0 * Ipl * Ipl * Rav[j])/4
        W_dia_list.append(W)

        li_loc = li(-Bzav[j]/10000, Rav[j], Ipl, a[j], k[j], beta_dia)
        li_list.append(li_loc)
        Lp_loc = Lp(li=li_loc, R=Rav[j], a=a[j], k=k[j])
        Li_list.append(Lp_loc)

        psi_ind = Lp_loc * Ipl
        psi_ind_list.append(psi_ind)
        psi_res_list.append(Psav[j] - psi_ind)
        beta_t = 1.6 * pi * W *1e-4 / (3*Bt*Bt*Vp[j])
        beta_t_list.append(beta_t)
        beta_N_list.append(100*Bt*a[j]*beta_t*1e3/Ipl)

    print(beta_N_list)
    psi_ind_min = min(psi_ind_list[:int(len(psi_ind_list)/2)])
    psi_ind_list = [i-psi_ind_min for i in psi_ind_list]
    psi_res_list = [i+psi_ind_min for i in psi_res_list]
    return {'data': {'time': time, 'data': {'Bt': Bt_list, 'beta_dia': beta_dia_list, 'W_dia': W_dia_list, 'li': li_list,
                                            'dia_sig': dia_sig_mcc, 'Bv': [abs(i*1e-4) for i in Bzav], 'Lp': [i*1e9 for i in Li_list], 'Psi_av': Psav, 'psiInd': psi_ind_list,
                                            'psiRes': psi_res_list, 'beta_t': beta_t_list, 'beta_N': beta_N_list, 'Ipl': Ipl_list, 'Rav': Rav, 'k': k, 'tr_up': tr_up, 'tr_down': tr_down, 'Vp':Vp},
                     'dimensions': {'Bt': 'T', 'beta_dia': '%', 'W_dia': 'J', 'li': '%',
                                            'dia_sig': 'mWb', 'Bv': 'T', 'Lp': 'nH', 'Psi_av': 'Wb', 'psiInd': 'Wb',
                                            'psiRes': 'Wb', 'beta_t': '%', 'beta_N': 'mm*T/A', 'Ipl': 'A', 'Rav': 'm', 'k': '%', 'tr_up': '%', 'tr_down': '%', 'Vp': 'm-3'}},
            'shafr_int_meth': {'time': [i/1000 for i in data_mcc['shafr_int_method']['time']['variable']], 'W': data_mcc['shafr_int_method']['w_eq']['variable'], 'dimensions':{'W': 'J'}},
            'error': None}
