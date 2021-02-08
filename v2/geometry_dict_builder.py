
# Python OCC
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.TopExp import topexp
from OCC.Core.TopAbs import (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE, TopAbs_WIRE,
                             TopAbs_SHELL, TopAbs_SOLID, TopAbs_COMPOUND,
                             TopAbs_COMPSOLID)
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopoDS import TopoDS_Shape


# CAD
import topology_utils as topology_utils
from utils import get_boundingbox, convert_3dcurve, convert_2dcurve, convert_surface, convert_vec_to_list

class GeometryDictBuilder:
    """
    A class which builds a python dictionary
    ready for export to the geometry file
    """
    def __init__(self, entity_mapper):
        """
        Construct from the entity mapper which gives
        us a mapping between entities
        """
        self.entity_mapper = entity_mapper


    def build_dict_for_bodies(self, bodies, logger=None):
        """
        Build the dictionary for these bodies
        """
        if isinstance(bodies, TopoDS_Shape):
            bodies = [bodies]
            
        body_dicts = []
            
        for body in bodies:
            
            surfaces, curves2d = self.build_surfaces_and_2dcurves(body)

            body_dict = {
                "bbox": get_boundingbox(body, logger=logger),
                "surfaces": surfaces,
                "3dcurves": self.build_3dcurves_array(body),
                "2dcurves": curves2d,
                "vertices": self.build_vertices_array(body)
            }
            body_dicts.append(body_dict)

        return body_dicts
    
    def build_vertices_array(self, body):
        top_exp = TopologyExplorer(body)
        nr_verts = top_exp.number_of_vertices()
        body_vertices = [None]*nr_verts
        verts = top_exp.vertices()
        for vert in verts:
            expected_vert_index = self.entity_mapper.vertex_index(vert)
            #print(len(body_curves), expected_edge_index)
            assert expected_vert_index >= 0 and expected_vert_index < len(body_vertices)
            assert body_vertices[expected_vert_index] == None
            body_vertices[expected_vert_index] = self.build_vertex_data(vert)

        return body_vertices
    
    def build_vertex_data(self, vertex):
        return convert_vec_to_list(BRep_Tool.Pnt(vertex))

    def build_3dcurves_array(self, body):
        top_exp = TopologyExplorer(body)
        nr_edges = top_exp.number_of_edges()
        body_curves = [None]*nr_edges
        edges = top_exp.edges()
        for edge in edges:
            expected_edge_index = self.entity_mapper.edge_index(edge)
            #print(len(body_curves), expected_edge_index)
            assert expected_edge_index >= 0 and expected_edge_index < len(body_curves)
            assert body_curves[expected_edge_index] == None
            body_curves[expected_edge_index] = self.build_3dcurve_data(edge)

        return body_curves
    
    def build_3dcurve_data(self, edge):
        # Check this actually gets the vertex order correct
        start_vertex = topexp.FirstVertex(edge)
        end_vertex = topexp.LastVertex(edge)
        self.debug_check_correct_vertex_order(edge, start_vertex, end_vertex)
        curve = convert_3dcurve(edge)
        return curve

    def build_surfaces_and_2dcurves(self, body):
        top_exp = TopologyExplorer(body, ignore_orientation=False)
        nr_faces = top_exp.number_of_faces()
        body_surfaces = [None]*nr_faces
        body_2dcurves_dict = {}

        # Iterate over faces
        faces = top_exp.faces()
        for face in faces:
            expected_face_index = self.entity_mapper.face_index(face)
            assert expected_face_index >= 0 and expected_face_index < len(body_surfaces)
            assert body_surfaces[expected_face_index] == None
            body_surfaces[expected_face_index] = convert_surface(face)
            
#             # TODO add proper meshing code
#             verts, tris, _, _, _ = process_face(expected_face_index, face)
#             os.makedirs(res_path, exist_ok=True)
#             igl.write_triangle_mesh("%s/%s_%03i_mesh_%04i.obj"%(res_path, fil, occ_cnt, fci), np.array(verts), np.array(faces))

            # Iterate over edges in face
            edges = top_exp.edges_from_face(face)
            for edge in edges:                  
                expected_halfedge_index = self.entity_mapper.halfedge_index(edge)
                #assert expected_halfedge_index not in body_2dcurves_dict
                body_2dcurves_dict[expected_halfedge_index] = convert_2dcurve(edge, face)


        body_2dcurves = []
        assert list(body_2dcurves_dict.keys()) == list(range(len(body_2dcurves_dict.keys())))
        for ci in range(len(body_2dcurves_dict.keys())):
            body_2dcurves.append(body_2dcurves_dict[ci])

        return body_surfaces, body_2dcurves



    def debug_check_correct_vertex_order(
        self, 
        edge, 
        start_vertex,
        end_vertex
    ):
        """
        Check the correct vertex is used as the start and end vertex
        given the geometry of the edge curve
        """
        curve = BRepAdaptor_Curve(edge)
        t_start = curve.FirstParameter()
        t_end = curve.LastParameter()
        start_point = curve.Value(t_start)
        end_point = curve.Value(t_end)

        start_point_from_vertex = BRep_Tool.Pnt(start_vertex)
        end_point_from_vertex = BRep_Tool.Pnt(end_vertex)

        tolerance = 0.01
        # print(f"start_point {self.point_to_str(start_point)}")
        # print(f"start_point_from_vertex {self.point_to_str(start_point_from_vertex)}")
        # print(f"end_point {self.point_to_str(end_point)}")
        # print(f"end_point_from_vertex {self.point_to_str(end_point_from_vertex)}")
        #assert start_point.IsEqual(start_point_from_vertex, tolerance)
        #assert end_point.IsEqual(end_point_from_vertex, tolerance)

    def point_to_str(self, pt):
        return f"<{pt.X()}, {pt.Z()}, {pt.Z()}>"
