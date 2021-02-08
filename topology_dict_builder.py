
# Python OCC
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.TopExp import topexp
from OCC.Core.TopAbs import (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE, TopAbs_WIRE,
                             TopAbs_SHELL, TopAbs_SOLID, TopAbs_COMPOUND,
                             TopAbs_COMPSOLID)
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Wire
from OCC.Core.ShapeExtend import *


# CAD
import topology_utils as topology_utils

class TopologyDictBuilder:
    """
    A class which builds a python dictionary
    ready for export to the topology file
    """
    def __init__(self, entity_mapper):
        """
        Construct from the entity mapper which gives
        us a mapping between the 
        """
        self.entity_mapper = entity_mapper


    def build_dict_for_bodies(self, bodies):
        """
        Build the dictionary for these bodies
        """
        if isinstance(bodies, TopoDS_Shape):
            bodies = [bodies]
            
        body_dict = {
            "regions": self.build_regions_array(bodies),
            "shells": self.build_shells_array(bodies),
            "faces": self.build_faces_array(bodies),
            "edges": self.build_edges_array(bodies),
            "loops": self.build_loops_array(bodies),
            "halfedges": self.build_halfedges_array(bodies)
        }
        if len(bodies) > 1:
            body_dict["bodies"] = self.build_bodies_array(bodies)

        return body_dict

    def build_bodies_array(self, bodies):
        bodies_arr = []
        for body in bodies:
            bodies_arr.append(self.build_body_data(body))
        return bodies_arr

    def build_regions_array(self, bodies):
        regions_arr = []
        for body in bodies:
            top_exp = TopologyExplorer(body)
            regions = top_exp.solids()
            for region in regions:
                expected_region_index = self.entity_mapper.region_index(region)
                assert expected_region_index == len(regions_arr)
                regions_arr.append(self.build_region_data(top_exp, region))
        return regions_arr
        

    def build_shells_array(self, bodies):
        shells_arr = []
        for body in bodies:
            top_exp = TopologyExplorer(body)
            shells = top_exp.shells()
            for shell in shells:
                expected_shell_index = self.entity_mapper.shell_index(shell)
                assert expected_shell_index == len(shells_arr)
                shells_arr.append(self.build_shell_data(top_exp, shell))
        return shells_arr


    def build_faces_array(self, bodies):
        faces_arr = []
        for body in bodies:
            top_exp = TopologyExplorer(body)
            faces = top_exp.faces()
            for face in faces:
                expected_face_index = self.entity_mapper.face_index(face)
                assert expected_face_index == len(faces_arr)
                faces_arr.append(self.build_face_data(top_exp, face))
        return faces_arr


    def build_edges_array(self, bodies):
        edges_arr = []
        for body in bodies:
            top_exp = TopologyExplorer(body)
            edges = top_exp.edges()
            for edge in edges:
                expected_edge_index = self.entity_mapper.edge_index(edge)
                assert expected_edge_index == len(edges_arr)
                edges_arr.append(self.build_edge_data(top_exp, edge))
        return edges_arr


    def build_loops_array(self, bodies):
        loops_arr = []
        for body in bodies:
            top_exp = TopologyExplorer(body)
            loops = top_exp.wires()
            for loop in loops:
                expected_loop_index = self.entity_mapper.loop_index(loop)
                assert expected_loop_index == len(loops_arr)
                loops_arr.append(self.build_loop_data(top_exp, loop))
        return loops_arr


    def build_halfedges_array(self, bodies):
        halfedges_arr = []
        for body in bodies:
            oriented_top_exp = TopologyExplorer(body, ignore_orientation=False)
            halfedges = oriented_top_exp.edges()
            halfedge_set = set()
            for halfedge in halfedges:
                h = self.entity_mapper.get_hash(halfedge)
                orientation = halfedge.Orientation()
                tup = (h, orientation)
                if not tup in halfedge_set:
                    expected_halfedge_index = self.entity_mapper.halfedge_index(halfedge)
                    assert expected_halfedge_index == len(halfedges_arr)
                    halfedges_arr.append(self.build_halfedge_data(halfedge))
                    halfedge_set.add(tup)
        return halfedges_arr

    def build_body_data(self, body):
        region_indices = []
        top_exp = TopologyExplorer(body)
        regions = top_exp.solids()
        for region in regions:
            region_index = self.entity_mapper.region_index(region)
            region_indices.append(region_index)
        return {
            "regions": region_indices
        }

    def build_region_data(self, top_exp, region):
        shell_indices = []
        shells = top_exp._loop_topo(TopAbs_SHELL, region)
        for shell in shells:
            shell_orientation = topology_utils.orientation_to_sense(shell.Orientation())
            shell_indices.append(self.entity_mapper.shell_index(shell))
        return {
            "shells": shell_indices
        }


    def build_shell_data(self, top_exp, shell):
        face_list = []
        faces = top_exp._loop_topo(TopAbs_FACE, shell)
        shell_orientation = topology_utils.orientation_to_sense(shell.Orientation())
        for face in faces:
            # We need to know if this face-use has the same orientation 
            # as the "primary face-use"
            face_orientation = topology_utils.orientation_to_sense(face.Orientation())
            primary_face_orientation = self.entity_mapper.primary_face_orientation(face)

            # Is this face-use oriented the same way as the primary face-use
            face_orientation_wrt_shell = bool(face_orientation) == bool(primary_face_orientation) 
            face_list.append(
                {
                    "face_index": self.entity_mapper.face_index(face),
                    "face_orientation_wrt_shell": face_orientation_wrt_shell
                }
            )
        return {
            "orientation_wrt_region": shell_orientation,
            "faces": face_list
        }


    def build_face_data(self, top_exp, face):
        loop_indices = []
        loops = top_exp.wires_from_face(face)
        for loop in loops:
            loop_indices.append(self.entity_mapper.loop_index(loop))
        
        # Face normal wrt surface normal
        orientation = self.entity_mapper.primary_face_orientation(face)
        index_of_face = self.entity_mapper.face_index(face)
        
        return {
            "surface": index_of_face,
            "surface_orientation": orientation,
            "loops": loop_indices,
        }


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
        
        assert start_point.IsEqual(start_point_from_vertex, tolerance)
        assert end_point.IsEqual(end_point_from_vertex, tolerance)

    def build_edge_data(self, top_exp, edge):
        index_of_edge = self.entity_mapper.edge_index(edge)
        start_vertex = topexp.FirstVertex(edge)
        end_vertex = topexp.LastVertex(edge)

        start_vertex_index = self.entity_mapper.vertex_index(start_vertex)
        end_vertex_index = self.entity_mapper.vertex_index(end_vertex)

        return {
            "3dcurve": index_of_edge,
            "start_vertex": start_vertex_index,
            "end_vertex": end_vertex_index
        }


    def build_loop_data(self, top_exp, loop):
        nr = top_exp.number_of_faces_from_wires(loop)
        assert nr == 1
        face = list(top_exp.faces_from_wire(loop))[0]
        saw = ShapeAnalysis_Wire(loop, face, 1e-8)
        #saw.Perform()
        sd = {}
        sd["order"] = saw.CheckOrder()
        sd["connected"] = saw.CheckConnected()
        sd["small"] = saw.CheckSmall()
        sd["edgecurves"] = saw.CheckEdgeCurves()
        sd["degenerated"] = saw.CheckDegenerated()
        sd["closed"] = saw.CheckClosed()
        
        sd["sisect"] = saw.CheckSelfIntersection()
        sd["lack"] = saw.CheckLacking()
        sd["gap3d"] = saw.CheckGaps3d()
        sd["gap2d"] = saw.CheckGaps2d()
        sd["gapcurve"] = saw.CheckCurveGaps()
        
        wire_exp = WireExplorer(loop)
        halfedge_indices = []
        halfedges = wire_exp.ordered_edges()
        for halfedge in halfedges:
            halfedge_indices.append(self.entity_mapper.halfedge_index(halfedge))
        return {
            "halfedges": halfedge_indices,
            "status": sd
        }


    def build_halfedge_data(self, halfedge):
        orientation = topology_utils.orientation_to_sense(halfedge.Orientation())
        mate = halfedge.Reversed()
        orientation2 = topology_utils.orientation_to_sense(halfedge.Orientation())
        assert orientation == orientation2
        mates = []
        if self.entity_mapper.halfedge_exists(mate):
            mates.append(self.entity_mapper.halfedge_index(mate))
        
        edge_index = self.entity_mapper.edge_index(halfedge)
        halfedge_index = self.entity_mapper.halfedge_index(halfedge)

        return {
            "mates": mates,
            "2dcurve": halfedge_index,
            "edge": edge_index,
            "orientation_wrt_edge": orientation
        }


    def point_to_str(self, pt):
        return f"<{pt.X()}, {pt.Z()}, {pt.Z()}>"
