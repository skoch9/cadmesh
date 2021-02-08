import yaml
from yaml import CLoader
import numpy as np
import sys

def load_features(path):
    with open(path, "r") as fi:
        features = yaml.load(fi, Loader=CLoader)
    return features

def convert_features(features):
    tr_curves = features["curves"]
    trim_curves = features["trim"]

    for p_cnt, p in enumerate(features["topo"]):
        p["offsets"] = [[0.0, 0.0]]
        wires = sorted(list(set(p["wire_ids"])))
        c_id = 0
        for w in wires:
            #*p["wire_ids"].count(w)]
            # Check orientation of first curve in wire
            if p["wire_ids"].count(w) >= 2:
                cur = tr_curves[p["3dcurves"][c_id]]
                nxt = tr_curves[p["3dcurves"][c_id+1]]
                c_ori = p["orientations"][c_id]
                n_ori = p["orientations"][c_id+1]
                if c_ori == 0:
                    pole0 = np.array(cur["poles"][0])
                    pole1 = np.array(cur["poles"][-1])
                else: 
                    pole0 = np.array(cur["poles"][-1])
                    pole1 = np.array(cur["poles"][0])

                if n_ori == 0:
                    pole2 = np.array(nxt["poles"][0])
                    pole3 = np.array(nxt["poles"][-1])
                else: 
                    pole2 = np.array(nxt["poles"][-1])
                    pole3 = np.array(nxt["poles"][0])


                d02 = np.linalg.norm(pole0 - pole2)
                d12 = np.linalg.norm(pole1 - pole2)
                d03 = np.linalg.norm(pole0 - pole3)
                d13 = np.linalg.norm(pole1 - pole3)

                amin = np.argmin([d02, d12, d03, d13]) 

                if (amin == 0 or amin == 2) and not np.isclose(np.linalg.norm(pole0 - pole1), 0): # Orientation of first curve incorrect, fix
                    if np.min([d02, d12, d03, d13]) <= 1e-7:
                        #print("FIX ORIENT 0", p_cnt)
                        #print(d02, d12, d03, d13)
                        #print(pole0, pole1, pole2, pole3)
                        #print(amin, c_ori, n_ori, d02, d12, d03, d13)
                        p["orientations"][c_id] = abs(c_ori - 1)
                    else:
                        #print("NOT FIX 0", d02, d12, d03, d13)
                        pass

            # Fix all orientations in wire
            for i in range(c_id, c_id + p["wire_ids"].count(w) - 1):
                #print(i)
                cur = tr_curves[p["3dcurves"][i]]
                #print("P:", cur["poles"])
                nxt = tr_curves[p["3dcurves"][i+1]]
                c_ori = p["orientations"][i]
                n_ori = p["orientations"][i+1]
                if c_ori == 0:
                    pole1 = np.array(cur["poles"][-1])
                else: 
                    pole1 = np.array(cur["poles"][0])

                if n_ori == 0:
                    pole2 = np.array(nxt["poles"][0])
                    pole3 = np.array(nxt["poles"][-1])
                else: 
                    pole2 = np.array(nxt["poles"][-1])
                    pole3 = np.array(nxt["poles"][0])

                d12 = np.linalg.norm(pole1 - pole2)
                d13 = np.linalg.norm(pole1 - pole3)

                amin = np.argmin([d12, d13])
                #print(d12, d13, amin)
                #print("A", p_cnt, i, amin, c_ori, n_ori, d12, d13)

                if amin == 1: # Incorrect orientation, flip
                    if np.min([d12, d13]) <= 1e-7:
                        #print("FIX ORIENT %i"%i, p_cnt)

                        #print(pole1, pole2, pole3, c_ori, n_ori, d12, d13, amin)
                        p["orientations"][i+1] = abs(n_ori - 1)
                    else:
                        #print("NOT FIX %i"%i, d12, d13)
                        pass
                        
            last_offset = np.array([0.0, 0.0])
            for i in range(c_id, c_id + p["wire_ids"].count(w) - 1):
                cur = trim_curves[p["2dcurves"][i]]
                nxt = trim_curves[p["2dcurves"][i+1]]
                c_ori = p["orientations"][i]
                n_ori = p["orientations"][i+1]
                if c_ori == 0:
                    pole1 = np.array(cur["poles"][-1])
                else: 
                    pole1 = np.array(cur["poles"][0])

                if n_ori == 0:
                    pole2 = np.array(nxt["poles"][0])
                    pole3 = np.array(nxt["poles"][-1])
                else: 
                    pole2 = np.array(nxt["poles"][-1])
                    pole3 = np.array(nxt["poles"][0])

                d12 = np.linalg.norm(pole1 - pole2)
                d13 = np.linalg.norm(pole1 - pole3)

                amin = np.argmin([d12, d13])
                #print(d12, d13, amin)
                #print("A", p_cnt, i, amin, c_ori, n_ori, d12, d13)

                if amin == 1: # Incorrect orientation, flip
                    if np.min([d12, d13]) <= 1e-7:
                        print("FIX ORIENT2D %i"%i, p_cnt)

                        #print(pole1, pole2, pole3, c_ori, n_ori, d12, d13, amin)
                        p["orientations"][i+1] = abs(n_ori - 1)
                    else:
                        #print("NOT FIX2 %i"%i, d12, d13)                        
                        pass

                if np.min([d12, d13]) > 1e-7:                           
                    if i < c_id + p["wire_ids"].count(w) - 2: # Curves afterwards in wire
                        nnxt = trim_curves[p["2dcurves"][i+2]]
                        nn_ori = p["orientations"][i+2]
                    else:
                        nnxt = trim_curves[p["2dcurves"][c_id]] # No curves afterwards, go back to first
                        nn_ori = p["orientations"][c_id]

                    if nn_ori == 0:
                        pole4 = np.array(nnxt["poles"][0])
                    else: 
                        pole4 = np.array(nnxt["poles"][-1])

                    #print("Broken int curve", i, d12, d13, pole1+last_offset, pole2, pole3, pole4)

                    ds = []
                    ps = [] #orientations
                    ofs = []
                    p1 = pole1 + last_offset
                    for ox in [-2*np.pi, -np.pi, -1.0, 0.0, 1.0, np.pi, 2*np.pi]:
                        for oy in [-2*np.pi, -np.pi, -1.0, 0.0, 1.0, np.pi, 2*np.pi]:

                            p2 = np.array([pole2[0]+ox, pole2[1]+oy])
                            p3 = np.array([pole3[0]+ox, pole3[1]+oy])
                            if np.abs(ox) > 3.0: # case of +-2pi
                                p2[0] = np.abs(p2[0])
                                p3[0] = np.abs(p3[0])
                            if np.abs(oy) > 3.0:
                                p2[1] = np.abs(p2[1])
                                p3[1] = np.abs(p3[1])


                            ds.append(np.linalg.norm(p1 - p2) + np.linalg.norm(pole4 - p3))
                            ds.append(np.linalg.norm(p1 - p3) + np.linalg.norm(pole4 - p2))
                            #ps.append([p2, p3])
                            #ps.append([p3, p2])
                            ps.extend([0, 1])
                            ofs.append([ox, oy])#, ox2, oy2])
                            ofs.append([ox, oy])
                    #dmin = np.argmin(ds)
                    dss = np.argsort(ds)
                    #nxt["poles"][0] = ps[dmin][0].tolist()
                    #nxt["poles"][1] = ps[dmin][1].tolist()
                    #print(tr_curves[p["2dcurves"][c_id+1]])
                    #print(np.sort(ds), dss, ofs[dss[0]], ofs[dss[1]], ofs[dss[2]], ofs[dss[3]])#, ps[dss[0]], ps[dss[1]])
                    #if np.sort(ds)[0] > 1e-7:
                    #    print("Probably wrong offset chosen.")
                    #print(ps[dss[0]], ds[dss[0]], ps[dss[1]], ds[dss[1]])
                    if ps[dss[0]] == 0 and ds[dss[0]] < 1e-6:
                        p["offsets"].append(ofs[dss[0]])
                        last_offset = ofs[dss[0]]
                        #print("c0")
                    elif ps[dss[1]] == 0 and ds[dss[1]] < 1e-6:
                        p["offsets"].append(ofs[dss[1]])
                        last_offset = ofs[dss[1]]
                        #print("c1")
                    else:
                        print("Probably wrong offset chosen.")
                        p["offsets"].append(np.array([0.0, 0.0]))
                        last_offset = np.array([0.0, 0.0])
                    #print("OA")
                else:
                    p["offsets"].append(np.array([0.0, 0.0]))
                    last_offset = np.array([0.0, 0.0])
                    #print("OFFs")
                    #print("Wire", p["wire_ids"])
                    #print("OO")


            c_id += p["wire_ids"].count(w)
        if len(p["2dcurves"]) > len(p["offsets"]):
            #print(p["offsets"])
            #print("Missing Offset")
            p["offsets"].append([0.0, 0.0])
        #print(p["offsets"])
        
    # Apply offset transformations
    for si, s in enumerate(features["topo"]):
        #print(s["offsets"])
        for i in range(len(s["2dcurves"])):
            c2d = features["trim"][s["2dcurves"][i]]
            if c2d["type"] == "BSpline":
                if "offsets" in s and len(s["offsets"]) > i:
                    s["offsets"][i] = np.array(s["offsets"][i]).tolist()
                else:
                    #print("Zero Offset missing")
                    s["offsets"].append([0.0, 0.0])

    return features
        
if __name__ == "__main__":
    f = sys.argv[1]
    r = sys.argv[2]

    features = load_features(f)
    features = convert_features(features)
    with open(r, "w") as fi:
        yaml.dump(features, fi)
