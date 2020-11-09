import matplotlib.pyplot as plt
import lcpymake.base
from pathlib import Path
import networkx as nx


def draw(g: lcpymake.base.Graph, outfile: Path):
    plt.subplot(1, 1, 1)
    nx.draw(g.graph, with_labels=True)
    plt.savefig(str(outfile))
