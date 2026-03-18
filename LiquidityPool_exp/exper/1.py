import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot([1, 2, 3, 4], [1, 4, 2, 3])

empty = Rectangle((0, 0), 0, 0, alpha=0)

handles = [
    empty,
    Line2D([0], [0], color='black', linewidth=2),
    empty,
    Line2D([0], [0], color='red', marker='o', linestyle=''),
    Line2D([0], [0], color='gray', linewidth=1),
    Line2D([0], [0], color='blue', marker='s', linestyle=''),
]

labels = [
    'Group A',
    '  Item 1',
    'Group B',
    '  Item 3',
    '  Item 2',
    '  Item 4'
]

leg = ax.legend(handles=handles, labels=labels,
                ncol=2,
                handlelength=1.5,
                handletextpad=0.5)

# Hide group title handles
leg.legend_handles[0].set_visible(False)
leg.legend_handles[2].set_visible(False)

plt.show()