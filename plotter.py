import uuid
from statistics import mean
from typing import List, Tuple

import matplotlib.pyplot as plt

number_of_observations = 15


def violin_plot(data: List, pos: List[int], title: str, y_label: str, x_label: str):
    interval = len(data) // number_of_observations
    _interval = [interval for _ in range(number_of_observations)]
    data = list(map(lambda x: data[x[1] * x[0]], enumerate(_interval)))
    pos = list(map(lambda x: pos[x[1] * x[0]], enumerate(_interval)))

    fig, ax = plt.subplots()

    ax.violinplot(data, pos, points=20, widths=0.9, showmeans=True, showextrema=True, showmedians=True)
    ax.set(xlabel=x_label, ylabel=y_label, title=title)
    avg = [mean(x) for x in data]
    ax.plot(pos, avg, label='Mean', linestyle='--')
    fig.show()
    fig.savefig('simulations/' + uuid.uuid4().hex + ".png", dpi=(250), bbox_inches='tight')


def grouped_bar_plot(data, pos, title: str, y_label: str, x_label: str, legend: Tuple = None):
    interval = len(data[0]) // number_of_observations
    _interval = [interval for _ in range(number_of_observations)]
    for idx, d in enumerate(data):
        data[idx] = list(map(lambda x: d[x[0] * x[1]], enumerate(_interval)))

    pos = list(map(lambda x: pos[x[0] * x[1]], enumerate(_interval)))

    fig, ax = plt.subplots()
    width = 0.4

    bars = []

    for idx, bn in enumerate(data):
        if idx == 0:
            b = ax.bar(pos, bn, width)
        else:
            b = ax.bar(list(map(lambda x: x + (width * idx), pos)), bn, width)
        bars.append(b)

    ax.set_title(title)
    ax.set_xticks(tuple(map(lambda x: (x + (width * x)) - (x + (width * x)) / 8, pos)))
    ax.set_xticklabels(tuple(pos))
    ax.set(xlabel=x_label, ylabel=y_label, title=title)
    if legend: ax.legend(tuple(bars), legend)
    ax.autoscale_view()

    fig.show()
    fig.savefig('simulations/' + uuid.uuid4().hex + ".png", dpi=(250), bbox_inches='tight')
