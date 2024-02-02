import dia_sig
import matplotlib.pyplot as plt

checked_fig, ch_ax = plt.subplots(1,2, sharex=True, figsize=(14,2))
data = dia_sig.dia_data(43128, 43097, ch_ax)
