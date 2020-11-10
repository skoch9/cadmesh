from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface, BRepAdaptor_CompCurve, BRepAdaptor_Curve2d
from OCC.Core.gp import *
from OCC.Core.BRepTools import *
from OCC.Core.BRep import *
from OCC.Core.TopoDS import *
import sys
import os
import numpy as np
import json
import glob
import fileinput
import random
import yaml
import igl
import copy
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.TColStd import TColStd_Array1OfReal, TColStd_Array2OfReal
from OCC.Core.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt, TColgp_Array1OfPnt2d
from OCC.Core.BRepGProp import (brepgprop_SurfaceProperties,
                                brepgprop_VolumeProperties)
from OCC.Core.Geom2dAdaptor import Geom2dAdaptor_Curve
from OCC.Core.GeomConvert import geomconvert_CurveToBSplineCurve, geomconvert_SurfaceToBSplineSurface
from OCCUtils.edge import Edge
from OCCUtils.Topology import Topo
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert

from OCC.Core.GeomConvert import geomconvert_SurfaceToBSplineSurface
from OCC.Core.GeomConvert import geomconvert_CurveToBSplineCurve
from OCC.Core.Geom2dConvert import geom2dconvert_CurveToBSplineCurve
from OCC.Core.TopLoc import TopLoc_Location
from convert import convert_features

np.set_printoptions(precision=17)

def read_step_file(filename, return_as_shapes=False, verbosity=False):
    assert os.path.isfile(filename)
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(filename)
    if status == IFSelect_RetDone:  # check status
        if verbosity:
            failsonly = False
            step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
            step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
        shapes = []
        nr = 1
        try:
            while True:
                ok = step_reader.TransferRoot(nr)
                if not ok:
                    break
                _nbs = step_reader.NbShapes()
                shapes.append(step_reader.Shape(nr))  # a compound
                #assert not shape_to_return.IsNull()
                nr += 1
        except:
            print("No Shape", nr)
    else:
        raise AssertionError("Error: can't read file.")

    return shapes


def get_boundingbox(shape, tol=1e-6, use_mesh=True):
    bbox = Bnd_Box()
    bbox.SetGap(tol)
    if use_mesh:
        mesh = BRepMesh_IncrementalMesh()
        mesh.SetParallel(True)
        mesh.SetShape(shape)
        mesh.Perform()
        assert mesh.IsDone()
    brepbndlib_Add(shape, bbox, use_mesh)

    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return [xmin, ymin, zmin, xmax, ymax, zmax, xmax-xmin, ymax-ymin, zmax-zmin]

edge_map = {0: "Line", 1: "Circle", 2: "Ellipse", 3: "Hyperbola", 4: "Parabola", 5: "Bezier", 6: "BSpline", 7: "Offset", 8: "Other"}
surf_map = {0: "Plane", 1: "Cylinder", 2: "Cone", 3: "Sphere", 4: "Torus", 5: "Bezier", 6: "BSpline", 7: "Revolution", 8: "Extrusion", 9: "Offset", 10: "Other"}
gmsh_map = {"Surface of Revolution": "Revolution", "Surface of Extrusion": "Extrusion", "Plane": "Plane", "Cylinder": "Cylinder",\
           "Cone": "Cone", "Torus": "Torus", "Sphere": "Sphere", "Bezier surface": "Bezier", "BSpline surface": "BSpline", "Unknown": "Other"}


def convert_curve(curve):
    d1_feat = {"type": edge_map[curve.GetType()]}
    c_type = d1_feat["type"]
    if c_type == "Line":
        c = curve.Line()
        d1_feat["location"] = list(c.Location().Coord())
        d1_feat["direction"] = list(c.Direction().Coord())
        scale_factor = 1000.0
    elif c_type == "Circle":
        c = curve.Circle()
        d1_feat["location"] = list(c.Location().Coord())
        d1_feat["z_axis"] = list(c.Axis().Direction().Coord())
        d1_feat["radius"] = c.Radius()
        d1_feat["x_axis"] = list(c.XAxis().Direction().Coord())
        d1_feat["y_axis"] = list(c.YAxis().Direction().Coord())
        scale_factor = 1.0
    elif c_type == "Ellipse":
        c = curve.Ellipse()
        d1_feat["focus1"] = list(c.Focus1().Coord())
        d1_feat["focus2"] = list(c.Focus2().Coord())
        d1_feat["x_axis"] = list(c.XAxis().Direction().Coord())
        d1_feat["y_axis"] = list(c.YAxis().Direction().Coord())
        d1_feat["z_axis"] = list(c.Axis().Direction().Coord())
        d1_feat["maj_radius"] = c.MajorRadius()
        d1_feat["min_radius"] = c.MinorRadius()
        scale_factor = 1.0
    elif c_type == "BSpline":
        c = curve.BSpline()
        c.SetNotPeriodic()
        d1_feat["rational"] = c.IsRational()
        d1_feat["closed"] = c.IsClosed()
        d1_feat["continuity"] = c.Continuity()
        d1_feat["degree"] = c.Degree()
        p = TColgp_Array1OfPnt(1, c.NbPoles())
        c.Poles(p)
        points = []
        for pi in range(p.Length()):
            points.append(list(p.Value(pi+1).Coord()))
        d1_feat["poles"] = points

        k = TColStd_Array1OfReal(1, c.NbPoles() + c.Degree() + 1)
        c.KnotSequence(k)
        knots = []
        for ki in range(k.Length()):
            knots.append(k.Value(ki+1))
        d1_feat["knots"] = knots

        w = TColStd_Array1OfReal(1, c.NbPoles())
        c.Weights(w)
        weights = []
        for wi in range(w.Length()):
            weights.append(w.Value(wi+1))
        d1_feat["weights"] = weights

        scale_factor = 1.0
    else:
        print("Unsupported type 3d", c_type)

    return d1_feat

def convert_2dcurve(curve, convert_2bs=False):
    curve_t = curve.Edge()
    d1_feat = {"type": edge_map[curve.GetType()], "interval": [curve.FirstParameter(), curve.LastParameter()]}        
    c_type = d1_feat["type"]

    if c_type == "Line":
        c = curve.Line()
        d1_feat["location"] = list(c.Location().Coord())
        d1_feat["direction"] = list(c.Direction().Coord())
    elif c_type == "Circle":
        c = curve.Circle()
        d1_feat["location"] = list(c.Location().Coord())
        d1_feat["radius"] = c.Radius()
        d1_feat["x_axis"] = list(c.XAxis().Direction().Coord())
        d1_feat["y_axis"] = list(c.YAxis().Direction().Coord())
    elif c_type == "Ellipse":
        c = curve.Ellipse()
        d1_feat["focus1"] = list(c.Focus1().Coord())
        d1_feat["focus2"] = list(c.Focus2().Coord())
        d1_feat["x_axis"] = list(c.XAxis().Direction().Coord())
        d1_feat["y_axis"] = list(c.YAxis().Direction().Coord())
        d1_feat["maj_radius"] = c.MajorRadius()
        d1_feat["min_radius"] = c.MinorRadius()
    elif c_type == "BSpline":
        if not convert_2bs:
            c = curve.BSpline()
        else:
            c = curve
        c.SetNotPeriodic()
        d1_feat["rational"] = c.IsRational()
        d1_feat["closed"] = c.IsClosed()
        d1_feat["continuity"] = c.Continuity()
        d1_feat["degree"] = c.Degree()
        p = TColgp_Array1OfPnt2d(1, c.NbPoles())
        c.Poles(p)
        points = []
        for pi in range(p.Length()):
            points.append(list(p.Value(pi+1).Coord()))
        d1_feat["poles"] = points

        k = TColStd_Array1OfReal(1, c.NbPoles() + c.Degree() + 1)
        c.KnotSequence(k)
        knots = []
        for ki in range(k.Length()):
            knots.append(k.Value(ki+1))
        d1_feat["knots"] = knots

        w = TColStd_Array1OfReal(1, c.NbPoles())
        c.Weights(w)
        weights = []
        for wi in range(w.Length()):
            weights.append(w.Value(wi+1))
        d1_feat["weights"] = weights
    else:
        print("Unsupported type 2d", c_type)
    return d1_feat

def convert_surface(surf, convert_2bs=False):
    surf_t = surf.Face()
    d2_feat = {"type": surf_map[surf.GetType()]}

    s_type = d2_feat["type"]
        
    if s_type == "Plane":
        s = surf.Plane()
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["z_axis"] = list(s.Axis().Direction().Coord())
        d2_feat["x_axis"] = list(s.XAxis().Direction().Coord())
        d2_feat["y_axis"] = list(s.YAxis().Direction().Coord())
        d2_feat["coefficients"] = list(s.Coefficients())

    elif s_type == "Cylinder":
        s = surf.Cylinder()
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["z_axis"] = list(s.Axis().Direction().Coord())
        d2_feat["x_axis"] = list(s.XAxis().Direction().Coord())
        d2_feat["y_axis"] = list(s.YAxis().Direction().Coord())
        d2_feat["coefficients"] = list(s.Coefficients())
        d2_feat["radius"] = s.Radius()

    elif s_type == "Cone":
        s = surf.Cone()
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["z_axis"] = list(s.Axis().Direction().Coord())
        d2_feat["x_axis"] = list(s.XAxis().Direction().Coord())
        d2_feat["y_axis"] = list(s.YAxis().Direction().Coord())
        d2_feat["coefficients"] = list(s.Coefficients())
        d2_feat["radius"] = s.RefRadius()
        d2_feat["angle"] = s.SemiAngle()
        d2_feat["apex"] = list(s.Apex().Coord())

    elif s_type == "Sphere":
        s = surf.Sphere()
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["x_axis"] = list(s.XAxis().Direction().Coord())
        d2_feat["y_axis"] = list(s.YAxis().Direction().Coord())
        d2_feat["coefficients"] = list(s.Coefficients())
        d2_feat["radius"] = s.Radius()

    elif s_type == "Torus":
        s = surf.Torus()
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["z_axis"] = list(s.Axis().Direction().Coord())
        d2_feat["x_axis"] = list(s.XAxis().Direction().Coord())
        d2_feat["y_axis"] = list(s.YAxis().Direction().Coord())
        d2_feat["max_radius"] = s.MajorRadius()
        d2_feat["min_radius"] = s.MinorRadius()


    elif s_type == "Bezier":
        print("BEZIER SURF")

    elif s_type == "BSpline":
        if not convert_2bs:
            c = surf.BSpline()
        else:
            c = surf

        _round = lambda x: round(x, 15)
        d2_feat["trim_domain"] = list(map(_round, breptools_UVBounds(surf_t)))
        d2_feat["face_domain"] = list(map(_round, c.Bounds()))
        d2_feat["is_trimmed"] = d2_feat["trim_domain"] != d2_feat["face_domain"]
        c.SetUNotPeriodic()
        c.SetVNotPeriodic()
        d2_feat["u_rational"] = c.IsURational()
        d2_feat["v_rational"] = c.IsVRational()
        d2_feat["u_closed"] = c.IsUClosed()
        d2_feat["v_closed"] = c.IsVClosed()
        d2_feat["continuity"] = c.Continuity()
        d2_feat["u_degree"] = c.UDegree()
        d2_feat["v_degree"] = c.VDegree()

        p = TColgp_Array2OfPnt(1, c.NbUPoles(), 1, c.NbVPoles())
        c.Poles(p)
        points = []
        for pi in range(p.ColLength()):
            elems = []
            for pj in range(p.RowLength()):
                elems.append(list(p.Value(pi+1, pj+1).Coord()))
            points.append(elems)
        d2_feat["poles"] = points

        k = TColStd_Array1OfReal(1, c.NbUPoles() + c.UDegree() + 1)
        c.UKnotSequence(k)
        knots = []
        for ki in range(k.Length()):
            knots.append(k.Value(ki+1))
        d2_feat["u_knots"] = knots

        k = TColStd_Array1OfReal(1, c.NbVPoles() + c.VDegree() + 1)
        c.VKnotSequence(k)
        knots = []
        for ki in range(k.Length()):
            knots.append(k.Value(ki+1))
        d2_feat["v_knots"] = knots

        w = TColStd_Array2OfReal(1, c.NbUPoles(), 1, c.NbVPoles())
        c.Weights(w)
        weights = []
        for wi in range(w.ColLength()):
            elems = []
            for wj in range(w.RowLength()):
                elems.append(w.Value(wi+1, wj+1))
            weights.append(elems)
        d2_feat["weights"] = weights

        scale_factor = 1.0

    elif s_type == "Revolution":
        s = surf.AxeOfRevolution()
        c = surf.BasisCurve()
        d1_feat = convert_curve(c)
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["z_axis"] = list(s.Direction().Coord())
        d2_feat["curve"] = d1_feat

    elif s_type == "Extrusion":
        c = surf.BasisCurve()
        d1_feat = convert_curve(c)
        d2_feat["direction"] = list(surf.Direction().Coord())
        d2_feat["curve"] = d1_feat
        
    else:
        print("Unsupported type", s_type)
    
    return d2_feat


def mesh_model(model, res_path, convert=True, all_edges=True):
    fil = model.split("/")[-1][:-5]
    folder = "/".join(model.split("/")[:-1])
    with fileinput.FileInput(model, inplace=True) as fi:
        for line in fi:
            print(line.replace("UNCERTAINTY_MEASURE_WITH_UNIT( LENGTH_MEASURE( 1.00000000000000E-06 )",
                           "UNCERTAINTY_MEASURE_WITH_UNIT( LENGTH_MEASURE( 1.00000000000000E-17 )"), end='')

    occ_steps = read_step_file(model)
    bt = BRep_Tool()

    for occ_cnt in range(len(occ_steps)):
        if convert:
            try:
                nurbs_converter = BRepBuilderAPI_NurbsConvert(occ_steps[occ_cnt])
                nurbs_converter.Perform(occ_steps[occ_cnt])
                nurbs = nurbs_converter.Shape()
            except Exception as e:
                print("Conversion failed")
                print(occ_steps[occ_cnt])
                print(e)
                continue
        else:
            nurbs = occ_steps[occ_cnt]
            
        mesh = BRepMesh_IncrementalMesh(occ_steps[occ_cnt], 0.9, False, 0.5, True)
        mesh.Perform()
        if not mesh.IsDone():
            print("Mesh is not done.")
            continue
        
        occ_topo = TopologyExplorer(nurbs)
        occ_top = Topo(nurbs)
        occ_topo1 = TopologyExplorer(occ_steps[occ_cnt])
        occ_top1 = Topo(occ_steps[occ_cnt])
        
        d1_feats = []
        d2_feats = []
        t_curves = []
        tr_curves = []
        stats = {}
        stats["model"] = model
        total_edges = 0
        total_surfs = 0
        stats["curves"] = []
        stats["surfs"] = []
        c_cnt = 0
        t_cnt = 0

        # Iterate over edges
        for edge in occ_topo.edges():
            curve = BRepAdaptor_Curve(edge)
            stats["curves"].append(edge_map[curve.GetType()])
            d1_feat = convert_curve(curve)
            
            if edge_map[curve.GetType()] == "Other":
                continue
            
            for f in occ_top.faces_from_edge(edge):
                if f == None:
                    print("Broken face")
                    continue
                su = BRepAdaptor_Surface(f)
                c = BRepAdaptor_Curve2d(edge, f)
                t_curve = {"surface": f, "3dcurve": edge, "3dcurve_id": c_cnt, "2dcurve_id": t_cnt}
                t_curves.append(t_curve)
                tr_curves.append(convert_2dcurve(c))
                t_cnt += 1

            d1_feats.append(d1_feat)
            c_cnt += 1
            total_edges += 1

        patches = []
        faces1 = list(occ_topo1.faces())
        # Iterate over faces
        for fci, face in enumerate(occ_topo.faces()):
            surf = BRepAdaptor_Surface(face)
            stats["surfs"].append(surf_map[surf.GetType()])
            d2_feat = convert_surface(surf)
            
            if surf_map[surf.GetType()] == "Other":
                continue

            for tc in t_curves:
                if tc["surface"] == face:
                    patch = {"3dcurves": [], "2dcurves": [], "orientations": [], "surf_orientation": face.Orientation(),
                            "wire_ids": [], "wire_orientations": []}
                    
                    for wc, fw in enumerate(occ_top.wires_from_face(face)):
                        patch["wire_orientations"].append(fw.Orientation())
                        if all_edges:
                            edges = [i for i in WireExplorer(fw).ordered_edges()]
                        else:
                            edges = list(occ_top.edges_from_wire(fw))
                        for fe in edges:
                            for ttc in t_curves:
                                if ttc["3dcurve"].IsSame(fe) and tc["surface"] == ttc["surface"]:
                                    patch["3dcurves"].append(ttc["3dcurve_id"])
                                    patch["2dcurves"].append(ttc["2dcurve_id"])
                                    patch["wire_ids"].append(wc)
                                    orientation = fe.Orientation()
                                    patch["orientations"].append(orientation)
                                      
                    patches.append(patch)
                    break
            
            location = TopLoc_Location()
            facing = (bt.Triangulation(faces1[fci], location))
            if facing != None:
                tab = facing.Nodes()
                tri = facing.Triangles()
                verts = []
                for i in range(1, facing.NbNodes()+1):
                    verts.append(list(tab.Value(i).Coord()))

                faces = []
                for i in range(1, facing.NbTriangles()+1):
                    index1, index2, index3 = tri.Value(i).Get()
                    faces.append([index1 - 1, index2 - 1, index3 - 1])
            
                os.makedirs(res_path, exist_ok=True)
                igl.write_triangle_mesh("%s/%s_%03i_mesh_%04i.obj"%(res_path, fil, occ_cnt, fci), np.array(verts), np.array(faces))
                d2_feat["faces"] = faces
                d2_feat["verts"] = verts
            else:
                print("Missing triangulation")
                continue
            
            d2_feats.append(d2_feat)
            total_surfs += 1
            
            
        bbox =  get_boundingbox(occ_steps[occ_cnt], use_mesh=False)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox[:6]
        bbox1 = ["%.2f"%xmin, "%.2f"%ymin, "%.2f"%zmin, "%.2f"%xmax, "%.2f"%ymax, "%.2f"%zmax, "%.2f"%(xmax-xmin), "%.2f"%(ymax-ymin), "%.2f"%(zmax-zmin)]
        stats["#edges"] = total_edges
        stats["#surfs"] = total_surfs
                
        features = {"curves": d1_feats, "surfaces": d2_feats, "trim": tr_curves, "topo": patches, "bbox": bbox1}
        # Fix possible orientation problems
        if convert:
            features = convert_features(features)
        
        os.makedirs(res_path, exist_ok=True)
        fip = fil + "_features2"
        with open("%s/%s_%03i.yml"%(res_path, fip, occ_cnt), "w") as fili:
            yaml.dump(features, fili, indent=2)
        
        fip = fil + "_features"
        with open("%s/%s_%03i.yml"%(res_path, fip, occ_cnt), "w") as fili:
            features2 = copy.deepcopy(features)
            for sf in features2["surfaces"]:
                del sf["faces"]
                del sf["verts"]
            yaml.dump(features2, fili, indent=2)    

#        res_path = folder.replace("/step/", "/stat/")
#        fip = fil + "_stats"
#        with open("%s/%s_%03i.yml"%(res_path, fip, occ_cnt), "w") as fili:
#            yaml.dump(stats, fili, indent=2)
    
    print("Writing results for %s with %i parts."%(model, len(occ_steps)))


if __name__ == "__main__":
    f = sys.argv[1]
    r = sys.argv[2]
    if len(sys.argv) > 3:
        a = sys.argv[3]
        c = sys.argv[4]
    else:
        a = 1
        c = 1
    mesh_model(f, r, convert=bool(int(c)), all_edges=bool(int(a)))


