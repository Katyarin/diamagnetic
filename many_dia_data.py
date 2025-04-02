import dia_sig
import matplotlib.pyplot as plt
import json

with open('settings.json', 'r') as set_file:
    settings = json.load(set_file)
old_path = 'Z:/!diamagnetic_data/json_old3/'

shotn_list = [i for i in range(40021, 45800)]
#shotn_list = [i for i in range(45528, 45548)]

history_list = {}

for shot in shotn_list:
    print(shot)
    try:
        with open('%s%i.json' %(old_path,shot), 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        continue
    print('yes data')
    rec = data['compensation']

    shot_data = dia_sig.dia_data(shot, rec, ax=False)
    history_list[shot] = {}
    shot_data, history_list, err = dia_sig.av_ne(shot, shot_data, settings, history_list)

    resOfSave = dia_sig.Save_files(settings, shot_data, shot, rec)
    if resOfSave:
        print('Data not save')
        print(resOfSave)
    else:
        print('Data was saved')
