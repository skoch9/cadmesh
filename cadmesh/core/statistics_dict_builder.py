from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface
from OCC.Core.ShapeAnalysis import shapeanalysis_OuterWire
from OCC.Core.ShapeAnalysis import shapeanalysis_GetFaceUVBounds
from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pnt2d




def extract_face_stats(face, entity_mapper, prec=1e-8):
    stats = {}
    # Exact domain calculation
    umin, umax, vmin, vmax = shapeanalysis_GetFaceUVBounds(face)
    stats["exact_domain"] = [umin, umax, vmin, vmax]

    # Outer wire
    ow = shapeanalysis_OuterWire(face)
    stats["outer_wire"] = entity_mapper.loop_index(ow)

    # 
    srf = BRep_Tool().Surface(face)               
    sas = ShapeAnalysis_Surface(srf)

    stats["has_singularities"] = sas.HasSingularities(prec)
    stats["nr_singularities"] = sas.NbSingularities(prec)
    singularities = []
    for i in range(1, 10):
        point3d = gp_Pnt()
        point2d_first = gp_Pnt2d()
        point2d_last = gp_Pnt2d()
        sing = sas.Singularity(i, point3d, point2d_first, point2d_last)
        if sing[0] and stats["has_singularities"]:
            singularity = {}
            singularity["rank"] = i
            singularity["precision"] = sing[1]
            singularity["firstpar"] = sing[2]
            singularity["lastpar"] = sing[3]
            singularity["uiso"] = sing[4]
            singularity["point3d"] = list(point3d.Coord())
            singularity["first2d"] = list(point2d_first.Coord())
            singularity["last2d"] = list(point2d_last.Coord())
            point2d = sas.ValueOfUV(point3d, prec)
            singularity["point2d"] = list(point2d.Coord())
            singularities.append(singularity)
        else: 
            break

    stats["singularities"] = singularities   
    #print(stats["has_singularities"])
    #print(stats["nr_singularities"])
#                 surf = BRepAdaptor_Surface(face)
#                 _round = lambda x: round(x, 15)
#                 c = surf.BSpline()
#                 trim_domain = list(map(_round, breptools_UVBounds(face)))
#                 face_domain = list(map(_round, c.Bounds()))

#                 print(trim_domain)
#                 print(face_domain)

    #print("EFS", stats)
    return stats


def extract_statistical_information(body, entity_mapper, logger):
    top_exp = TopologyExplorer(body, ignore_orientation=False)
    nr_faces = top_exp.number_of_faces()
    stats = [None]*nr_faces
    # Iterate over faces
    faces = top_exp.faces()
    for face in faces:
        expected_face_index = entity_mapper.face_index(face)
        try:
            f_stats = extract_face_stats(face, entity_mapper)
            assert stats[expected_face_index] == None
            stats[expected_face_index] = f_stats
        except Exception as e:
            #print("Conversion failed, processing unconverted")
            #print(e.args.split("\n"))
            logger.error("Stat extraction error: %s"%str(e))
            continue
            

    #print("ESI", stats)
    return stats