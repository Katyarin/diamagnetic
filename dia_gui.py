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


def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth


'''def autoscale_y(axis,margin=0.1):
    """This function rescales the y-axis based on the data that is visible given the current xlim of the axis.
    ax -- a matplotlib axes object
    margin -- the fraction of the total height of the y-data to pad the upper and lower ylims"""

    def get_bottom_top(line):
        xd = list(line.get_xdata())
        yd = list(line.get_ydata())
        lo,hi = axis.get_xlim()
        #y_displayed = yd[((xd>lo) & (xd<hi))]
        mini = 0
        maxi = 0
        for i, el in enumerate(xd):
            if el >= lo:
                mini = i
            break
        for i, el in enumerate(xd):
            if el >= hi:
                maxi = i
            break
        print(mini, maxi)
        y_displayed = yd[mini:maxi]
        h = max(y_displayed) - min(y_displayed)
        bot = min(y_displayed)-margin*h
        top = max(y_displayed)+margin*h
        return bot,top

    lines = axis.get_lines()
    bot,top = np.inf, -np.inf

    for line in lines:
        new_bot, new_top = get_bottom_top(line)
        if new_bot < bot: bot = new_bot
        if new_top > top: top = new_top

    axis.set_ylim(bot,top)'''


plt.rcParams['axes.facecolor']='#E3F2FD'
plt.rcParams['figure.facecolor']='#E3F2FD'
px = 1/plt.rcParams['figure.dpi']
color_list = ['b', 'r', 'm', 'g', 'black']
color_list2 = ['cyan', 'orange', 'pink', 'olive', 'gray']
data_add = {'dimensions': {'Bt': 'T', 'beta_dia': '%', 'W_dia': 'J', 'li': '%',
                                            'dia_sig': 'mWb', 'Bv': 'T', 'Lp': 'nH', 'Psi_av': 'Wb', 'psiInd': 'Wb',
                                            'psiRes': 'Wb', 'beta_t': '%', 'beta_N': 'mm*T/A', 'Ipl': 'A', 'Rav': 'm', 'k': '%', 'tr_up': '%', 'tr_down': '%'}, 'error': None}

#PATH_for_save_PUB = '//172.16.12.127/Pub/!diamagnetic_data'
#PATH_for_save = 'c:/work/Data/diamagnetic_data/'
#PATH_for_save = 'c:/work/Data/diamagnetic_data/'
CFM_ADDR = 'http://172.16.12.150:8050/_dash-update-component'

with open('settings.json', 'r') as set_file:
    settings = json.load(set_file)

sg.theme('Material1')
list_of_checkbokes = [[sg.vtop(sg.Text('История', font=16))]]
for i in range(20):
    list_of_checkbokes.append([sg.vtop(sg.Checkbox('', key='%icheck' %i, font=16, visible=False, enable_events=True))])
layout = [  [sg.Text('Для расчета введите номер разряда и номер вычета', font=16)],
            [sg.Text('Разряд #', font=16), sg.Input(key='-SHOT-', font=16), sg.Text('Вычет #', font=16), sg.Input(key='-RECSHOT-', font=16)],
            [sg.Button('Ok', font=16), sg.Button('Append', font=16), sg.Button('Save', font=16), sg.Button('Read Me', font=16), sg.Button('Settings', font=16)],
            [sg.Text(key='-err_text-', font=16), sg.Button('ReCalc', font=16, visible=False)],
            [sg.Column([[sg.Canvas(key='-plot2-',expand_x=True, expand_y=True)], [sg.Slider(orientation='h', expand_x=True, key='-SL_min-'), sg.Slider(orientation='h', expand_x=True, key='-sl-max-', default_value=240)]], expand_x=True, expand_y=True),
             sg.vtop(sg.Column(list_of_checkbokes), expand_x=True, expand_y=True)],
            [sg.Text('Created by Tkachenko E.E.', text_color='gray', justification='right', expand_x=True)]]

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
        [sg.Canvas(key='-plot1-')], [sg.Button('OK', font=16), sg.Button('Cancel', font=16, button_color='red')]]

    window_check = sg.Window('Проверка соответствия разряда вычета требуемому разряду', layout, resizable=True, finalize=True)
    plot_left = draw_figure(window_check['-plot1-'].TKCanvas, checked_fig)
    checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
    make_canvas_interactive(plot_left)
    plot_left.draw()


    while True:
        event, values = window_check.read()
        if event == 'Cancel':
            window_check.close()
            return 0
        if event == sg.WIN_CLOSED or event=='OK':
            window_check.close()
            return 1
    #window_check.close()


fig, axs = plt.subplots(4, 3, sharex=True, figsize=((screen_size[0]*px, screen_size[1]*0.8*px)))
plot_right = draw_figure(window['-plot2-'].TKCanvas, fig)
make_canvas_interactive(plot_right)
color_count = 0

active_list = []
history_list = {}
history_ind = 0
def draw_data(data, shotn, color_count):
    if data['error'] == None:
        #axs[0, 0].plot(data['data']['time'], data['data']['data']['Bt'], label='Bt %i' %shotn, color=color_list[color_count])
        axs[0, 0].plot(data['data']['time'], data['data']['data']['Bv'], '-', label='Bv %i' %shotn, color=color_list[color_count])
        axs[1, 0].plot(data['data']['time'], data['data']['data']['beta_dia'], label=shotn, color=color_list[color_count])
        axs[2, 0].plot(data['data']['time'], [i/1000 for i in data['data']['data']['W_dia']], label=shotn, color=color_list[color_count])
        axs[3, 0].plot([i/1000 for i in data['shafr_int_meth']['time']], [i/1000 for i in data['shafr_int_meth']['W']], label=shotn, color=color_list[color_count])

        axs[0, 1].plot(data['data']['time'], data['data']['data']['li'], label=shotn, color=color_list[color_count])
        axs[1, 1].plot(data['data']['time'], data['data']['data']['Lp'], label=shotn, color=color_list[color_count])
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

        axs[0, 2].plot(data['data']['time'], data['data']['data']['k'], label=shotn, color=color_list[color_count])
        axs[1, 2].plot(data['data']['time'], data['data']['data']['tr_up'], label=r'$\delta_{up}$ %i' %shotn, color=color_list[color_count])
        axs[1, 2].plot(data['data']['time'], data['data']['data']['tr_down'], '--', label=r'$\delta_{down}$ %i' %shotn, color=color_list[color_count])
        axs[2, 2].plot(data['data']['time'], data['data']['data']['Psi_av'], '-', label=r'$\Psi_{av}$ %i' %shotn, color=color_list[color_count])
        axs[3, 2].plot(data['data']['time'], data['data']['data']['psiInd'], '-', label=r'$\Delta\Psi_{ind}$ %i' %shotn, color=color_list[color_count])
        axs[3, 2].plot(data['data']['time'], data['data']['data']['psiRes'], '--', label=r'$\Delta\Psi_{res}$ %i' %shotn, color=color_list[color_count])


        axs[0, 0].set_ylabel(r'$B, T$')
        #axs[0, 0].set_xlim(0.110, 0.3)
        #axs[0, 0].set_ylim(0, 1)
        axs[1, 0].set_ylabel(r'$\beta_{dia}$')
        #axs[1, 0].set_ylim(0, 0.6)
        axs[2, 0].set_ylabel(r'$W_{dia}, kJ$')
        axs[3, 0].set_ylabel(r'$W_{shafr}, kJ$')
        #axs[2, 0].set_ylim(0, 20)

        axs[0, 1].set_ylabel(r'$l_{i}$')
        #axs[3, 0].set_ylim(0, 2)
        axs[1, 1].set_ylabel(r'$L_{p}, nH$')
        axs[0, 2].set_ylabel(r'$\kappa$')
        axs[1, 2].set_ylabel(r'$\delta$')
        axs[2, 2].set_ylabel(r'$\Psi, Wb$')
        axs[3, 2].set_ylabel(r'$\Delta\Psi, Wb$')
        axs[2, 1].set_ylabel(r'$\beta_{T}, %$')
        axs[3, 1].set_ylabel(r'$\beta_{N}, mm \cdot T / A$')
        #axs[3, 0].set_ylim(0, 2)
        axs[3, 0].set_xlabel('time, s')
        axs[3, 1].set_xlabel('time, s')
        axs[3, 2].set_xlabel('time, s')

        count =0
        for ax in axs:
            for subax in ax:
                subax.legend()
                if count in [3, 4, 5, 9, 10, 11]:
                    #subax.yaxis.set_label_position("right")
                    subax.yaxis.tick_right()
                count+=1
        ax_list = []
        for ax in axs:
            ax_list.extend([subax for subax in ax])
        ax_tuple = tuple(ax_list)
        cursor = MultiCursor(fig.canvas, ax_tuple, color='r', lw=0.5, horizOn=False, vertOn=True)
        plot_right.draw()
        window['-SL_min-'].update(range=((min(data['data']['time'])*1e3), (max(data['data']['time']))*1e3))
        window['-sl-max-'].update(range=((min(data['data']['time'])*1e3), (max(data['data']['time']))*1e3))
        window['-sl-max-'].update(value=(max(data['data']['time'])*1e3))
        window['-SL_min-'].update(value=(min(data['data']['time'])*1e3))
        '''elif data['error'] == "MCC file does not exist":
        MCC_create(VAL)'''
    else:
        window['-err_text-'].update('ОШИБКА!!! %s' %data['error'], background_color='red', text_color='white', visible=True)


def data_open(values, ReCalc=False):
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
                    'error': data_add['error'], 'shafr_int_meth': data_new['shafr_int_meth']}
            rec = data_new['compensation']
            window['-err_text-'].update('Данные загружены из базы данных (вычет: %i), если хотите пересчитать, введите номер вычета и нажмите ReCalc' %rec, background_color='green', text_color='white', visible=True)
            window['ReCalc'].update(visible=True)
        except:
            try:
                rec = int(values['-RECSHOT-'])
            except:
                window['-err_text-'].update('ОШИБКА! Введите целочисленный номер вычета', background_color='red', text_color='white', visible=True)
                rec = 0
                return 0, 0, 0

            if rec * shotn:
                data = dia_sig.dia_data(shotn, rec, ch_ax)
                check = check_page()
                shotn = check*shotn
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
                draw_data(data, shotn, color_count)
            mcc_window.close()
        mcc_window['-no_mcc-'].update(serv_resp.json()['response']['children'])
        if event == sg.WIN_CLOSED:
            break
    mcc_window.close()


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
        window['-err_text-'].update(visible=False)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.088, bottom=0.093, right=0.95, top=0.96, wspace=0.126, hspace=0.157)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.06, right=0.95, top=0.983, wspace=0.212, hspace=0)
        data, shotn, rec = data_open(values)
        if int(shotn*rec):
            draw_data(data, shotn, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            window['%icheck' %history_ind].update(text='%i' %shotn, value=True, visible=True)
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
            draw_data(data, shotn, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            window['%icheck' % history_ind].update(text='%i' % shotn, value=True, visible=True)
            history_ind += 1

    if event == 'Save':
        PATH_for_save = settings['path_out']
        window['ReCalc'].update(visible=False)
        with open('%sjson/%i.json' %(PATH_for_save, shotn), 'w') as json_f:
            json.dump({'compensation': rec, 'time': data['data']['time'], 'data': data['data']['data'], 'shafr_int_meth': data['shafr_int_meth']}, json_f)
        data = data['data']
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
        window['-err_text-'].update('Файлы разряда %i сохранены в папку %s' %(shotn, PATH_for_save), background_color='green', text_color='white')
        window['-err_text-'].update(visible=True)

    if event == 'Read Me':
        deffinition()

    if event == 'Settings':
        set_page()

    if event == 'ReCalc':
        window['-err_text-'].update(visible=False)
        window['ReCalc'].update(visible=False)
        for ax in ch_ax:
            ax.cla()
        checked_fig.subplots_adjust(left=0.062, bottom=0.26, right=0.95, top=0.843, wspace=0.126, hspace=0)
        for ax in axs:
            for subax in ax:
                subax.clear()
                subax.grid()
        fig.subplots_adjust(left=0.05, bottom=0.06, right=0.95, top=0.983, wspace=0.212, hspace=0)
        data, shotn, rec = data_open(values, ReCalc=True)
        if int(shotn*rec):
            draw_data(data, shotn, color_count)
            history_list[shotn] = data
            active_list.append(shotn)
            window['%icheck' % history_ind].update(text='%i' % shotn, value=True, visible=True)
            history_ind += 1
        #color_count = 0

    if event == '-SL_min- Release' or event == '-sl-max- Release':
        axs[3,0].set_xlim((values['-SL_min-']/1e3), (values['-sl-max-']/1e3))
        '''for i in range(4):
            for j in range(3):
                axs[i,j].replot()'''
        min_dict = {}
        max_dict = {}
        for key in history_list[active_list[0]]['data']['data'].keys():
            for shot in active_list:
                min_loc = min([history_list[shot]['data']['data'][key][i] for i, t in enumerate(history_list[shot]['data']['time']) if values['-sl-max-']/1e3 > t > values['-SL_min-']/1e3])
                max_loc = max([history_list[shot]['data']['data'][key][i] for i, t in enumerate(history_list[shot]['data']['time']) if values['-sl-max-']/1e3 > t > values['-SL_min-']/1e3])
                if key not in min_dict or min_dict[key] > min_loc:
                    min_dict[key] = min_loc*0.9
                if key not in max_dict or max_dict[key] < max_loc:
                    max_dict[key] = max_loc*1.1
        for shot in active_list:
            min_loc = min([history_list[shot]['shafr_int_meth']['W'][i] for i, t in enumerate(history_list[shot]['shafr_int_meth']['time']) if values['-sl-max-'] > t > values['-SL_min-']])*0.9
            max_loc = max([history_list[shot]['shafr_int_meth']['W'][i] for i, t in enumerate(history_list[shot]['shafr_int_meth']['time']) if values['-sl-max-'] > t > values['-SL_min-']])*1.1
            if 'shafr_int_meth' not in min_dict or min_dict['shafr_int_meth'] > min_loc:
                min_dict['shafr_int_meth'] = min_loc
            if 'shafr_int_meth' not in max_dict or max_dict['shafr_int_meth'] < max_loc:
                max_dict['shafr_int_meth'] = max_loc

        axs[0, 0].set_ylim(min_dict['Bv'], max_dict['Bv'])
        axs[1, 0].set_ylim(min_dict['beta_dia'], max_dict['beta_dia'])
        axs[2, 0].set_ylim(min_dict['W_dia']/1000, max_dict['W_dia']/1000)
        axs[3, 0].set_ylim(min_dict['shafr_int_meth']/1000, max_dict['shafr_int_meth']/1000)

        axs[0, 1].set_ylim(min_dict['li'], max_dict['li'])
        axs[1, 1].set_ylim(min_dict['Lp'], max_dict['Lp'])
        axs[2, 1].set_ylim(min_dict['beta_t'], max_dict['beta_t'])
        axs[3, 1].set_ylim(min_dict['beta_N'], max_dict['beta_N'])

        axs[0, 2].set_ylim(min_dict['k'], max_dict['k'])
        axs[1, 2].set_ylim((min_dict['tr_down']*int(min_dict['tr_down']<min_dict['tr_up']) + min_dict['tr_up']*int(min_dict['tr_down']>min_dict['tr_up'])),
                           (max_dict['tr_down']*int(max_dict['tr_down']>max_dict['tr_up']) + max_dict['tr_up']*int(max_dict['tr_down']<max_dict['tr_up'])))
        axs[2, 2].set_ylim(min_dict['Psi_av'], max_dict['Psi_av'])
        axs[3, 2].set_ylim((min_dict['psiRes']*int(min_dict['psiRes']<min_dict['psiInd']) + min_dict['psiInd']*int(min_dict['psiRes']>min_dict['psiInd'])),
                           (max_dict['psiRes']*int(max_dict['psiRes']>max_dict['psiInd']) + max_dict['psiInd']*int(max_dict['psiRes']<max_dict['psiInd'])))
    plot_right.draw()

    for i in range(20):
        if event == '%icheck' %i:
            if window['%icheck' %i].get():
                shotn = int(window['%icheck' %i].Text)
                active_list.append(shotn)
                data = history_list[shotn]
                color_count+=1
                draw_data(data, shotn, color_count)
            else:
                shotn = window['%icheck' %i].Text
                active_list.remove(int(shotn))
                for ax in axs:
                    for subax in ax:
                        subax.cla()
                        subax.grid()
                fig.subplots_adjust(left=0.05, bottom=0.06, right=0.95, top=0.983, wspace=0.212, hspace=0)
                if active_list:
                    color_count = 0
                    for shot in active_list:
                        data = history_list[shot]
                        draw_data(data, shot, color_count)
                else:
                    plot_right.draw()





    if event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        break

window.close()