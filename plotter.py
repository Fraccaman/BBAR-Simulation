import uuid
from statistics import mean
from typing import List, Tuple
import pkg_resources
pkg_resources.require("matplotlib==3.1.0")

import matplotlib.pyplot as plt
import numpy as np

number_of_observations = 20


def violin_plot(data: List, pos: List[int], title: str, y_label: str, x_label: str):
    if number_of_observations < len(data):
        assert(len(data) == len(pos))
        total_n_of_observations = len(data) # number_of_observations
        tmp = [total_n_of_observations // number_of_observations for _ in range(number_of_observations)]
        data = list(map(lambda x: data[x[1] * x[0]], enumerate(tmp)))
        pos = list(map(lambda x: pos[x[1] * x[0]], enumerate(tmp)))

    fig, ax = plt.subplots()

    ax.violinplot(data, pos, points=20, widths=4, showextrema=True, showmedians=True)
    ax.set(xlabel=x_label, ylabel=y_label, title=title)
    avg = [mean(x) for x in data]
    ax.plot(pos, avg, label='Mean', linestyle='--')
    fig.show()
    fig.savefig('simulations/' + uuid.uuid4().hex + ".png", dpi=(250), bbox_inches='tight')


def grouped_bar_plot(data, pos, title: str, y_label: str, x_label: str, legend: Tuple = None):
    number_of_observations = 10
    if number_of_observations < len(data[0]):
        assert(len(data[0]) == len(pos))
        interval = len(data[0]) // number_of_observations
        _interval = [interval for _ in range(number_of_observations)]
        for idx, d in enumerate(data):
            data[idx] = list(map(lambda x: d[x[0] * x[1]], enumerate(_interval)))
        pos = list(map(lambda x: pos[x[0] * x[1]], enumerate(_interval)))

    fig, ax = plt.subplots()
    width = 2

    bars = []

    for idx, bn in enumerate(data):
        if idx == 0:
            b = ax.bar(pos, bn, width)
        else:
            b = ax.bar(list(map(lambda x: x + (width * idx), pos)), bn, width)
        bars.append(b)

    ax.set_title(title)
    ax.set_xticks(tuple(map(lambda x: (x + (width * x)) - (x + (width * x)) / 2.5, pos)))
    ax.set_xticklabels(tuple(pos))
    ax.set(xlabel=x_label, ylabel=y_label, title=title)
    if legend: ax.legend(tuple(bars), legend)
    ax.autoscale_view()

    fig.show()
    fig.savefig('simulations/' + uuid.uuid4().hex + ".png", dpi=(250), bbox_inches='tight')


def stacked_bar_plot(data, series_labels, category_labels=None,
                show_values=False, value_format="{}", y_label=None,
                grid=False, reverse=False):
    """Plots a stacked bar chart with the data and labels provided.

    Keyword arguments:
    data            -- 2-dimensional numpy array or nested list
                       containing data for each series in rows
    series_labels   -- list of series labels (these appear in
                       the legend)
    category_labels -- list of category labels (these appear
                       on the x-axis)
    show_values     -- If True then numeric value labels will
                       be shown on each bar
    value_format    -- Format string for numeric value labels
                       (default is "{}")
    y_label         -- Label for y-axis (str)
    grid            -- If True display grid
    reverse         -- If True reverse the order that the
                       series are displayed (left-to-right
                       or right-to-left)
    """

    if number_of_observations < len(data[0]):
        assert(len(data[0]) == len(category_labels))
        total_n_of_observations = len(data[0]) # number_of_observations
        tmp = [total_n_of_observations // number_of_observations for _ in range(number_of_observations)]
        data[0] = list(map(lambda x: data[0][x[1] * x[0]], enumerate(tmp)))
        data[1] = list(map(lambda x: data[1][x[1] * x[0]], enumerate(tmp)))
        data[2] = list(map(lambda x: data[2][x[1] * x[0]], enumerate(tmp)))
        category_labels = list(map(lambda x: category_labels[x[1] * x[0]], enumerate(tmp)))

    ny = len(data[0])
    ind = list(range(ny))

    axes = []
    cum_size = np.zeros(ny)

    data = np.array(data)

    if reverse:
        data = np.flip(data, axis=1)
        category_labels = reversed(category_labels)

    for i, row_data in enumerate(data):
        axes.append(plt.bar(ind, row_data, bottom=cum_size,
                            label=series_labels[i]))
        cum_size += row_data

    if category_labels:
        plt.xticks(ind, category_labels)

    if y_label:
        plt.ylabel(y_label)

    plt.legend()
    # axes.set_ylim([0, 1])

    if grid:
        plt.grid()

    if show_values:
        for axis in axes:
            for bar in axis:
                w, h = bar.get_width(), bar.get_height()
                plt.text(bar.get_x() + w/2, bar.get_y() + h/2,
                         value_format.format(h), ha="center",
                         va="center")

    plt.show()
    plt.savefig('simulations/' + uuid.uuid4().hex + ".png", dpi=(250), bbox_inches='tight')


def heat_map(data, label_one, label_two):
    data = list(reversed(data))
    fig, ax = plt.subplots()
    im = ax.imshow(data)

    ax.set_xticks(np.arange(len(label_one)))
    ax.set_yticks(np.arange(len(label_two)))

    ax.set_xticklabels(label_one)
    ax.set_yticklabels(reversed(label_two))

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    for i in range(len(label_one)):
        for j in range(len(label_two)):
            text = ax.text(j, i, data[i][j], ha="center", va="center", color="w")

    ax.set_title("Number of peers in common between bootstrap nodes")
    fig.tight_layout()
    plt.colorbar(im)
    plt.show()

    fig.savefig('simulations/' + uuid.uuid4().hex + ".png", dpi=(250), bbox_inches='tight')

