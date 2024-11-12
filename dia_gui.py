import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import dia_sig
import json
import numpy as np
import shtRipper
import os
import requests
from matplotlib.widgets import MultiCursor
import numpy as np

version = 5.0


def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth


sg.set_options(font=16)
plt.rcParams['axes.facecolor']='#E3F2FD'
plt.rcParams['figure.facecolor']='#E3F2FD'
px = 1/plt.rcParams['figure.dpi']
color_list = ['b', 'r', 'm', 'g', 'black']
color_list2 = ['cyan', 'orange', 'pink', 'olive', 'gray']
data_add = {'dimensions': {'Bt': 'T', 'beta_dia': '%', 'W_dia': 'J', 'li': '%',
                                            'dia_sig': 'mWb', 'Bv': 'T', 'Lp': 'nH', 'Psi_av': 'Wb', 'psiInd': 'Wb',
                                            'psiRes': 'Wb', 'beta_t': '%', 'beta_N': 'mm*T/A', 'Ipl': 'A', 'Rav': 'm', 'k': '%', 'tr_up': '%', 'tr_down': '%', 'Vp': 'm-3'}, 'error': None}

#PATH_for_save_PUB = '//172.16.12.127/Pub/!diamagnetic_data'
#PATH_for_save = 'c:/work/Data/diamagnetic_data/'
#PATH_for_save = 'c:/work/Data/diamagnetic_data/'
CFM_ADDR = 'http://172.16.12.150:8050/_dash-update-component'

with open('settings.json', 'r') as set_file:
    settings = json.load(set_file)

indexPath = settings['TS_path']

with open('%sindex.json' % indexPath, 'r') as indFile:
    index = json.load(indFile)

maxIndexShot = max([int(i) for i in list(index.keys())])
sg.theme('Material1')
list_of_checkbokes = [[sg.Text('История', font=16), sg.Button('Reset', font=16)]]
#list_of_checkbokes2 = [[sg.vtop(sg.Text('История', font=16))]]
for i in range(20):
    list_of_checkbokes.append([sg.vtop(sg.Checkbox('', key='%icheck' %i, font=16, visible=False, enable_events=True))])
    #list_of_checkbokes2.append([sg.vtop(sg.Checkbox('', key='%icheck2' %i, font=16, visible=False, enable_events=True))])
sl_min = sg.Slider(orientation='h', expand_x=True, key='-SL_min-')
sl_max = sg.Slider(orientation='h', expand_x=True, key='-sl-max-', default_value=240)
#sl_min2 = sg.Slider(orientation='h', expand_x=True, key='-SL_min2-')
#sl_max2 = sg.Slider(orientation='h', expand_x=True, key='-sl-max2-', default_value=240)
tab01 = [[sg.Canvas(key='-plot2-',expand_x=True, expand_y=True)]]
tab02 = [[sg.Canvas(key='-plot3-',expand_x=True, expand_y=True)]]
tab1 = [[sg.Column(tab01, expand_x=True, expand_y=True),
             sg.vtop(sg.Column(list_of_checkbokes), expand_x=True, expand_y=True)]]
#tab2 = [tab02]
#tab2=[[sg.Text('Для расчета введите номер разряда и номер вычета', font=16)]]

'''layout = [[sg.Text('Для расчета введите номер разряда и номер вычета', font=16)],
          [sg.Text('Разряд #', font=16), sg.Input(key='-SHOT-', font=16), sg.Text('Вычет #', font=16), sg.Input(key='-RECSHOT-', font=16)],
          [sg.Button('Ok', font=16), sg.Button('TS', font=16), sg.Button('Append', font=16), sg.Button('Save', font=16), sg.Button('Read Me', font=16), sg.Button('Settings', font=16)],
          [sg.Text(key='-err_text-', font=16), sg.Button('ReCalc', font=16, visible=False)],
          [sg.TabGroup([
              [sg.Tab('Basic Info', tab01), sg.Tab('Contact Details', tab01)]])],
          [sg.Text('Created by Tkachenko E.E.', text_color='gray', justification='right', expand_x=True)]
          ]
'''
layout = [[sg.Text('Для расчета введите номер разряда и номер вычета', font=16)],
          [sg.Text('Разряд #', font=16), sg.Input(key='-SHOT-', font=16), sg.Text('Вычет #', font=16), sg.Input(key='-RECSHOT-', font=16)],
          [sg.Button('Ok', font=16), sg.Button('TS', font=16), sg.Button('Append', font=16), sg.Button('Save', font=16), sg.Button('Read Me', font=16), sg.Button('Settings', font=16),
          sg.Text(key='-err_text-', font=16), sg.Button('ReCalc', auto_size_button=True, visible=False), sg.Button('Find', auto_size_button=True, visible=False), sg.Button('Stop', auto_size_button=True, visible=False)],
          [sg.TabGroup([
              [sg.Tab('Основные', tab1), sg.Tab('Метод токовых колец', tab02)]], expand_x=True, expand_y=True)],
          [sl_min, sl_max],
          [sg.Text('Created by Tkachenko E.E.', text_color='gray', justification='right', expand_x=True)]

]
window = sg.Window('Расчет данных по диамагнитному сигналу v%.1f' %version, layout, resizable=True, finalize=True)

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

def move_center(window):
    screen_width, screen_height = window.get_screen_dimensions()
    win_width, win_height = window.size
    x, y = (screen_width - win_width)//2, (screen_height - win_height)//2
    window.move(x, y)

def deffinition():
    '''layout = [[sg.Text('Описание кнопок', font=('TimesNewRoman', 20,'bold underline'))],
                       [sg.vtop(sg.Text('Ok \n \n TS \n \n Append \n \n Save \n \n Settings \n \n ReCalc  ', font=('TimesNewRoman', 16,'bold'), justification='right')),
                        (sg.Text('вывести данные разряда на экран. Можно не вводить номер вычета, если файл есть в базе данных, то программа загрузит разряд из базы \n'
                       '\n \n загрузить данные диагностики томсоновского рассеяния  \n'
                       '\n добавить на графики данные введенного разряда \n'
                                '\n сохранить данные в txt, json и sht файлы. Директория по умолчанию: Pub/!!diamagnetic_data/ \n'
                                '\n Настройки путей для чтения sht-данных и сохранения расчетов программы. \n Пути сейчас:  \n Папка с SHT-файлами: %s \n Папка с новыми SHT-файлами: %s \n Сохранить в  %s \n'
                                '\n пересчитать разряд заново (необходимо ввести номер разряда-вычета' %(settings['path_in'], settings['path_in_new'], settings['path_out']), font=16, expand_x=True))],
              [sg.Text('Формулы', font=('TimesNewRoman', 20,'underline bold'))],
              [sg.Canvas(key='-def-')],
              [sg.Button('Close')]]'''
    layout = [[sg.Text('Описание кнопок', font=('TimesNewRoman', 20, 'bold underline'))],
              [sg.Text('Ok', font=('TimesNewRoman', 16,'bold'), justification='right', size=10), sg.Text('вывести данные разряда на экран. Можно не вводить номер вычета, если файл есть в базе данных, то программа загрузит разряд из базы', font=16, expand_x=True)],
              [sg.Text('TS', font=('TimesNewRoman', 16,'bold'), justification='right', size=10), sg.Text('загрузить данные диагностики томсоновского рассеяния', font=16, expand_x=True)],
              [sg.Text('Append', font=('TimesNewRoman', 16,'bold'), justification='right', size=10), sg.Text('добавить на графики данные введенного разряда', font=16, expand_x=True)],
              [sg.Text('Save', font=('TimesNewRoman', 16,'bold'), justification='right', size=10), sg.Text('сохранить данные в txt, json и sht файлы. Директория по умолчанию: Pub/!!diamagnetic_data/', font=16, expand_x=True)],
              [sg.Text('Settings', font=('TimesNewRoman', 16,'bold'), justification='right', size=10), sg.Text('Настройки путей для чтения sht-данных и сохранения расчетов программы. \nПути сейчас:  \n     Папка с SHT-файлами: %s \n     Папка с новыми SHT-файлами: %s \n     Сохранить в  %s \n     Папка с данными диагностики ТР: %s'  %(settings['path_in'], settings['path_in_new'], settings['path_out'], settings['TS_path']), font=16, expand_x=True)],
              [sg.Text('ReCalc', font=('TimesNewRoman', 16,'bold'), justification='right', size=10), sg.Text('пересчитать разряд заново (необходимо ввести номер разряда-вычета)', font=16, expand_x=True)],
              [sg.Text('Формулы', font=('TimesNewRoman', 20, 'underline bold'))],
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
    axDef.text(0.2, 0.225, r'$\beta_{T} = \frac{4\mu_0 \cdot W_{dia}}{3\cdot B_{T}^2 \cdot V}$', fontsize=16)
    axDef.text(0.2, 0.15, r'$\beta_{N} = \frac{100\cdot a \cdot B_T \cdot \beta_T}{I_p}$', fontsize=16)
    axDef.text(0.2, 0.1, r'где $I_{tf}$ - ток в катушках тороидального магнитного поля,', fontsize=10)
    axDef.text(0.2, 0.075, r'$R_{av}$ - радиус центра тяжести токовых колец,', fontsize=10)
    axDef.text(0.2, 0.05, r'$I_p$ - ток плазмы, $\kappa$ - вытянутость, ', fontsize=10)
    axDef.text(0.2, 0.025, r'$\mu_0 = 4 \pi \cdot 10^{-7}$, $a$ - малый радиус плазмы', fontsize=10)
    axDef.get_xaxis().set_visible(False)
    axDef.get_yaxis().set_visible(False)
    '''axDef.patch.set_alpha(0.9)'''
    figDef.subplots_adjust(left=-0.1, bottom=-0.005, right=1.005, top=1.005, wspace=0, hspace=0)
    window2 = sg.Window('Read Me', layout, finalize=True, resizable=True, auto_save_location=True)
    draw_figure(window2['-def-'].TKCanvas, figDef)


    #window2.location = (main_window_x, main_window_y)
    #window.refresh()
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
              [sg.Button('Save', key='-shtNewFolder-'), sg.Text('Путь сохранен', key='-shtNewTxt-', visible=False)],

              [sg.Text('Select folder for reading TS data:')],
              [sg.Input(enable_events=True, key='-TS_IN-', font=('Arial Bold', 12), expand_x=True),
               sg.FolderBrowse(initial_folder=settings['TS_path'], key='br_TS')],
              [sg.Button('Save', key='-TSFolder-'), sg.Text('Путь сохранен', key='-TSTxt-', visible=False)]
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
        if event == '-TSFolder-':
            settings['TS_path'] = str(values['-TS_IN-'])
            with open('settings.json', 'w') as set_new_file:
                json.dump(settings, set_new_file, indent=2)
            set_window['-TSTxt-'].update(visible=True)
        if event == sg.WIN_CLOSED:
            break
    set_window.close()


checked_fig, ch_ax = plt.subplots(2, 1, sharex=True, figsize=(10, 6))


def check_page():
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


fig, axs = plt.subplots(4, 3, sharex=True, figsize=((14, 7)))
plot_right = draw_figure(window['-plot2-'].TKCanvas, fig)
make_canvas_interactive(plot_right)

fig3, axs3 = plt.subplots(4, 3, sharex=True, figsize=((14, 7)))
plot3 = draw_figure(window['-plot3-'].TKCanvas, fig3)
make_canvas_interactive(plot3)
color_count = 0
TS_plot = 1
legs = [0 ,0]
legs[0] = fig.legend([], [], loc='outside lower center', ncol=20)
legs[1] = fig3.legend([], [], loc='outside right upper')

active_list = []
history_list = {}
history_ind = 0



def resize_fig(values):
    min_dict = {}
    max_dict = {}
    for key in history_list[active_list[0]]['data']['data'].keys():
        for shot in active_list:
            if history_list[shot]['data']['data'][key]:
                min_loc = min(
                    [history_list[shot]['data']['data'][key][i] for i, t in enumerate(history_list[shot]['data']['time']) if
                     values['-sl-max-'] / 1e3 > t > values['-SL_min-'] / 1e3])
                max_loc = max(
                    [history_list[shot]['data']['data'][key][i] for i, t in enumerate(history_list[shot]['data']['time']) if
                     values['-sl-max-'] / 1e3 > t > values['-SL_min-'] / 1e3])
                if key not in min_dict or abs(min_dict[key]) > abs(min_loc):
                    if min_loc > 0:
                        min_dict[key] = min_loc * 0.9
                    else:
                        min_dict[key] = min_loc * 1.1
                if key not in max_dict or abs(max_dict[key]) < abs(max_loc):
                    if max_loc > 0:
                        max_dict[key] = max_loc * 1.1
                    else:
                        max_dict[key] = max_loc * 0.9
    for shot in active_list:
        min_loc = min([history_list[shot]['shafr_int_meth']['W'][i] for i, t in
                       enumerate(history_list[shot]['shafr_int_meth']['time']) if
                       values['-sl-max-']/ 1e3 > t > values['-SL_min-']/ 1e3]) * 0.9
        max_loc = max([history_list[shot]['shafr_int_meth']['W'][i] for i, t in
                       enumerate(history_list[shot]['shafr_int_meth']['time']) if
                       values['-sl-max-']/ 1e3 > t > values['-SL_min-']/ 1e3]) * 1.1
        if 'shafr_int_meth' not in min_dict or min_dict['shafr_int_meth'] > min_loc:
            min_dict['shafr_int_meth'] = min_loc
        if 'shafr_int_meth' not in max_dict or max_dict['shafr_int_meth'] < max_loc:
            max_dict['shafr_int_meth'] = max_loc

    axs3[1, 1].set_ylim(min_dict['Bv'], max_dict['Bv'])
    axs[0, 0].set_ylim(min_dict['beta_dia'], max_dict['beta_dia'])
    #print(max_dict['shafr_int_meth'])
    axs[2, 0].set_ylim(0, max_dict['shafr_int_meth']/1e3)
    axs[1, 0].set_ylim(min_dict['W_dia']/1e3, max_dict['W_dia']/1e3)
    #axs[3, 0].set_ylim(0, max_dict['shafr_int_meth']/1e3)
    #axs[3, 0].set_ylim(min_dict['shafr_int_meth'] / 1000, max_dict['shafr_int_meth'] / 1000)

    axs[1, 1].set_ylim(min_dict['li'], max_dict['li'])
    axs3[0, 0].set_ylim(min_dict['Vp'], max_dict['Vp'])
    axs[2, 1].set_ylim(min_dict['beta_t'], max_dict['beta_t'])
    axs[3, 1].set_ylim(min_dict['beta_N'], max_dict['beta_N'])

    #axs[0, 2].set_ylim(min_dict['k'], max_dict['k'])
    axs[1, 2].set_ylim(min_dict['dEFC']*0.9, max_dict['dEFC'])
    axs3[3, 0].set_ylim((min_dict['tr_down'] * int(min_dict['tr_down'] < min_dict['tr_up']) + min_dict['tr_up'] * int(
        min_dict['tr_down'] > min_dict['tr_up'])),
                       (max_dict['tr_down'] * int(max_dict['tr_down'] > max_dict['tr_up']) + max_dict['tr_up'] * int(
                           max_dict['tr_down'] < max_dict['tr_up'])))
    axs[2, 2].set_ylim(min_dict['Psi_av'], max_dict['Psi_av'])
    axs[3, 2].set_ylim((min_dict['psiRes'] * int(min_dict['psiRes'] < min_dict['psiInd']) + min_dict['psiInd'] * int(
        min_dict['psiRes'] > min_dict['psiInd'])),
                       (max_dict['psiRes'] * int(max_dict['psiRes'] > max_dict['psiInd']) + max_dict['psiInd'] * int(
                           max_dict['psiRes'] < max_dict['psiInd'])))

    axs3[1, 0].set_ylim(min_dict['Sp'], max_dict['Sp'])
    axs3[0, 1].set_ylim(min_dict['Bt'], max_dict['Bt'])
    axs3[2, 1].set_ylim(min_dict['Rav'], max_dict['Rav'])
    axs3[3, 1].set_ylim(min_dict['Zc'], max_dict['Zc'])
    axs3[0, 2].set_ylim(min_dict['Zav'], max_dict['Zav'])
    axs3[1, 2].set_ylim(min_dict['a'], max_dict['a'])
    axs3[2, 2].set_ylim(min_dict['Rx'], max_dict['Rx'])
    axs3[3, 2].set_ylim(min_dict['Zx'], max_dict['Zx'])

def av_ne(shotn, data):
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
        data_TS_dyn[' T_max']['data'] = data_TS_dyn[' T_max_measured']['data']
        data_TS_dyn[' T_max']['dimensions'] = data_TS_dyn[' T_max_measured']['dimensions']
        history_list[shotn]['TS_data'] = {'time': [i/1000 for i in data_TS_dyn[' time']['data']], '<n>V': data_TS_dyn[' <n>V']['data'],
                           '<n>V_err': data_TS_dyn[' <n>V_err']['data'], '<n>42': data_TS_dyn[' <n>42']['data'], '<n>42_err': data_TS_dyn[' <n>42_err']['data'],
                                          'We': [i/1000 for i in data_TS_dyn[' We']['data']], 'T_max': data_TS_dyn[' T_max']['data'], 'T_max_err':  data_TS_dyn[' T_max_err']['data']}
        data['TS_data'] = history_list[shotn]['TS_data']
        data['TS_data']['dimensions'] = {}
        for key in data['TS_data'].keys():
            if key != 'time' and key != 'dimensions':
                data['TS_data']['dimensions'][key] = data_TS_dyn[' ' + key]['dimensions']

    except Exception as error:
        TS_plot = 1
        print('TS_err is:', error)
        window['-err_text-'].update('ВНИМАНИЕ!!! Нет файла с данными ТР. Попробуйте позже или обратитесь к группе ТР', background_color='orange', text_color='white',
                                    visible=True)

    return data


def draw_data(data, shotn, rec, color_count):
    try:
        if data['error'] == None:
            #axs[0, 0].plot(data['data']['time'], data['data']['data']['Bt'], label='Bt %i' %shotn, color=color_list[color_count])
            axs3[1, 1].plot(data['data']['time'], data['data']['data']['Bv'], '-', label='Bv %i' %shotn, color=color_list[color_count])
            axs[0, 0].plot(data['data']['time'], data['data']['data']['beta_dia'], label=shotn, color=color_list[color_count])
            axs[1, 0].plot(data['data']['time'], [i/1000 for i in data['data']['data']['W_dia']], label=r'$W_{dia} $ %i' %shotn, color=color_list[color_count])
            axs[2, 0].plot(data['shafr_int_meth']['time'], [i/1000 for i in data['shafr_int_meth']['W']], '-', label=r'$W_{shafr} $ %i' %shotn, color=color_list[color_count])

            axs[1, 1].plot(data['data']['time'], data['data']['data']['li'], label=shotn, color=color_list[color_count])

            try:
                axs[0, 1].errorbar(data['TS_data']['time'], data['TS_data']['<n>V'],
                                   yerr=data['TS_data']['<n>V_err'], label=r'$<n>_V$',
                                   color=color_list[color_count])
                axs[0, 1].errorbar(data['TS_data']['time'], data['TS_data']['<n>42'],
                                   yerr=data['TS_data']['<n>42_err'], fmt='.', label=r'$<n>^{42}_l$',
                                   color=color_list[color_count])
                axs[0, 2].errorbar(data['TS_data']['time'], data['TS_data']['T_max'],
                                   yerr=data['TS_data']['T_max_err'], fmt='.', label=r'$T_{center}$ %i' % shotn,
                                   color=color_list[color_count])
                axs[3, 0].plot(data['TS_data']['time'], data['TS_data']['We'], label=r'$W_e$ %i' % shotn,
                                   color=color_list[color_count])
                if color_count == 0:
                    axs[0, 1].legend(loc='lower center')
                '''axs[0, 2].legend()
                axs[3, 0].legend()'''
            except Exception as error:
                print(error)
                '''axs[0, 1].cla()
                axs[0, 2].cla()
                axs[3, 0].cla()
                axs[0, 1].grid()
                axs[0, 2].grid()
                axs[3, 0].grid()'''
                print('No TS data')

            axs3[0, 0].plot(data['data']['time'], data['data']['data']['Vp'], label=shotn, color=color_list[color_count])

            axs[2, 1].plot(data['data']['time'], data['data']['data']['beta_t'], label=shotn, color=color_list[color_count])
            axs[3, 1].plot(data['data']['time'], data['data']['data']['beta_N'], label=shotn, color=color_list[color_count])

            #axs[0, 2].plot(data['data']['time'], data['data']['data']['k'], label=shotn, color=color_list[color_count])
            axs3[2, 0].plot(data['data']['time'], data['data']['data']['k'], label=shotn, color=color_list[color_count])

            axs3[3, 0].plot(data['data']['time'], data['data']['data']['tr_up'], label=r'$\delta_{up}$', color=color_list[color_count])
            axs3[3, 0].plot(data['data']['time'], data['data']['data']['tr_down'], '--', label=r'$\delta_{down}$', color=color_list[color_count])

            axs[1, 2].plot(data['data']['time'], data['data']['data']['dEFC'], label=r'$EFC_S - EFC_N $ %i' %shotn, color=color_list[color_count])
            axs[2, 2].plot(data['data']['time'], data['data']['data']['Psi_av'], '-', label=r'$\Psi_{av}$ %i' %shotn, color=color_list[color_count])
            axs[3, 2].plot(data['data']['time'], data['data']['data']['psiInd'], '-', label=r'$\Delta\Psi_{ind}$', color=color_list[color_count])
            axs[3, 2].plot(data['data']['time'], data['data']['data']['psiRes'], '--', label=r'$\Delta\Psi_{res}$', color=color_list[color_count])

            axs3[1, 0].plot(data['data']['time'], data['data']['data']['Sp'], label=r'$S_p$ %i' % shotn, color=color_list[color_count])
            axs3[1, 0].set_ylabel(r'$S_p, m^2$')

            axs3[0, 1].plot(data['data']['time'], data['data']['data']['Bt'], label=r'$B_T$ %i' % shotn, color=color_list[color_count])
            axs3[0, 1].set_ylabel(r'$B, T$')
            axs3[2, 1].plot(data['data']['time'], data['data']['data']['Rav'], label=r'$R_{av}$ %i' % shotn, color=color_list[color_count])
            axs3[2, 1].set_ylabel(r'$R_{av}, m$')
            axs3[3, 1].plot(data['data']['time'], data['data']['data']['Zc'], label=r'$Z_{central}$ %i' % shotn, color=color_list[color_count])
            axs3[3, 1].set_ylabel(r'$Z_{central}, cm$')

            axs3[0, 2].plot(data['data']['time'], data['data']['data']['Zav'], label=r'$Zav$ %i' % shotn, color=color_list[color_count])
            axs3[0, 2].set_ylabel(r'$Z_{av}, cm$')
            axs3[1, 2].plot(data['data']['time'], data['data']['data']['a'], label=r'$a$ %i' % shotn, color=color_list[color_count])
            axs3[1, 2].set_ylabel(r'$a$, m')
            axs3[2, 2].plot(data['data']['time'], data['data']['data']['Rx'], '.', label=r'$R_{x}$ %i' % shotn, color=color_list[color_count])
            axs3[2, 2].set_ylabel(r'$R_{x}, cm$')
            axs3[3, 2].plot(data['data']['time'], data['data']['data']['Zx'], '.', label=r'$Z_{x}$ %i' % shotn, color=color_list[color_count])
            axs3[3, 2].set_ylabel(r'$Z_{x}, cm$')


            axs3[1, 1].set_ylabel(r'$B, T$')
            #axs[0, 0].set_xlim(0.110, 0.3)
            #axs[0, 0].set_ylim(0, 1)
            axs[0, 0].set_ylabel(r'$\beta_{dia}$')
            #axs[1, 0].set_ylim(0, 0.6)
            axs[1, 0].set_ylabel(r'$W, kJ$')
            axs[2, 0].set_ylabel(r'$W, kJ$')
            axs[3, 0].set_ylabel(r'$W_e, kJ$')
            axs[1, 1].set_ylabel(r'$l_{i}$')
            #axs[2, 0].set_ylim(0, 20)

            axs[0, 1].set_ylabel(r'$<n_{e}>, m^{-3}$')
            #axs[3, 0].set_ylim(0, 2)
            axs3[0, 0].set_ylabel(r'$V_{p}, m^{3}$')
            axs[0, 2].set_ylabel(r'$T_{e}^{center}$, eV')
            axs3[2, 0].set_ylabel(r'$\kappa$')
            axs3[3, 0].set_ylabel(r'$\delta$')
            axs[1, 2].set_ylabel(r'$EFC_S - EFC_N$')
            axs[2, 2].set_ylabel(r'$\Psi, Wb$')
            axs[3, 2].set_ylabel(r'$\Delta\Psi, Wb$')
            axs[2, 1].set_ylabel(r'$\beta_{T}$')
            axs[3, 1].set_ylabel(r'$\beta_{N}, mm \cdot T / A$')
            #axs[3, 0].set_ylim(0, 2)
            axs[3, 0].set_xlabel('time, s')
            axs[3, 1].set_xlabel('time, s')
            axs[3, 2].set_xlabel('time, s')

            axs3[3, 0].set_xlabel('time, s')
            axs3[3, 1].set_xlabel('time, s')
            axs3[3, 2].set_xlabel('time, s')

            if color_count == 0:
                axs[3,2].legend()
                axs3[3,0].legend()

            count =0
            for ax in axs:
                for subax in ax:
                    #subax.legend(loc='upper left')
                    if count in [3, 4, 5, 9, 10, 11]:
                        #subax.yaxis.set_label_position("right")
                        subax.yaxis.tick_right()
                    count+=1

            count = 0
            for ax in axs3:
                for subax in ax:
                    #subax.legend(loc='upper left')
                    if count in [3, 4, 5, 9, 10, 11]:
                        #subax.yaxis.set_label_position("right")
                        subax.yaxis.tick_right()
                    count+=1
            ax_list = []
            lines, labels = axs[0,0].get_legend_handles_labels()
            legs[0].remove()
            legs[1].remove()
            legs[0] = fig.legend(lines, labels, loc='outside lower center', ncol=20)
            legs[1] = fig3.legend(lines, labels, loc='outside right upper')
            for ax in axs:
                ax_list.extend([subax for subax in ax])
            ax_tuple = tuple(ax_list)
            #cursor = MultiCursor(fig.canvas, ax_tuple, color='r', lw=0.5, horizOn=False, vertOn=True)
            plot_right.draw()
            plot3.draw()
            window['-SL_min-'].update(range=((min(data['data']['time'])*1e3), (max(data['data']['time']))*1e3))
            window['-sl-max-'].update(range=((min(data['data']['time'])*1e3), (max(data['data']['time']))*1e3))
            window['-sl-max-'].update(value=(max(data['data']['time'])*1e3))
            window['-SL_min-'].update(value=(min(data['data']['time'])*1e3))
            '''elif data['error'] == "MCC file does not exist":
            MCC_create(VAL)'''

        else:
            window['-err_text-'].update('ОШИБКА!!! %s' %data['error'], background_color='red', text_color='white', visible=True)

    except Exception as exep:
        print(exep)
        window['-err_text-'].update('ОШИБКА!!! Введите номер вычета %i и нажмите ReCalc ' %rec, background_color='red', text_color='white',
                                    visible=True)
        window['ReCalc'].update(visible=True)
        window['Find'].update(visible=True)


def data_open(values, ReCalc=False):
    window['-err_text-'].update('Чтение файлов...', background_color='blue',
                                text_color='white',
                                visible=True)
    window.refresh()
    try:
        shotn = int(values['-SHOT-'])
    except:
        window['-err_text-'].update('ОШИБКА! Введите целочисленный номер разряда', background_color='red', text_color='white', visible=True)
        shotn = 0
    if ReCalc:
        try:
            rec = int(values['-RECSHOT-'])
        except:
            window['-err_text-'].update('ОШИБКА! Введите целочисленный номер вычета', background_color='red', text_color='white', visible=True)
            window['Find'].update(visible=True)
            rec = 0

        if rec * shotn:
            data = dia_sig.dia_data(shotn, rec, ch_ax)
            window['-err_text-'].update(visible=False)
            check_page()
            history_list[shotn] = data
        else:
            return 0, 0, 0
    else:
        try:
            PATH_for_save = settings['path_out']
            with open('%sjson/%i.json' % (PATH_for_save, shotn), 'r') as json_f:
                data_new = json.load(json_f)
            data = {'data': {}}
            '''data = {'data': {'time': data_new['time'], 'data': data_new['data'], 'dimensions': data_add['dimensions']},
                    'error': data_add['error'], 'shafr_int_meth': data_new['shafr_int_meth'], 'TS_data': data_new['TS_data']}'''
            for key in data_new.keys():
                if key == 'time' or key == 'data' or key == 'dimensions':
                    data['data'][key] = data_new[key]
                elif key!='compensation':
                    data[key] = data_new[key]
            if 'dimensions' not in list(data['data'].keys()):
                data['data']['dimensions'] = data_add['dimensions']
            if 'error' not in list(data['data'].keys()):
                data['error'] = data_add['error']
            if 'dimensions' not in list(data['shafr_int_meth'].keys()):
                data['shafr_int_meth']['dimensions'] = {'W': 'J'}
            rec = data_new['compensation']
            if 'shafr_int_meth' in list(data.keys()):
                if max(data['shafr_int_meth']['time']) > 10:
                    data['shafr_int_meth']['time'] = [i/1e3 for i in data['shafr_int_meth']['time']]
            window['-err_text-'].update('Данные загружены из базы данных (вычет: %i), если хотите пересчитать, введите номер вычета и нажмите ReCalc' %rec, background_color='green', text_color='white', visible=True)
            window['ReCalc'].update(visible=True)
            history_list[shotn] = data
        except Exception as exep:
            print(exep)
            try:
                rec = int(values['-RECSHOT-'])
            except:
                window['-err_text-'].update('ОШИБКА! Введите целочисленный номер вычета', background_color='red', text_color='white', visible=True)
                window['Find'].update(visible=True)
                rec = 0
                return 0, 0, 0

            if rec * shotn:
                data = dia_sig.dia_data(shotn, rec, ch_ax)
                window['-err_text-'].update(visible=False)
                check = check_page()
                shotn = check*shotn
                history_list[shotn] = data
    if data:
        if 'TS_data' not in list(data.keys()):
            data = av_ne(shotn, data)
    return data, shotn, rec


def MCC_create(VAL):
    layout = [[sg.Text('MCC data calculation...')],
              [sg.Cancel(), sg.Text(key='-no_mcc-')]]
    mcc_window = sg.Window('MCC data calculation...', layout=layout)
    while True:
        event, values = mcc_window.read()
        serv_resp = requests.post(CFM_ADDR, json={
            'changedPropIds': ["btn-2.n_clicks"],
            'inputs': [
                {
                    'id': "btn-2",
                    'property': "n_clicks",
                    'value': 1
                }
            ],
            'output': "my-output1.children",
            'outputs': {
                'id': "my-output1",
                'property': "children"
            },
            'state': [
                {
                    'id': "shot_number_input",
                    'property': "value",
                    'value': int(VAL['-SHOT-'])}
            ]
        })

        if serv_resp.json()['response']['my-output1']['children'].startswith(' Good! '):
            data, shotn, rec = data_open(VAL)
            if int(shotn * rec):
                draw_data(data, shotn, rec, color_count)
            mcc_window.close()
        mcc_window['-no_mcc-'].update(serv_resp.json()['response']['children'])
        if event == sg.WIN_CLOSED:
            break
    mcc_window.close()


def FindZeroDiscarge(shotn_need):
    if shotn_need > maxIndexShot:
        window['-err_text-'].update('К сожалению, этот номер разряда еще не внесён в базу данных по поиску разрядов-вычетов. Обратитесь, пожалуйста, к Ткаченко Екатерине.',
                                    background_color='red', text_color='white',
                                    visible=True)
        return 0, 0, 0
    for delta in range(2, 500):
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
        if delta % 2:
            shotn = shotn_need + delta // 2
        else:
            shotn = shotn_need - delta // 2
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
            return 0, 0, 0
        if 'err' in list(index[str(shotn)].keys()):
            #print(shotn, index[str(shotn)]['err'])
            if 'has suspicious file size' in index[str(shotn)]['err']:
                continue
            # time.sleep(1)
            data = dia_sig.dia_data(shotn_need, shotn, ch_ax, pf2=False)
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
                    checkRes = check_page()
                    #print(checkRes)
                    if checkRes==1:
                        #history_list[shotn] = data
                        if data:
                            if 'TS_data' not in list(data.keys()):
                                data = av_ne(shotn, data)
                                #print(data.keys())
                        return data, shotn_need, shotn
                    elif checkRes==-1:
                        return 0, 0, 0


data = {}
shotn = 0
rec = 0
window.Maximize()
window['-SL_min-'].bind('<ButtonRelease-1>', ' Release')
window['-sl-max-'].bind('<ButtonRelease-1>', ' Release')

while True:
    event, values = window.read()
    if event == 'Ok':
        color_count = 0
        active_list = []
        for i in range(20):
            window['%icheck' %i].update(False)
           # window['%icheck2' %i].update(False)
        window['-err_text-'].update(visible=False)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        for ax in axs3:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.09, right=0.95, top=0.983, wspace=0.212, hspace=0)
        fig3.subplots_adjust(left=0.05, bottom=0.06, right=0.910, top=0.983, wspace=0.212, hspace=0)
        data, shotn, rec = data_open(values)
        if int(shotn*rec):
            draw_data(data, shotn, rec, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            window['%icheck' %history_ind].update(text='%i' %shotn, value=True, visible=True)
            #window['-err_text-'].update(visible=False)
            #window['ReCalc'].update(visible=False)
            #window['%icheck2' %history_ind].update(text='%i' %shotn, value=True, visible=True)
            history_ind += 1

    if event == 'Append':
        color_count += 1
        if color_count == len(color_list):
            color_count = 0
        window['-err_text-'].update(visible=False)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
        data, shotn, rec = data_open(values)
        if int(shotn * rec):
            draw_data(data, shotn, rec, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            window['%icheck' % history_ind].update(text='%i' % shotn, value=True, visible=True)
            #window['-err_text-'].update(visible=False)
            #window['%icheck2' % history_ind].update(text='%i' % shotn, value=True, visible=True)
            history_ind += 1

    if event == 'Save':
        try:
            PATH_for_save = settings['path_out']
            window['ReCalc'].update(visible=False)
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
            with open('%sjson/%i.json' %(PATH_for_save, shotn), 'w') as json_f:
                json.dump(for_dump, json_f)
            to_pack = {}
            #print('yes1')
            for key in data.keys():
                #print(key, type(data[key]))
                if key != 'data' and key !='TS_data' and key != 'dimensions' and type(data[key])==dict:
                    for key2 in data[key].keys():
                        if key2 != 'time' and key2 != 'dimensions':
                            to_pack[key + '_' + key2] = {
                                'comment': 'data from %s' %key,
                                'unit': '%s(%s)' % (key2, data[key]['dimensions'][key2]),
                                'tMin': min(data[key]['time']),  # mininun time
                                'tMax': max(data[key]['time']),  # maximum time
                                'offset': 0.0,  # ADC zero level offset
                                'yRes': 0.0001,  # ADC resolution: 0.0001 Volt per adc bit
                                'y': data[key][key2]
                            }
                    #print('yes1.1')
                elif key =='TS_data':
                    for key2 in data[key].keys():
                        #print(key2)
                        if 'err' not in key2 and key2 != 'time' and key2 != 'dimensions' and key2 != 'We':
                            to_pack[key2] = {
                                'comment': 'data from %s' %key,
                                'unit': '%s(%s)' % (key2, data[key]['dimensions'][key2]),
                                'x': data[key]['time'],
                                'y': data[key][key2],
                                'err': data[key][key2 + '_err']
                            }
                        if key2 == 'We':
                            to_pack[key2] = {
                                'comment': 'data from %s' %key,
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
                        if data['data'][key]:
                            txt_f.write('%12.4f' % data['data'][key][i])
                        else:
                            txt_f.write('%12s' % 'None')
                    txt_f.write('\n')
            for key in data['data'].keys():
                to_pack[key] = {
                    'comment': '',
                    'unit': '%s(%s)' %(key, data['dimensions'][key]),
                    'tMin': min(data['time']),  # mininun time
                    'tMax': max(data['time']),  # maximum time
                    'offset': 0.0,  # ADC zero level offset
                    'yRes': 0.0001,  # ADC resolution: 0.0001 Volt per adc bit
                    'y': data['data'][key]
                }
            print('yes3')
            packed = shtRipper.ripper.write(path=(PATH_for_save + 'sht/'), filename='%i.SHT' %shotn, data=to_pack)
            if len(packed) != 0:
                print('packed error = "%s"' % packed)
            window['-err_text-'].update('Файлы разряда %i сохранены в папку %s' %(shotn, PATH_for_save), background_color='green', text_color='white')
            window['-err_text-'].update(visible=True)
        except Exception as exep:
            print(exep)
            window['-err_text-'].update('Не удалось сохранить файлы. Пожалуйста, пересчитайте разряд и попробуйте снова (вычет: %i)' % (rec),
                                        background_color='red', text_color='white')
            window['-err_text-'].update(visible=True)
            window['ReCalc'].update(visible=True)

    if event == 'Read Me':
        deffinition()

    if event == 'Settings':
        set_page()

    if event == 'ReCalc':
        window['-err_text-'].update(visible=False)
        window['ReCalc'].update(visible=False)
        history_list[shotn] = {}
        active_list.remove(shotn)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.062, bottom=0.26, right=0.95, top=0.843, wspace=0.126, hspace=0)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        for ax in axs3:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.09, right=0.95, top=0.983, wspace=0.212, hspace=0)
        fig3.subplots_adjust(left=0.05, bottom=0.06, right=0.91, top=0.983, wspace=0.212, hspace=0)
        data, shotn, rec = data_open(values, ReCalc=True)
        if int(shotn*rec):
            TS_plot = 0
            draw_data(data, shotn, rec, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            history_ind-=1
            window['%icheck' % history_ind].update(text='%i' % shotn, value=True, visible=True)
           # window['%icheck2' % history_ind].update(text='%i' % shotn, value=True, visible=True)
            history_ind += 1
        #color_count = 0

    if event == 'Find':
        #window['-err_text-'].update(visible=False)
        window['-err_text-'].update(
            'Выполняется поиск...',
            background_color='blue', text_color='white')
        window['Find'].update(visible=False)
        window['Stop'].update(visible=True)
        #window.read()
        #history_list[shotn] = {}
        #active_list.remove(shotn)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.062, bottom=0.26, right=0.95, top=0.843, wspace=0.126, hspace=0)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        for ax in axs3:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.09, right=0.95, top=0.983, wspace=0.212, hspace=0)
        fig3.subplots_adjust(left=0.05, bottom=0.06, right=0.91, top=0.983, wspace=0.212, hspace=0)
        data, shotn, rec = FindZeroDiscarge(int(values['-SHOT-']))
        window['Stop'].update(visible=False)
        if int(shotn*rec):
            print(shotn, rec)
            #window['Find'].update(visible=False)
            #window['-err_text-'].update(visible=False)
            draw_data(data, shotn, rec, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            window['%icheck' %history_ind].update(text='%i' %shotn, value=True, visible=True)
            #window['%icheck2' %history_ind].update(text='%i' %shotn, value=True, visible=True)
            history_ind += 1


    if event == '-SL_min- Release' or event == '-sl-max- Release':
        axs[3,0].set_xlim((values['-SL_min-']/1e3), (values['-sl-max-']/1e3))
        axs3[3,0].set_xlim((values['-SL_min-']/1e3), (values['-sl-max-']/1e3))
        '''for i in range(4):
            for j in range(3):
                axs[i,j].replot()'''
        resize_fig(values)
    plot_right.draw()
    plot3.draw()

    for i in range(20):
        if event == '%icheck' %i:
            if window['%icheck' %i].get():
                #window['%icheck2' % i].update(True)
                shotn = int(window['%icheck' %i].Text)
                active_list.append(shotn)
                data = history_list[shotn]
                color_count+=1
                TS_plot = 1
                draw_data(data, shotn, 0, color_count)
                resize_fig(values)
            else:
                #window['%icheck2' % i].update(False)
                shotn = window['%icheck' %i].Text
                active_list.remove(int(shotn))
                for ax in axs:
                    for subax in ax:
                        subax.cla()
                        subax.grid()
                for ax in axs3:
                    for subax in ax:
                        subax.cla()
                        subax.grid()
                fig.subplots_adjust(left=0.05, bottom=0.09, right=0.95, top=0.983, wspace=0.212, hspace=0)
                fig3.subplots_adjust(left=0.05, bottom=0.06, right=0.91, top=0.983, wspace=0.212, hspace=0)
                if active_list:
                    color_count = 0
                    for shot in active_list:
                        data = history_list[shot]
                        draw_data(data, shot, 0, color_count)
                else:
                    color_count = 0
                    plot_right.draw()
                    plot3.draw()


    if event == 'TS':
        print('buut yes')
        try:
            shotn = int(values['-SHOT-'])
        except:
            window['-err_text-'].update('ОШИБКА! Введите целочисленный номер разряда', background_color='red',
                                        text_color='white', visible=True)
            shotn = 0
        data = av_ne(shotn, data)
        axs[0, 1].errorbar(history_list[shotn]['TS_data']['time'], history_list[shotn]['TS_data']['<n>V'],
                           yerr=history_list[shotn]['TS_data']['<n>V_err'], label=r'$<n>_V$',
                           color=color_list[color_count])
        axs[0, 1].errorbar(history_list[shotn]['TS_data']['time'], history_list[shotn]['TS_data']['<n>42'],
                           yerr=history_list[shotn]['TS_data']['<n>42_err'], fmt='.', label=r'$<n>^{42}_l$',
                           color=color_list[color_count])
        axs[0, 2].errorbar(history_list[shotn]['TS_data']['time'], history_list[shotn]['TS_data']['T_max'],
                           yerr=history_list[shotn]['TS_data']['T_max_err'], fmt='.', label=r'$T_{center}$ %i' % shotn,
                           color=color_list[color_count])
        axs[3, 0].plot(history_list[shotn]['TS_data']['time'], history_list[shotn]['TS_data']['We'], label=r'$W_e$ %i' % shotn,
                       color=color_list[color_count])
        axs[0, 1].legend()
        axs[0, 2].legend()
        axs[3, 0].legend()

    if event == 'Reset':
        active_list = []
        history_list = {}
        history_ind = 0
        color_count = 0
        for i in range(20):
            window['%icheck' %i].update(False, visible=False)
        window['-err_text-'].update(visible=False)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        for ax in axs3:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.09, right=0.95, top=0.983, wspace=0.212, hspace=0)
        fig3.subplots_adjust(left=0.05, bottom=0.06, right=0.91, top=0.983, wspace=0.212, hspace=0)
        plot_right.draw()
        plot3.draw()

    if event == sg.WIN_CLOSED:
        break

window.close()