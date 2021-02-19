from yaml import CLoader
import yaml
import glob
from tqdm.auto import tqdm
from cadmesh import tqdm_joblib
from joblib import Parallel, delayed
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np


def parse_geometry_file_for_types(path):
    curve_types = []
    surf_types = []
    try:
        with open(path, "r") as fi:
            parts = yaml.load(fi, Loader=CLoader)

        if type(parts) == dict:
            for p in parts["parts"]:
                for c3d in p["3dcurves"]:
                    curve_types.append(c3d["type"])
                for s3d in p["surfaces"]:
                    surf_types.append(s3d["type"])
    except:
        pass
    
    return path, curve_types, surf_types
    

def process_files_parallel(path, function, jobs=12):
    files = glob.glob(path)   

    with tqdm_joblib(tqdm(desc="Processing geometry files", total=len(files))) as progress_bar:
        results = Parallel(n_jobs=jobs)(delayed(function)(gf) for gf in files)
    
    return results



def plot_types(typemap, title="Type percentages"):
    typemap = dict(sorted(typemap.items(), key=lambda item: item[1], reverse=True))
    labels = list(typemap.keys())
    values = np.array(list(map(lambda x: int(x), list(typemap.values()))))
    values = (values / np.sum(values) * 10000.0).astype(np.int)/100.0

    x = np.arange(len(labels))  # the label locations
    width = 0.5  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 7))
    rects1 = ax.bar(x, values, width)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Percentage')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}%'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    plt.show()



def analyse_curve_and_surface_types(path):
    results = process_files_parallel(path, parse_geometry_file_for_types)
    line_types = ["Line", "Circle", "Ellipse", "Hyperbola", "Parabola", "Bezier", "BSpline", "Offset", "Other"]
    surf_types = ["Plane", "Cylinder", "Cone", "Sphere", "Torus", "Bezier", "BSpline", "Revolution", "Extrusion", "Offset", "Other"]

    g_lines = Counter()    
    g_surfs = Counter()
    rev_ext = []
    for r in results[:]:
        nr = r[0].split("/")[3].split("_")[0]
        #lines = Counter(r[1])
        #surfs = Counter(r[2])
        g_lines.update(r[1])
        g_surfs.update(r[2])
        if surfs["Revolution"] > 0 or surfs["Extrusion"] > 0:
            rev_ext.append(nr)
            
    plot_types(g_lines, title="Curve types")
    plot_types(g_surfs, title="Surface types")
    
    return g_lines, g_surfs, rev_ext