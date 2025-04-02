import shtRipper
import matplotlib.pyplot as plt
import numpy as np
import json
import math
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import os
import requests
from matplotlib.widgets import MultiCursor
import numpy as np


pi = 3.14159265359
mu0 = 4*pi*1e-7
R0 = 0.36 #geometric centre

#Ip_key = 'Ip внутр.(Пр2ВК) (инт.18)'
Ip_key = 'Ip новый (Пр1ВК) (инт.16)'

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
        try:
            res = shtRipper.ripper.read(filename, data_name)
        except Exception as error:
            print('sht new file error: ', error)
            return {'err': error}

    if 'err' in list(res.keys()):
        return {'err': res['err']}
    smooth_res = {}
    for key in res.keys():
        if key != 'nl 42 cm (1.5мм) 64pi' and key != 'Itf (2TF)(инт.23)' and key != 'Ipf2 верх (7CC) (инт.29)':
            baseline = sum(res[key]['y'][:1000]) / len(res[key]['y'][:1000])
            res[key]['y'] = [i - baseline for i in res[key]['y']]
        smooth_res[key] = {}
        if key == 'Ip новый (Пр1ВК) (инт.16)' or key == 'Ip внутр.(Пр2ВК) (инт.18)':
            smooth_res[key] = {}
            smooth_res[key]['data'] = list(smooth(res[key]['y'][5:-1:10], 31))
            smooth_res[key]['time'] = res[key]['x'][5:-1:10]
        else:
            smooth_res[key]['data'] = list(smooth(res[key]['y'], 95))
            smooth_res[key]['time'] = res[key]['x']
    return smooth_res


def dia_data(shot, recoupment, ax, pf2=False):
    Ip_key = 'Ip новый (Пр1ВК) (инт.16)'
    Up_mult = 0
    Ip_nw_mult = 0
    data_name_need = ['Ip внутр.(Пр2ВК) (инт.18)',   'Itf (2TF)(инт.23)', 'Диамагнитный сигнал (новый инт.)', 'Ics (4CS) (инт.22)',
                  'Up (внутреннее 175 петля)', 'EFC S (инт. 35)', 'EFC N (инт. 27)', 'Ip новый (Пр1ВК) (инт.16)',]

    data_name_need_rec = ['Ip внутр.(Пр2ВК) (инт.18)', 'Itf (2TF)(инт.23)', 'Диамагнитный сигнал (новый инт.)',
                      'Ics (4CS) (инт.22)',
                      'Up (внутреннее 175 петля)','Ip новый (Пр1ВК) (инт.16)',]
    if pf2:
        data_name_need = ['Ip внутр.(Пр2ВК) (инт.18)', 'Itf (2TF)(инт.23)', 'Диамагнитный сигнал (новый инт.)', 'Ics (4CS) (инт.22)',
                          'Up (внутреннее 175 петля)', 'EFC S (инт. 35)', 'EFC N (инт. 27)', 'Ipf2 верх (7CC) (инт.29)', 'Ip новый (Пр1ВК) (инт.16)']

    try:
        data = get_sht_data(shot, data_name_need)
        #data = get_sht_data(shot, [])
        #print('shot OK')
        recoupment_data = get_sht_data(recoupment, data_name_need_rec)
        #print('rec OK')
    except Exception as err:
        return {'data': {}, 'error': err}

    if 'err' in list(data.keys()):
        return {'data': {}, 'error': data['err']}

    if 'err' in list(recoupment_data.keys()):
        return {'data': {}, 'error': recoupment_data['err']}


    dEFC_marker = 1
    for Dtype in data_name_need:
        if Dtype not in data:
            print(Dtype)
            if Dtype == 'EFC N (инт. 27)' or Dtype == 'EFC S (инт. 35)':
                dEFC_marker = 0
            else:
                return {'data': {}, 'error': 'no %s in shot' %Dtype}
    for Dtype in data_name_need_rec:
        if Dtype not in recoupment_data:
            return {'data': {}, 'error': 'no %s in rec shot' %Dtype}
    #fig, ax = plt.subplots(2,1, sharex=True, figsize=(7,5))
    print(max(data[Ip_key]['data']))
    if 0.5 < max(data['Ip новый (Пр1ВК) (инт.16)']['data']) / max(data['Ip внутр.(Пр2ВК) (инт.18)']['data'][:10000]) < 0.95:
        Ip_key = 'Ip внутр.(Пр2ВК) (инт.18)'
        Up_mult = 370
        Ip_nw_mult = 1
    print(Ip_key, max(data[Ip_key]['data']))
    try:
        for i in [1]:
            ax[i-1].set_title(data_name_need[i])
            ax[i-1].plot(data[data_name_need[i]]['time'], data[data_name_need[i]]['data'], label='plasma shot #%i' %shot)
            ax[i-1].plot(recoupment_data[data_name_need[i]]['time'], recoupment_data[data_name_need[i]]['data'], label='without plasma #%i' %recoupment)
            ax[i-1].grid()
            ax[i-1].set_ylabel('Signal, V', fontsize=16)
            ax[i-1].legend()
            ax[i-1].set_xlim(0, 0.4)
        ax[1].set_xlabel('time, s', fontsize=16)
        ax[1].set_ylim(-1, 3)
    except Exception as err:
        if ax != False:
            return {'data': {}, 'error': err}

    deltaITF = sum([data['Itf (2TF)(инт.23)']['data'][i] - recoupment_data['Itf (2TF)(инт.23)']['data'][i] for i in range(len(data['Itf (2TF)(инт.23)']['time']))])/len(data['Itf (2TF)(инт.23)']['time'])

    if shot >= 45624: # с этого момента внесли данный коэффициент прямо в комбископ
        koef_shot = 1e3
    else:
        koef_shot = 3.135

    if recoupment >= 45624:
        koef_rec = 1e3
    else:
        koef_rec = 3.135

    dia_sig1 = [data['Диамагнитный сигнал (новый инт.)']['data'][i] * koef_shot + data['Ics (4CS) (инт.22)']['data'][i] * 8e-6 * 3.135 for i
                in range(len(data['Ics (4CS) (инт.22)']['data']))]
    dia_sig2 = [
        recoupment_data['Диамагнитный сигнал (новый инт.)']['data'][i] * koef_rec + recoupment_data['Ics (4CS) (инт.22)']['data'][
            i] * 8e-6 * 3.135 for i in range(len(data['Ics (4CS) (инт.22)']['data']))]

    try:
        for i in [2]:
            ax[i-1].set_title(data_name_need[i])
            ax[i-1].plot(data[data_name_need[i]]['time'], dia_sig1, label='plasma shot #%i' %shot)
            ax[i-1].plot(recoupment_data[data_name_need[i]]['time'], dia_sig2, label='without plasma #%i' %recoupment)
            ax[i-1].grid()
            ax[i-1].set_ylabel('Signal, V', fontsize=16)
            ax[i-1].legend()
            ax[i-1].set_xlim(0, 0.4)
    except Exception as err:
        if ax != False:
            return {'data': {}, 'error': err}
    #print(len(data['EFC S (инт. 35)']['data']), len(data['EFC N (инт. 27)']['data']))
    if dEFC_marker:
        delta_efc = [data['EFC S (инт. 35)']['data'][i] - data['EFC N (инт. 27)']['data'][i] for i in
                     range(len(data['EFC N (инт. 27)']['data']))]
    else:
        delta_efc = []


    diamagnetic_sig = {'time': data['Диамагнитный сигнал (новый инт.)']['time'],
                       'data': [(dia_sig1[i] - dia_sig2[i]) for i in range(len(dia_sig1))]}

    Ip_all = [data[Ip_key]['data'][i] - data['Up (внутреннее 175 петля)']['data'][i] * Up_mult - Ip_nw_mult*
              (recoupment_data[Ip_key]['data'][i]- recoupment_data['Up (внутреннее 175 петля)']['data'][i] * Up_mult) for i in
              range(len(data[Ip_key]['data']))]

    '''Ip_all = [data[Ip_key]['data'][i] - data['Up (внутреннее 175 петля)']['data'][i] * 370  for i in
              range(len(data[Ip_key]['data']))]'''

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
    z_c = []
    rb = []
    zb = []
    Ip = []
    I_c = []
    Psav = []
    
    Vp = []

    Sp = []
    #q = []
    Rx = []
    Zx = []
    #min_ind = [abs(i) for i in data_mcc['Psav']['variable']].index(min([abs(i) for i in data_mcc['Psav']['variable']]))
    #max_ind = [abs(i) for i in data_mcc['Psav']['variable']].index(max([abs(i) for i in data_mcc['Psav']['variable']]))
    for i, el in enumerate([-i for i in data_mcc['Psav']['variable']]):
        if len(data_mcc['boundary']['zbdy']['variable'][i]) > 100:
            time.append(data_mcc['time']['variable'][i])
            if abs(el) > 10:
                Bzav.append(data_mcc['lp']['variable'][i])
                Psav.append(-data_mcc['Bzav']['variable'][i] + data_mcc['Bzav']['variable'][0])
            else:
                Bzav.append(data_mcc['Bzav']['variable'][i])
                Psav.append(el + data_mcc['Psav']['variable'][0])
            r_c.append(data_mcc['current_coils']['r']['variable'][i])
            z_c.append(data_mcc['current_coils']['z']['variable'][i])
            rb.append(data_mcc['boundary']['rbdy']['variable'][i])
            zb.append(data_mcc['boundary']['zbdy']['variable'][i])
            Ip.append(data_mcc['Ipl']['variable'][i])
            I_c.append(data_mcc['current_coils']['I']['variable'][i])
            Vp.append(data_mcc['Vp']['variable'][i])
            Sp.append(data_mcc['Sp']['variable'][i])
            Rx.append(data_mcc['Rx']['variable'][i])
            Zx.append(data_mcc['Zx']['variable'][i])
            #q.append(data_mcc['q']['variable'][i])



    Rav = [sum([r_c[index_time][i] * I_c[index_time][i] for i in range(len(r_c[index_time]))]) / Ip[index_time] / 100 for index_time in range(len(time))]
    Zav = [sum([z_c[index_time][i] * I_c[index_time][i] * 100 for i in range(len(z_c[index_time]))]) / Ip[index_time] / 100 for index_time in range(len(time))]

    k = [(max(zb[index_time]) - min(zb[index_time])) / (max(rb[index_time]) - min(rb[index_time])) for index_time in range(len(time))]

    a = [(max(rb[index_time]) - min(rb[index_time][1:])) / 200 for index_time in range(len(time))]
    R = [(max(rb[index_time]) + min(rb[index_time][1:])) / 200 for index_time in range(len(time))]

    tr_up = [(R[i] - rb[i][zb[i].index(max(zb[i]))]/100)/a[i] for i in range(len(time))]

    tr_down = [(R[i] - rb[i][zb[i].index(min(zb[i]))]/100)/a[i] for i in range(len(time))]

    Zc = [(max(zb[index_time]) + min(zb[index_time])) / 2 for index_time in range(len(time))]

    Bt_list = []
    B0_list = []
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
    dEFC = []
    pf2_up_data = []
    for j, p in enumerate(time):
        if pf2:
            pf2_up_data.append(-average_1ms(data['Ipf2 верх (7CC) (инт.29)']['time'], data['Ipf2 верх (7CC) (инт.29)']['data'], p)*1e-3)
        Itf = average_1ms(diamagnetic_sig['time'], data['Itf (2TF)(инт.23)']['data'], p)
        Bt = 0.2 * 16 * Itf / 1e6 / Rav[j]
        B0 = 0.2 * 16 * Itf / 1e6 / R0
        Bt_list.append(Bt)
        B0_list.append(B0)
        dia = average_1ms(diamagnetic_sig['time'], diamagnetic_sig['data'], p)
        if dEFC_marker:
            dEFC.append(average_1ms(data['EFC N (инт. 27)']['time'], delta_efc, p))
        else:
            dEFC.append(0)
        dia_sig_mcc.append(dia)
        Ipl = average_1ms(diamagnetic_sig['time'], Ip_all, p)
        Ipl_list.append(Ipl)
        #print(Ipl, dia, Bt, k[j], (k[j] * k[j] + 1) / (2 * k[j]) * Bt * dia / (20 * pi * Ipl / 1e6 * Ipl / 1e6))
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
        #beta_t = 1.6 * pi * W *1e-4 / (3*Bt*Bt*Vp[j])
        beta_t = 4 * mu0 * W / (3*B0*B0*Vp[j])
        beta_t_list.append(beta_t)
        beta_N_list.append(1e8*B0*a[j]*beta_t/Ipl)

    #print(beta_N_list)
    psi_ind_min = min(psi_ind_list[:int(len(psi_ind_list)/2)])
    psi_ind_list = [i-psi_ind_min for i in psi_ind_list]
    psi_res_list = [i+psi_ind_min for i in psi_res_list]
    return {'data': {'time': time, 'data': {'Bt': Bt_list, 'beta_dia': beta_dia_list, 'W_dia': W_dia_list, 'li': li_list,
                                            'dia_sig': dia_sig_mcc, 'Bv': [abs(i*1e-4) for i in Bzav], 'Lp': [i*1e9 for i in Li_list], 'Psi_av': Psav, 'psiInd': psi_ind_list,
                                            'psiRes': psi_res_list, 'beta_t': beta_t_list, 'beta_N': beta_N_list, 'Ipl': Ipl_list, 'Rav': Rav, 'Zav': Zav, 'k': k, 'tr_up': tr_up, 'tr_down': tr_down, 'Vp':Vp,
                                            'Sp': Sp, 'a': a, 'Zc': Zc, 'Rx': Rx, 'Zx': Zx, 'dEFC': dEFC, 'pf2_up': pf2_up_data, 'B0': B0_list},
                     'dimensions': {'Bt': 'T', 'beta_dia': '%', 'W_dia': 'J', 'li': '%',
                                            'dia_sig': 'mWb', 'Bv': 'T', 'Lp': 'nH', 'Psi_av': 'Wb', 'psiInd': 'Wb',
                                            'psiRes': 'Wb', 'beta_t': '%', 'beta_N': 'm*T/A', 'Ipl': 'A', 'Rav': 'm', 'Zav': 'cm', 'k': '%', 'tr_up': '%', 'tr_down': '%', 'Vp': 'm-3',
                                    'Sp': 'm^2', 'a': 'm', 'Zc': 'cm', 'Rx': 'cm', 'Zx': 'cm', 'dEFC': 'V*s', 'pf2_up': 'kA', 'B0': 'T'}},
            'shafr_int_meth': {'time': [i/1000 for i in data_mcc['shafr_int_method']['time']['variable']], 'W': data_mcc['shafr_int_method']['w_eq']['variable'], 'dimensions':{'W': 'J'}},
            'delta_itf': deltaITF, 'delta_dia': {'time': diamagnetic_sig['time'], 'data': diamagnetic_sig['data'], 'dimensions': {'data': 'V*s'}},
            'error': None}


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def make_canvas_interactive(figure_canvas_agg):
    toolbar = NavigationToolbar2Tk(figure_canvas_agg)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)


def move_center(window):
    screen_width, screen_height = window.get_screen_dimensions()
    win_width, win_height = window.size
    x, y = (screen_width - win_width)//2, (screen_height - win_height)//2
    window.move(x, y)


def av_ne(shotn, data, settings, history_list):
    TS_path = '%s%i/' %(settings['TS_path'], shotn)
    line_ind = 0
    data_TS_dyn = {}
    names_list = []
    try:
        with open(TS_path + '%i_dynamics.csv' %shotn, 'r') as dyn_file:
            for line in dyn_file:
                data_dyn_loc = line.split(sep=',')
                if line_ind == 0:
                    for el in data_dyn_loc:
                        data_TS_dyn[el] = {'data': [], 'dimensions': []}
                        names_list.append(el)

                elif line_ind == 1:
                    for i, el in enumerate(data_dyn_loc):
                        data_TS_dyn[names_list[i]]['dimensions'] = el[1:]
                else:
                    for i, el in enumerate(data_dyn_loc):
                        data_TS_dyn[names_list[i]]['data'].append(float(el))
                line_ind += 1
        data_TS_dyn[' T_max'] = {}
        try:
            data_TS_dyn[' T_max']['data'] = data_TS_dyn[' T_max_measured']['data']
            data_TS_dyn[' T_max']['dimensions'] = data_TS_dyn[' T_max_measured']['dimensions']
        except Exception as error:
            print('TS_err is 0:', error)
            data_TS_dyn[' T_max']['data'] = [float('NaN')]*len( data_TS_dyn[' time']['data'])
            data_TS_dyn[' T_max']['dimensions'] = 'eV'
            data_TS_dyn[' T_max_err'] = {'data': [float('NaN')]*len( data_TS_dyn[' time']['data']), 'dimensions': 'eV'}
        history_list[shotn]['TS_data'] = {'time': [i/1000 for i in data_TS_dyn[' time']['data']], '<n>V': data_TS_dyn[' <n>V']['data'],
                           '<n>V_err': data_TS_dyn[' <n>V_err']['data'], '<n>42': data_TS_dyn[' <n>42']['data'], '<n>42_err': data_TS_dyn[' <n>42_err']['data'],
                                          'We': [i/1000 for i in data_TS_dyn[' We']['data']], 'T_max': data_TS_dyn[' T_max']['data'], 'T_max_err':  data_TS_dyn[' T_max_err']['data']}
        data['TS_data'] = history_list[shotn]['TS_data']
        data['TS_data']['dimensions'] = {}
        for key in data['TS_data'].keys():
            if key != 'time' and key != 'dimensions':
                data['TS_data']['dimensions'][key] = data_TS_dyn[' ' + key]['dimensions']
        err = 0
    except Exception as error:
        print('TS_err is:', error)
        err = -1

    return data, history_list, err

# Working

def check_page(window, checked_fig):
    layout = [[sg.Text('Проверьте, что параметры разряда-вычета соответсвуют разряду и, если все в порядке, нажмите ОК', font=16)],
        [sg.Canvas(key='-plot1-')], [sg.Button('OK', font=16), sg.Button('Cancel', font=16, button_color='red')]]

    window_check = sg.Window('Проверка соответствия разряда вычета требуемому разряду', layout, resizable=True, finalize=True)
    plot_left = draw_figure(window_check['-plot1-'].TKCanvas, checked_fig)
    checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
    make_canvas_interactive(plot_left)
    plot_left.draw()
    main_window_x, main_window_y = window.current_location()
    window_check.move(main_window_x+100, main_window_y+100)
    window_check.location = (main_window_x+100, main_window_y+100)

    while True:
        event, values = window_check.read()
        if event == 'Cancel':
            window_check.close()
            return 0
        if  event=='OK':
            window_check.close()
            return 1
        if event == sg.WIN_CLOSED:
            window_check.close()
            return -1
    #window_check.close()

def FindZeroDiscarge(shotn_need,  history_list, ch_ax, checked_fig, maxIndexShot, window, index, settings):
    '''if shotn_need > maxIndexShot:
        window['-err_text-'].update('К сожалению, этот номер разряда еще не внесён в базу данных по поиску разрядов-вычетов (максимум %i). Обратитесь, пожалуйста, к Ткаченко Екатерине.' %maxIndexShot,
                                    background_color='red', text_color='white',
                                    visible=True)
        return 0, 0, 0'''
    for delta in range(2, 500):
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
        if delta % 2:
            shotn = shotn_need + delta // 2
            if shotn > maxIndexShot:
                continue
        else:
            shotn = shotn_need - delta // 2
            if shotn > maxIndexShot:
                continue
        #print(shotn)
        window['-err_text-'].update(
            'Выполняется поиск... %i' %shotn,
            background_color='blue', text_color='white')
        window.refresh()
        event,values = window.read(1)
        if event == 'Stop':
            window['-err_text-'].update(
                'Поиск был принудительно завершен',
                background_color='red', text_color='white')
            window.refresh()
            return 0, 0, 0, history_list
        if 'err' in list(index[str(shotn)].keys()):
            #print(shotn, index[str(shotn)]['err'])
            if 'has suspicious file size' in index[str(shotn)]['err']:
                continue
            # time.sleep(1)
            data = dia_data(shotn_need, shotn, ch_ax, pf2=False)
            if data['error']:
                #print(data['error'])
                continue
            # print(data['error'])
            #print('ITF ', data['delta_itf'])
            if abs(data['delta_itf']) < 5000:
                #print(shotn)
                #print('ITF ', abs(data['delta_itf']))
                delta_dia = []
                for i, t in enumerate(data['delta_dia']['time']):
                    # print(t)
                    if t < 0.1:
                        delta_dia.append(data['delta_dia']['data'][i])
                    elif t > 0.3:
                        delta_dia.append(data['delta_dia']['data'][i])
                if sum(delta_dia) / len(delta_dia) < 0.5:
                    checkRes = check_page(window, checked_fig)
                    #print(checkRes)
                    if checkRes==1:
                        window['-err_text-'].update(visible=False)
                        window.refresh()
                        history_list[shotn_need] = data
                        if data:
                            if 'TS_data' not in list(data.keys()):
                                data,  history_list, err = av_ne(shotn_need, data, settings, history_list)
                                #print(data.keys())
                        return data, shotn_need, shotn, history_list
                    elif checkRes==-1:
                        return 0, 0, 0, history_list

#Working

def Save_files(settings, data, shotn, rec):
    try:
        PATH_for_save = settings['path_out']

        '''if 'TS_data' not in list(data.keys()):
            data['TS_data'] = {}'''
        for_dump = {}
        for_dump['compensation'] = rec
        for key in data.keys():
            if key == 'data':
                for_dump['time'] = data['data']['time']
                for_dump['data'] = data['data']['data']
                for_dump['dimensions'] = data['data']['dimensions']
            else:
                for_dump[key] = data[key]
        with open('%sjson/%i.json' % (PATH_for_save, shotn), 'w') as json_f:
            json.dump(for_dump, json_f)
        to_pack = {}
        #print('yes1')
        for key in data.keys():
            # print(key, type(data[key]))
            if key != 'data' and key != 'TS_data' and key != 'dimensions' and type(data[key]) == dict:
                for key2 in data[key].keys():
                    if key2 != 'time' and key2 != 'dimensions':
                        to_pack[key + '_' + key2] = {
                            'comment': 'data from %s' % key,
                            'unit': '%s(%s)' % (key2, data[key]['dimensions'][key2]),
                            'tMin': min(data[key]['time']),  # mininun time
                            'tMax': max(data[key]['time']),  # maximum time
                            'offset': 0.0,  # ADC zero level offset
                            'yRes': 0.0001,  # ADC resolution: 0.0001 Volt per adc bit
                            'y': data[key][key2]
                        }
                #print('yes1.1')
            elif key == 'TS_data':
                for key2 in data[key].keys():
                    # print(key2)
                    if 'err' not in key2 and key2 != 'time' and key2 != 'dimensions' and key2 != 'We':
                        to_pack[key2] = {
                            'comment': 'data from %s' % key,
                            'unit': '%s(%s)' % (key2, data[key]['dimensions'][key2]),
                            'x': data[key]['time'],
                            'y': data[key][key2],
                            'err': data[key][key2 + '_err']
                        }
                    if key2 == 'We':
                        to_pack[key2] = {
                            'comment': 'data from %s' % key,
                            'unit': '%s(%s)' % (key, data[key]['dimensions'][key2]),
                            'tMin': min(data[key]['time']),  # mininun time
                            'tMax': max(data[key]['time']),  # maximum time
                            'offset': 0.0,  # ADC zero level offset
                            'yRes': 0.0001,  # ADC resolution: 0.0001 Volt per adc bit
                            'y': data[key][key2]
                        }
        #print('yes1.2')
        data = data['data']
        #print('yes2')
        with open('%stxt/%i.txt' % (PATH_for_save, shotn), 'w') as txt_f:
            txt_f.write('%12s' % 'time')
            for key in data['data']:
                txt_f.write('%12s' % key)
            txt_f.write('\n')
            txt_f.write('%12s' % 's')
            for key in data['data']:
                txt_f.write('%12s' % data['dimensions'][key])
            txt_f.write('\n')
            for i in range(len(data['time'])):
                txt_f.write('%12.4f' % data['time'][i])
                for key in data['data']:
                    if data['data'][key]:
                        txt_f.write('%12.4f' % data['data'][key][i])
                    else:
                        txt_f.write('%12s' % 'None')
                txt_f.write('\n')
        for key in data['data'].keys():
            to_pack[key] = {
                'comment': '',
                'unit': '%s(%s)' % (key, data['dimensions'][key]),
                'tMin': min(data['time']),  # mininun time
                'tMax': max(data['time']),  # maximum time
                'offset': 0.0,  # ADC zero level offset
                'yRes': 0.0001,  # ADC resolution: 0.0001 Volt per adc bit
                'y': data['data'][key]
            }
        #print('yes3')
        packed = shtRipper.ripper.write(path=(PATH_for_save + 'sht/'), filename='%i.SHT' % shotn, data=to_pack)
        if len(packed) != 0:
            print('packed error = "%s"' % packed)
        return 0

    except Exception as exep:
        print(exep)
        return exep

def open_Zeff_data(shot):
    ZeffDataPath = 'Z:/Tuxmeneva/Zeff/'
    ZeffData = {'time': [], 'ne': [], 'Zeff': [], 'errZeff': []}
    try:
        with open('%s%s_Zeff.txt' % (ZeffDataPath, shot), 'r') as Zfile:
            for line in Zfile:
                rawDataZ = line.split()
                if len(rawDataZ):
                    for i in range(len(rawDataZ)):
                        rawDataZ[i] = rawDataZ[i].replace(',', '.')
                        try:
                            rawDataZ[i] = float(rawDataZ[i])
                        except ValueError:
                            rawDataZ = []
                            break
                    if len(rawDataZ) == 5:
                        ZeffData['time'].append(float(rawDataZ[1]))
                        ZeffData['ne'].append(float(rawDataZ[2]))
                        ZeffData['Zeff'].append(float(rawDataZ[3]))
                        ZeffData['errZeff'].append(float(rawDataZ[4]))
                    elif len(rawDataZ) == 4:
                        ZeffData['time'].append(float(rawDataZ[1]))
                        ZeffData['Zeff'].append(float(rawDataZ[2]))
                        ZeffData['errZeff'].append(float(rawDataZ[3]))
                    elif len(rawDataZ) == 3:
                        ZeffData['time'].append(float(rawDataZ[0]))
                        ZeffData['Zeff'].append(float(rawDataZ[1]))
                        ZeffData['errZeff'].append(float(rawDataZ[2]))
                    else:
                        ZeffData = {}
    except FileNotFoundError:
        print('no Zeff')
        ZeffData = {}

    return ZeffData

