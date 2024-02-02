import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import dia_sig
import json
import numpy as np
import shtRipper
import os

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

plt.rcParams['axes.facecolor']='#E3F2FD'
plt.rcParams['figure.facecolor']='#E3F2FD'
px = 1/plt.rcParams['figure.dpi']
color_list = ['b', 'r', 'm', 'g', 'black']
color_list2 = ['cyan', 'orange', 'pink', 'olive', 'gray']
data_add = {'dimensions': {'Bt': 'T', 'beta_dia': '%', 'W_dia': 'J', 'li': '%',
                                            'dia_sig': 'mWb', 'Bv': 'T', 'Lp': 'nH', 'Psi_av': 'Wb', 'psiInd': 'Wb',
                                            'psiRes': 'Wb', 'beta_t': '%', 'beta_N': 'm*T/MA'}, 'error': None}

#PATH_for_save_PUB = '//172.16.12.127/Pub/!diamagnetic_data'
#PATH_for_save = 'c:/work/Data/diamagnetic_data/'
#PATH_for_save = 'c:/work/Data/diamagnetic_data/'

with open('settings.json', 'r') as set_file:
    settings = json.load(set_file)


sg.theme('Material1')
layout = [  [sg.Text('Для расчета введите номер разряда и номер вычета', font=16)],
            [sg.Text('Разряд #', font=16), sg.Input(key='-SHOT-', font=16), sg.Text('Вычет #', font=16), sg.Input(key='-RECSHOT-', font=16)],
            [sg.Button('Ok', font=16), sg.Button('Append', font=16), sg.Button('Save', font=16), sg.Button('Read Me', font=16), sg.Button('Settings', font=16)],
            [sg.Text(key='-err_text-', font=16), sg.Button('ReCalc', font=16, visible=False)],
            [sg.Canvas(key='-plot2-',expand_x=True, expand_y=True)], [sg.Text('Created by Tkachenko E.E.', text_color='gray', justification='right', expand_x=True)]]

window = sg.Window('Расчет данных по диамагнитному сигналу', layout, resizable=True, finalize=True)

screen_size = sg.Window.get_screen_size()
#print(screen_size)


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def make_canvas_interactive(figure_canvas_agg):
    toolbar = NavigationToolbar2Tk(figure_canvas_agg)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)


def deffinition():
    layout = [[sg.Text('Описание кнопок', font=('TimesNewRoman', 20,'bold underline'))],
                       [sg.vtop(sg.Text('Ok  \n \n \n Append  \n \n Save \n \n\n ReCalc  ', font=('TimesNewRoman', 16,'bold'), justification='right')),
                        sg.vtop(sg.Text('вывести данные разряда на экран. Можно не вводить номер вычета, \n если файл есть в базе данных, то программа загрузит разряд из базы \n'
                       '\nдобавить на графики данные введенного разряда \n'
                                '\n сохранить данные в txt, json и sht файлы. \n Директория по умолчанию: Pub/!!diamagnetic_data/ \n'
                                '\n пересчитать разряд заново (необходимо ввести номер разряда-вычета', font=16, expand_x=True))],
              [sg.Text('Формулы', font=('TimesNewRoman', 20,'underline bold'))],
              [sg.Canvas(key='-def-')],
              [sg.Button('Close')]]
    figDef, axDef = plt.subplots(1,1, figsize=(8,6))
    #figDef.suptitle('Definitions')
    axDef.cla()
    axDef.text(0.2, 0.9, r'$B_{T} = \frac{0.2 \cdot 16 \cdot I_{tf}}{10^6 \cdot R_{av}}$', fontsize=16)
    axDef.text(0.2, 0.825, r'$B_{v} = \frac{\mu_0 I_p}{4 \pi R_{av}}\left(\ln \frac{8 R_{av}}{a \sqrt{\kappa}}-\frac{3}{2}+\beta_p+\frac{l_i}{2}\right)$', fontsize=16)
    axDef.text(0.2, 0.75, r'$\beta_{dia} = 1-\frac{\kappa^2+1}{2 \kappa} \frac{B_T \Psi_{d i a}}{20 \pi I_p^2}$', fontsize=16)
    axDef.text(0.2, 0.675, r'$W_{dia} = \frac{3}{2} \frac{\beta_{d i a} \mu_0 I_p^2 R_{av}}{4}$', fontsize=16)
    axDef.text(0.2, 0.6, r'$l_{i} = 2 \cdot \left(B_{v} \cdot \frac{4 \pi R_{av}}{\mu_0 I_p} - \left(\ln \frac{8 R_{av}}{a \sqrt{\kappa}}-\frac{3}{2}+\beta_p\right)\right)$', fontsize=16)
    axDef.text(0.2, 0.525, r'$L_{p} = \mu_0 R\left(\ln \left(\frac{8 R_{av}}{a \sqrt{\kappa}}\right)-2+\frac{l_i}{2}\right)$', fontsize=16)
    axDef.text(0.2, 0.45, r'$\Psi_{av}$ - магнитный поток, усредненный по кольцам', fontsize=16)
    axDef.text(0.2, 0.375, r'$\Psi_{ind} = I_{p} \cdot L_{p}$', fontsize=16)
    axDef.text(0.2, 0.3, r'$\Psi_{res} = \Psi_{av} - \Psi_{ind}$', fontsize=16)
    axDef.text(0.2, 0.225, r'$\beta_{T} = \frac{4\mu_0 \cdot W_{dia}}{3\cdot B_{T} \cdot V}$', fontsize=16)
    axDef.text(0.2, 0.15, r'$\beta_{N} = \frac{100\cdot a \cdot B_T \cdot \beta_T}{I_p}$', fontsize=16)
    axDef.text(0.2, 0.1, r'где $I_{tf}$ - ток в катушках тороидального магнитного поля,', fontsize=10)
    axDef.text(0.2, 0.075, r'$R_{av}$ - радиус центра тяжести токовых колец,', fontsize=10)
    axDef.text(0.2, 0.05, r'$I_p$ - ток плазмы, $\kappa$ - вытянутость, ', fontsize=10)
    axDef.text(0.2, 0.025, r'$\mu_0 = 4 \pi \cdot 10^{-7}$, $a$ - малый радиус плазмы', fontsize=10)
    axDef.get_xaxis().set_visible(False)
    axDef.get_yaxis().set_visible(False)
    '''axDef.patch.set_alpha(0.9)'''
    figDef.subplots_adjust(left=-0.1, bottom=-0.005, right=1.005, top=1.005, wspace=0, hspace=0)
    window2 = sg.Window('Read Me', layout, modal=True, finalize=True, resizable=True)
    draw_figure(window2['-def-'].TKCanvas, figDef)
    while True:
        event, values = window2.read()
        if event == sg.WIN_CLOSED or event=='Close':
            break
    window2.close()


def set_page():
    layout = [[sg.Text('Select folder for saving files:')],
              [sg.Input(enable_events=True, key='-IN-',font=('Arial Bold', 12),expand_x=True), sg.FolderBrowse(initial_folder=settings['path_out'], key='br_save')],
              [sg.Button('Save', key='-saving-'), sg.Text('Путь сохранен', key='-saveTxt-', visible=False)],
              [sg.Text('Select folder for reading sht files:')],
              [sg.Input(enable_events=True, key='-shtIN-', font=('Arial Bold', 12), expand_x=True),
               sg.FolderBrowse(initial_folder=settings['path_in'], key='br_sht')],
              [sg.Button('Save', key='-shtFolder-'), sg.Text('Путь сохранен', key='-shtTxt-', visible=False)],
              [sg.Text('Select folder for reading new sht files:')],
              [sg.Input(enable_events=True, key='-shtNewIN-', font=('Arial Bold', 12), expand_x=True),
               sg.FolderBrowse(initial_folder=settings['path_in_new'], key='br_sht_new')],
              [sg.Button('Save', key='-shtNewFolder-'), sg.Text('Путь сохранен', key='-shtNewTxt-', visible=False)]
              ]
    set_window = sg.Window('Settings', layout=layout)
    while True:
        event, values = set_window.read()
        if event == '-saving-':
            settings['path_out'] = str(values['-IN-']) + '/'
            with open('settings.json', 'w') as set_new_file:
                json.dump(settings, set_new_file, indent=2)
            if not os.path.isdir('%sjson' % (settings['path_out'])):
                os.mkdir('%sjson' % (settings['path_out']))
            if not os.path.isdir('%stxt' % (settings['path_out'])):
                os.mkdir('%stxt' % (settings['path_out']))
            if not os.path.isdir('%ssht' % (settings['path_out'])):
                os.mkdir('%ssht' % (settings['path_out']))
            set_window['-saveTxt-'].update(visible=True)
        if event == '-shtFolder-':
            settings['path_in'] = str(values['-shtIN-']) + '/sht%i.sht'
            with open('settings.json', 'w') as set_new_file:
                json.dump(settings, set_new_file, indent=2)
            set_window['-shtTxt-'].update(visible=True)
        if event == '-shtNewFolder-':
            settings['path_in_new'] = str(values['-shtNewIN-']) + '/sht%i.sht'
            with open('settings.json', 'w') as set_new_file:
                json.dump(settings, set_new_file, indent=2)
            set_window['-shtNewTxt-'].update(visible=True)
        if event == sg.WIN_CLOSED:
            break
    set_window.close()


checked_fig, ch_ax = plt.subplots(2, 1, sharex=True, figsize=(10, 6))


def check_page():
    layout = [[sg.Text('Проверьте, что параметры разряда-вычета соответсвуют разряду и, если все в порядке, нажмите ОК', font=16)],
        [sg.Canvas(key='-plot1-')], [sg.Button('OK', font=16)]]

    window_check = sg.Window('Проверка соответствия разряда вычета требуемому разряду', layout, resizable=True, finalize=True)
    plot_left = draw_figure(window_check['-plot1-'].TKCanvas, checked_fig)
    checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
    make_canvas_interactive(plot_left)
    plot_left.draw()


    while True:
        event, values = window_check.read()
        if event == sg.WIN_CLOSED or event=='OK':
            break
    window_check.close()


fig, axs = plt.subplots(4, 2, sharex=True, figsize=((screen_size[0]*px, screen_size[1]*0.8*px)))
plot_right = draw_figure(window['-plot2-'].TKCanvas, fig)
make_canvas_interactive(plot_right)
color_count = 0


def draw_data(data, shotn, color_count):
    if data['error'] == None:
        axs[0, 0].plot(data['data']['time'], data['data']['data']['Bt'], label='Bt %i' %shotn, color=color_list[color_count])
        axs[0, 0].plot(data['data']['time'], data['data']['data']['Bv'], '--', label='Bv %i' %shotn, color=color_list[color_count])
        axs[1, 0].plot(data['data']['time'], data['data']['data']['beta_dia'], label=shotn, color=color_list[color_count])
        axs[2, 0].plot(data['data']['time'], [i/1000 for i in data['data']['data']['W_dia']], label=shotn, color=color_list[color_count])
        axs[3, 0].plot(data['data']['time'], data['data']['data']['li'], label=shotn, color=color_list[color_count])
        axs[0, 1].plot(data['data']['time'], data['data']['data']['Lp'], label=shotn, color=color_list[color_count])
        axs[2, 1].plot(data['data']['time'], data['data']['data']['beta_t'], label=shotn, color=color_list[color_count])
        axs[3, 1].plot(data['data']['time'], data['data']['data']['beta_N'], label=shotn, color=color_list[color_count])

        '''psiAv = smooth([data['data']['data']['Psi_av'][1] - data['data']['data']['Psi_av'][0]]
                       +[(data['data']['data']['Psi_av'][i+1] - data['data']['data']['Psi_av'][i-1])/2 for i in range(1, len(data['data']['data']['Psi_av'])-1)] +
                       [data['data']['data']['Psi_av'][-1] - data['data']['data']['Psi_av'][-2]], 4)
        axs[1, 1].plot(data['data']['time'], psiAv, label=r'$\Delta \Psi_{av}$ %i' %shotn)

        psiInd = smooth([data['data']['data']['psiInd'][1] - data['data']['data']['psiInd'][0]]
                       + [(data['data']['data']['psiInd'][i + 1] - data['data']['data']['psiInd'][i - 1]) / 2 for i in
                          range(1, len(data['data']['data']['psiInd']) - 1)] +
                       [data['data']['data']['psiInd'][-1] - data['data']['data']['psiInd'][-2]], 4)
        axs[1, 1].plot(data['data']['time'], psiInd,
                       label=r'$\Delta \Psi_{ind}$ %i' % shotn)'''

        '''axs[1, 1].plot(data['data']['time'], [data['data']['data']['psiRes'][1] - data['data']['data']['psiRes'][0]]
                       + [(data['data']['data']['psiRes'][i + 1] - data['data']['data']['psiRes'][i - 1]) / 2 for i in
                          range(1, len(data['data']['data']['psiRes']) - 1)] +
                       [data['data']['data']['psiRes'][-1] - data['data']['data']['psiRes'][-2]],
                       label=r'$\Delta \Psi_{res}$ %i' % shotn)'''


        axs[1, 1].plot(data['data']['time'], data['data']['data']['Psi_av'], '--', label=r'$\Psi_{av}$ %i' %shotn, color=color_list[color_count])
        axs[1, 1].plot(data['data']['time'], data['data']['data']['psiInd'], '-', label=r'$\Psi_{ind}$ %i' %shotn, color=color_list[color_count])
        axs[1, 1].plot(data['data']['time'], data['data']['data']['psiRes'], '.', label=r'$\Psi_{res}$ %i' %shotn, color=color_list2[color_count])


        axs[0, 0].set_ylabel(r'$B, T$')
        #axs[0, 0].set_xlim(0.110, 0.3)
        axs[0, 0].set_ylim(0, 1)
        axs[1, 0].set_ylabel(r'$\beta_{dia}$')
        axs[1, 0].set_ylim(0, 0.6)
        axs[2, 0].set_ylabel(r'$W_{dia}, kJ$')
        axs[2, 0].set_ylim(0, 20)
        axs[3, 0].set_ylabel(r'$l_{i}$')
        axs[3, 0].set_ylim(0, 2)
        axs[0, 1].set_ylabel(r'$L_{p}, nH$')
        axs[1, 1].set_ylabel(r'$\Psi, Wb$')
        axs[2, 1].set_ylabel(r'$\beta_{T}, %$')
        axs[3, 1].set_ylabel(r'$\beta_{N}, m \cdot T / MA$')
        #axs[3, 0].set_ylim(0, 2)
        axs[3, 0].set_xlabel('time, s')
        axs[3, 1].set_xlabel('time, s')

        count =0
        for ax in axs:
            for subax in ax:
                subax.legend()
                if count in [2, 3, 6, 7]:
                    #subax.yaxis.set_label_position("right")
                    subax.yaxis.tick_right()
                count+=1

        '''checked_fig.suptitle('shot #%i' % shotn, fontsize=16)

        plot_left.draw()'''
        plot_right.draw()
    else:
        window['-err_text-'].update('ОШИБКА!!! %s' %data['error'], background_color='red')


def data_open(values, ReCalc=False):
    try:
        shotn = int(values['-SHOT-'])
    except:
        window['-err_text-'].update('ОШИБКА! Введите целочисленный номер разряда', background_color='red')
        shotn = 0
    if ReCalc:
        try:
            rec = int(values['-RECSHOT-'])
        except:
            window['-err_text-'].update('ОШИБКА! Введите целочисленный номер вычета', background_color='red')
            rec = 0

        if rec * shotn:
            data = dia_sig.dia_data(shotn, rec, ch_ax)
            check_page()
    else:
        try:
            PATH_for_save = settings['path_out']
            with open('%sjson/%i.json' % (PATH_for_save, shotn), 'r') as json_f:
                data_new = json.load(json_f)
            data = {'data': {'time': data_new['time'], 'data': data_new['data'], 'dimensions': data_add['dimensions']},
                    'error': data_add['error']}
            rec = data_new['compensation']
            window['-err_text-'].update('Данные загружены из базы данных (вычет: %i), если хотите пересчитать, введите номер вычета и нажмите ReCalc' %rec, background_color='green')
            window['ReCalc'].update(visible=True)
        except:
            try:
                rec = int(values['-RECSHOT-'])
            except:
                window['-err_text-'].update('ОШИБКА! Введите целочисленный номер вычета', background_color='red')
                rec = 0
                return 0, 0, 0

            if rec * shotn:
                data = dia_sig.dia_data(shotn, rec, ch_ax)
                check_page()
    return data, shotn, rec


data = {}
shotn = 0
rec = 0
window.Maximize()

while True:
    event, values = window.read()
    if event == 'Ok':
        color_count = 0
        window['-err_text-'].update('', background_color=None)
        window['ReCalc'].update(visible=False)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.06, right=0.95, top=0.983, wspace=0.126, hspace=0)
        data, shotn, rec = data_open(values)
        if int(shotn*rec):
            draw_data(data, shotn, color_count)

    if event == 'Append':
        color_count += 1
        if color_count == len(color_list):
            color_count = 0
        window['-err_text-'].update('', background_color=None)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.062, bottom=0.26, right=0.95, top=0.843, wspace=0.126, hspace=0)
        data, shotn, rec = data_open(values)
        if int(shotn * rec):
            draw_data(data, shotn, color_count)

    if event == 'Save':
        PATH_for_save = settings['path_out']
        window['ReCalc'].update(visible=False)
        data = data['data']
        with open('%sjson/%i.json' %(PATH_for_save, shotn), 'w') as json_f:
            json.dump({'compensation': rec, 'time': data['time'], 'data': data['data']}, json_f)
        with open('%stxt/%i.txt' %(PATH_for_save, shotn), 'w') as txt_f:
            txt_f.write('%12s' %'time')
            for key in data['data']:
                txt_f.write('%12s' %key)
            txt_f.write('\n')
            txt_f.write('%12s' % 's')
            for key in data['data']:
                txt_f.write('%12s' % data['dimensions'][key])
            txt_f.write('\n')
            for i in range(len(data['time'])):
                txt_f.write('%12.4f' %data['time'][i])
                for key in data['data']:
                    txt_f.write('%12.4f' % data['data'][key][i])
                txt_f.write('\n')
        to_pack = {}
        for key in data['data']:
            to_pack[key] = {
                'comment': '',
                'unit': '%s(%s)' %(key, data['dimensions'][key]),
                'tMin': min(data['time']),  # mininun time
                'tMax': max(data['time']),  # maximum time
                'offset': 0.0,  # ADC zero level offset
                'yRes': 0.0001,  # ADC resolution: 0.0001 Volt per adc bit
                'y': data['data'][key]
            }
        packed = shtRipper.ripper.write(path=(PATH_for_save + 'sht/'), filename='%i.SHT' %shotn, data=to_pack)
        if len(packed) != 0:
            print('packed error = "%s"' % packed)
        window['-err_text-'].update('Файлы сохранены в папку %s' %PATH_for_save, background_color='green')

    if event == 'Read Me':
        deffinition()

    if event == 'Settings':
        set_page()

    if event == 'ReCalc':
        window['-err_text-'].update('', background_color=None)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.062, bottom=0.26, right=0.95, top=0.843, wspace=0.126, hspace=0)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.06, right=0.95, top=0.983, wspace=0.126, hspace=0)
        data, shotn, rec = data_open(values, ReCalc=True)
        if int(shotn*rec):
            draw_data(data, shotn, color_count)
        #color_count = 0


    if event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        break

window.close()