from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface, BRepAdaptor_CompCurve, BRepAdaptor_Curve2d
from OCC.Core.TColStd import TColStd_Array1OfReal, TColStd_Array2OfReal
from OCC.Core.TColgp import TColgp_Array1OfPnt, TColgp_Array2OfPnt, TColgp_Array1OfPnt2d
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepTools import breptools_UVBounds
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pnt2d

from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface
from OCC.Core.ShapeAnalysis import shapeanalysis_OuterWire
from OCC.Core.ShapeAnalysis import shapeanalysis_GetFaceUVBounds



from yaml import CLoader
import yaml
import json
import numpy as np

def write_dictionary_to_file(path, data, data_format="yaml"):
    if data_format.lower() == "json":
        write_dict_to_json(path, data)
    elif data_format.lower() == "yaml": 
        write_dict_to_yaml(path, data)
    else:
        print("Wrong data_format, allowed types are 'yaml' and 'json'.")

def load_dictionary_from_file(path, data_format="yaml"):
    if data_format.lower() == "json":
        return load_dict_from_json(path)
    elif data_format.lower() == "yaml": 
        return load_dict_from_yaml(path)
    else:
        print("Wrong data_format, allowed types are 'yaml' and 'json'.")
        
def load_dict_from_yaml(path):
    with open(path, "r") as fp:
        return yaml.load(fp, Loader=CLoader)

def load_dict_from_json(path):
    with open(path, "r") as fp:
        return json.load(fp)
        
def write_dict_to_yaml(path, data):
    if not path.suffix.endswith(".yaml"):
        new_path = path.with_suffix(path.suffix + ".yaml")
    else:
        new_path = path
    with open(new_path, "w") as fp:
        yaml.dump(data, fp, indent=2, width=79, default_flow_style=None)
        
def write_dict_to_json(path, data):
    new_path = path.with_suffix(path.suffix + ".json")
    with open(new_path, "w") as fp:
        json.dump(data, fp, indent=2)

def load_parts_from_step_file(pathname, logger=None):
    assert pathname.exists()
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(str(pathname))
    if status == IFSelect_RetDone:  # check status
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
            logger.error("Step transfer problem: %i"%nr)
            #print("No Shape", nr)
    else:
        logger.error("Step reading problem.")
        #raise AssertionError("Error: can't read file.")

    logger.info("Loaded parts: %i"%len(shapes))
    return shapes

def get_tri_vertex_coord(mesh, index):
    return np.array(list(mesh.Node(index).Coord()))

def convert_vec_to_np(vec):
    return np.array(list(vec.Coord()))

def convert_vec_to_list(vec):
    return list(vec.Coord())

def get_face_normal(surf, uv, face_orientation_wrt_surf):
    # Evaluate the surface at that UV
    point = gp_Pnt()
    u_deriv_vec = gp_Vec()
    v_deriv_vec = gp_Vec()
    surf.D1(uv.X(), uv.Y(), point, u_deriv_vec, v_deriv_vec)
    u_deriv = convert_vec_to_np(u_deriv_vec)
    v_deriv = convert_vec_to_np(v_deriv_vec)
    face_normal = np.cross(u_deriv, v_deriv)
    if not  face_orientation_wrt_surf:
        face_normal = -face_normal
    return face_normal

def vectors_parallel(v1, v2):
    l1 = np.linalg.norm(v1)
    l2 = np.linalg.norm(v2)

    # In the case of zero vectors we assume the
    # vectors to be parallel
    eps = 1e-7
    if l1 < eps:
        return True
    if l2 < eps:
        return True

    d = np.dot(v1, v2)
    cos_angle = d/(l1*l2)

    angle_tol_deg = 1
    angle_tol_rands = math.pi * angle_tol_deg/180.8
    cos_tol_angle = math.cos(angle_tol_rands)
    return cos_tol_angle > cos_angle

def get_boundingbox(body, tol=1e-6, use_mesh=False, logger=None):
    bbox = Bnd_Box()
    bbox.SetGap(tol)
    if use_mesh:
        if logger:
            logger.info("Meshing body: Init")
        mesh = BRepMesh_IncrementalMesh(body, 0.01, True, 0.1, True)
        #mesh.SetParallel(True)
        mesh.SetShape(body)
        mesh.Perform()
        assert mesh.IsDone()
        if logger:
            logger.info("Meshing body: Done")
    try:
        brepbndlib_Add(body, bbox, use_mesh)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    except:
        xmin = ymin = zmin = xmax = ymax = zmax = 0.0
    return [xmin, ymin, zmin, xmax, ymax, zmax]


def edge_type(nr):
    edge_map = {0: "Line", 1: "Circle", 2: "Ellipse", 3: "Hyperbola", 4: "Parabola", 5: "Bezier", 6: "BSpline", 7: "Offset", 8: "Other"}
    return edge_map[nr]

def surf_type(nr):
    surf_map = {0: "Plane", 1: "Cylinder", 2: "Cone", 3: "Sphere", 4: "Torus", 5: "Bezier", 6: "BSpline", 7: "Revolution", 8: "Extrusion", 9: "Offset", 10: "Other"}
    return surf_map[nr]


def convert_3dcurve(edge, curve_input=False):
    d1_feat = {}
    if not curve_input:
        curve = BRepAdaptor_Curve(edge)
    else:
        curve = edge
    c_type = edge_type(curve.GetType())
    d1_feat["interval"] = [curve.FirstParameter(), curve.LastParameter()]
    d1_feat["type"] = c_type
    
    if c_type == "Other":
        #print("Other Curve")
        return d1_feat

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
        #d1_feat["periodic"] = c.IsPeriodic()
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

def convert_2dcurve(edge, surface):
    d1_feat = {}
    curve = BRepAdaptor_Curve2d(edge, surface)
    c_type = edge_type(curve.GetType())
    d1_feat["interval"] = [curve.FirstParameter(), curve.LastParameter()]
    d1_feat["type"] = c_type

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
        c = curve.BSpline()
        c.SetNotPeriodic()
        #d1_feat["periodic"] = c.IsPeriodic()
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

def convert_surface(face):
    d2_feat = {}
    surf = BRepAdaptor_Surface(face)
    s_type = surf_type(surf.GetType())
    d2_feat["type"] = s_type
    _round = lambda x: round(x, 15)
    d2_feat["trim_domain"] = list(map(_round, breptools_UVBounds(face)))
    #print(surf.FirstUParameter(), surf.LastUParameter(), surf.FirstVParameter(), surf.LastVParameter())
    #print(d2_feat["face_domain"])

        
    if s_type == "Plane":
        s = surf.Plane()
        #print(dir(s), dir(surf), type(s), type(surf))
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
        c = surf.BSpline()
        _round = lambda x: round(x, 15)
        d2_feat["trim_domain"] = list(map(_round, breptools_UVBounds(face)))
        d2_feat["face_domain"] = list(map(_round, c.Bounds()))
        d2_feat["is_trimmed"] = d2_feat["trim_domain"] != d2_feat["face_domain"]
        #print(c.IsUPeriodic(), c.IsVPeriodic())
        c.SetUNotPeriodic()
        c.SetVNotPeriodic()
        #d2_feat["u_periodic"] = c.IsUPeriodic()
        #d2_feat["v_periodic"] = c.IsVPeriodic()
        #print(d2_feat["trim_domain"], d2_feat["face_domain"])
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
        per_offset = 1
        #if c.IsVPeriodic():
        #    per_offset = 2
        #print(c.NbVPoles() + c.VDegree() + 1 + per_offset, c.IsVPeriodic())
        k = TColStd_Array1OfReal(1, c.NbVPoles() + c.VDegree() + per_offset)
        #print(c.NbVPoles() + c.VDegree() + 1)
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
        d1_feat = convert_3dcurve(c, curve_input=True)
        d2_feat["location"] = list(s.Location().Coord())
        d2_feat["z_axis"] = list(s.Direction().Coord())
        d2_feat["curve"] = d1_feat

    elif s_type == "Extrusion":
        c = surf.BasisCurve()
        d1_feat = convert_3dcurve(c, curve_input=True)
        d2_feat["direction"] = list(surf.Direction().Coord())
        d2_feat["curve"] = d1_feat
        
    else:
        print("Unsupported type", s_type)
        print(dir(surf))
    
    return d2_feat