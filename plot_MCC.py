import json
import matplotlib.pyplot as plt

shot = 46036
time = 180

plt.figure(figsize=(10, 10))
plt.xlim(0, 100)
plt.ylim(-50, 50)

f = '//172.16.12.127/Pub/!!!CURRENT_COIL_METHOD/V3_zad7_mcc/mcc_%d.json' % shot
try:
    with open(f, 'r') as file:
        data_mcc = json.load(file)
except FileNotFoundError:
    print("MCC file does not exist")

for i, t in enumerate(data_mcc['time']['variable']):
    if abs(t-time/1e3) < 1e-4:
        print(t)
        plt.plot(data_mcc['boundary']['rbdy']['variable'][i], data_mcc['boundary']['zbdy']['variable'][i], label=t)

        print('вытянутость', data_mcc['kx']['variable'][i])
        print('верхняя треугольность', data_mcc['deu']['variable'][i])
        print('нижняя треугольность', data_mcc['ded']['variable'][i])

plt.show()