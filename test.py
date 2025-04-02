import matplotlib.pyplot as plt
import numpy as np

from matplotlib.widgets import CheckButtons, Button
nButtons = 20
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k',
          'tab:orange', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive',
          '#00FF00', '#B8860B', '#4B0082', '#1E90FF', '#FF1493', '#008B8B']
print(len(colors))
t = np.arange(0.0, 2.0, 0.01)
s0 = np.sin(2*np.pi*t)
s1 = np.sin(4*np.pi*t)
s2 = np.sin(6*np.pi*t)

def signal(i, k):
    return np.sin(i*np.pi*t)*k

lines = {}

fig, ax = plt.subplots(1, 3, width_ratios=[3, 3, 1], figsize=(10, 5))
'''l0, = ax.plot(t, s0, visible=False, lw=2, color=colors[0], label='1 Hz')
l1, = ax.plot(t, s1, lw=2, color=colors[1], label='2 Hz')
l2, = ax.plot(t, s2, lw=2, color=colors[2], label='3 Hz')

l = ax2.plot(t, s0, visible=False, lw=2, color=colors[0], label='1 Hz')
print(l)
l01 = l[0]
l11, = ax2.plot(t, s1, lw=2, color=colors[1], label='2 Hz')
l21, = ax2.plot(t, s2, lw=2, color=colors[2], label='3 Hz')'''
for axis in range(len(ax)-1):
    lines[axis] = []
    for i in range(3):
        l, = ax[axis].plot(t, signal(i, 1), lw=2, color=colors[i], label=i)
        lines[axis].append(l)

axNew = fig.add_axes([0.7, 0.05, 0.1, 0.075])
button = Button(axNew, 'New')

#lines_by_label = {'ax1': {l.get_label(): l for l in [l0, l1, l2]},
                  #'ax2': {l.get_label(): l for l in [l01, l11, l21]}}
#line_colors = [l.get_color() for l in lines_by_label['ax1'].values()]

#nlines = len(lines[0])
legAx = ax[2]
label_list = [i for i in range(len(colors))]
activeColors = [c if i < len(lines[0]) else 'w' for i, c in enumerate(colors)]
# Make checkbuttons with all plotted lines with correct visibility
#rax = ax.inset_axes([0.0, 0.0, 0.12, 0.2])
rax = legAx
check = CheckButtons(
    ax=rax,
    labels=label_list,
    actives=[l.get_visible() for l in lines[0]] + [False]*20,
    label_props={'color': activeColors},
    frame_props={'edgecolor': activeColors},
    check_props={'facecolor': activeColors})

'''def new_button(event):
    l, = ax.plot(t, s1*50, lw=2, color='magenta', label='2 Hz big amp')
    l2, = ax2.plot(t, s1*50, lw=2, color='magenta', label='2 Hz big amp')
    lines_by_label['ax1'][l.get_label()] = l
    lines_by_label['ax2'][l2.get_label()] = l2
    line_colors.append(l.get_color())
    print(check.get_status())
    check.labels.append(l.get_label())
    check.set_active(3, state=True)
    check.label_props={'color': line_colors}
    #check.actives.append(l.get_visible())
    check.frame_props = {'edgecolor': line_colors}
    check.check_props = {'facecolor': line_colors}
    print(check.get_status())
    plt.draw()
    #return check'''

def callback(label):
    for axis in range(len(ax)-1):
        ln = lines[axis][label_list.index(int(label))]
        ln.set_visible(not ln.get_visible())
        #ln.figure.canvas.draw_idle()
    plt.draw()

def newButton(event):

    currInd = len(lines[1])
    currLab = len(lines[1])
    print(check.labels[currInd])
    check.labels[currInd].set(text=currLab)
    print(check.labels[currInd])
    activeColors[len(lines[1])] = colors[len(lines[1])]
    for axis in range(len(ax) - 1):
        l, = ax[axis].plot(t, signal(currLab, 1), lw=2, color=colors[currInd], label=currLab)
        #l.set_visible(True)
        lines[axis].append(l)
    #plt.draw()
    label_list[currInd] = currLab

    check.set_label_props({'color': activeColors})
    check.set_frame_props({'edgecolor': activeColors})
    check.set_check_props({'facecolor': activeColors})
    check.set_active(currInd, False)
    check.set_active(currInd, True)
    plt.draw()


print(check)
def callback(label):
    for axis in range(len(ax)-1):
        ln = lines[axis][label_list.index(int(label))]
        ln.set_visible(not ln.get_visible())
        #ln.figure.canvas.draw_idle()
    plt.draw()

check.on_clicked(callback)
button.on_clicked(newButton)

plt.show()