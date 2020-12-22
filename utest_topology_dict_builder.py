#!/usr/bin/python

# System
import unittest
from pathlib import Path
import numpy as np
import math
import yaml

# Debugging visualization
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# Other libs
import igl

# CAD
from entity_mapper import EntityMapper
from topology_dict_builder import TopologyDictBuilder
import topology_utils as  topology_utils

# PythonOCC
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pnt2d
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BOPAlgo import BOPAlgo_Builder
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepTools import breptools
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.TopExp import topexp
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Curve2d, BRepAdaptor_Surface
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Wire
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.GCPnts import GCPnts_QuasiUniformDeflection
from OCC.Display.SimpleGui import init_display

class TopologyDictBuilderUtest(unittest.TestCase):

    def load_bodies_from_file(self, pathname):
        self.assertTrue(pathname.exists())
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
                print("No Shape", nr)
        else:
            raise AssertionError("Error: can't read file.")

        return shapes

    def debug_save_mesh(self, output_pathname, body):
        top_exp = TopologyExplorer(body)
        brep_tool = BRep_Tool()
        faces = top_exp.faces()
        first_vertex = 0
        tris = []
        verts = []
        for face in faces:
            face_orientation_wrt_surface_normal = topology_utils.orientation_to_sense(face.Orientation())
            location = TopLoc_Location()
            mesh = brep_tool.Triangulation(face, location)
            if mesh != None:
                self.assertTrue(mesh.HasUVNodes())

                # Loop over the triangles
                num_tris = mesh.NbTriangles()
                for i in range(1, num_tris+1):
                    index1, index2, index3 = mesh.Triangle(i).Get()

                    # Get the UV nodes
                    uv1 = self.convert_gp_pnt2d_to_numpy(mesh.UVNode(index1))
                    uv2 = self.convert_gp_pnt2d_to_numpy(mesh.UVNode(index2))
                    uv3 = self.convert_gp_pnt2d_to_numpy(mesh.UVNode(index3))
                    duv1 = uv2-uv1
                    duv2 = uv3-uv1

                    # We want to find out if the triangle nodes have
                    # anti-clockwise ordering in the UV space
                    area2 = np.cross(duv1, duv2)
                    self.assertTrue(area2 > 0.0)

                    if face_orientation_wrt_surface_normal:
                        # Same sense
                        tris.append([
                            first_vertex + index1 - 1, 
                            first_vertex + index2 - 1, 
                            first_vertex + index3 - 1
                        ])
                    else:
                        # Opposite sense
                        tris.append([
                            first_vertex + index3 - 1, 
                            first_vertex + index2 - 1, 
                            first_vertex + index1 - 1
                        ])

                num_vertices = mesh.NbNodes()
                first_vertex += num_vertices
                for i in range(1, num_vertices+1):
                    verts.append(list(mesh.Node(i).Coord()))

        igl.write_triangle_mesh(str(output_pathname), np.array(verts), np.array(tris))

    def debug_print_wire_poly(self, wire):
        poly = self.create_3d_polygon(wire)
        print("create line continuous")
        for point in poly:
            print(f"world {point[0]} {point[1]} {point[2]}")


    def debug_view_body(self, body):
        pyqt5_display, start_display, add_menu, add_function_to_menu = init_display('qt-pyqt5')
        pyqt5_display.DisplayShape(body, update=True)
        start_display()


    def make_non_manifold_body(self):
        b1 = BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 10, 10, 10).Shape()
        b2 = BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), 10, 10, 10).Shape()
        builder = BOPAlgo_Builder()
        builder.AddArgument(b1)
        builder.AddArgument(b2)
        builder.SetRunParallel(True)
        builder.Perform()
        self.assertTrue(not builder.HasErrors())
        return builder.Shape()


    def build_dict_for_non_manifold_body(self):
        body = self.make_non_manifold_body()
        self.build_dict_for_bodies([ body ], expect_manifold=False)

    def check_face_orientation_wrt_shell(self, output):
        # The sum of all the faces-uses referenced by the shells
        # will be the same as the total number of faces in the body
        total_num_shell_faces = 0
        for shell in output["shells"]:
            total_num_shell_faces += len(shell["faces"])

            # We expect all the face orientations wrt the shell
            # to have orientation = True
            for face in shell["faces"]:
                self.assertTrue(face["face_orientation_wrt_shell"])
        self.assertTrue(total_num_shell_faces == len(output["faces"]))

    def get_tri_vertex_coord(self, mesh, index):
        return np.array(list(mesh.Node(index).Coord()))
    
    def convert_vec_to_np(self, vec):
        return np.array(list(vec.Coord()))
        
    def get_face_normal(self, surf, uv, face_orientation_wrt_surf):
        # Evaluate the surface at that UV
        point = gp_Pnt()
        u_deriv_vec = gp_Vec()
        v_deriv_vec = gp_Vec()
        surf.D1(uv.X(), uv.Y(), point, u_deriv_vec, v_deriv_vec)
        u_deriv = self.convert_vec_to_np(u_deriv_vec)
        v_deriv = self.convert_vec_to_np(v_deriv_vec)
        face_normal = np.cross(u_deriv, v_deriv)
        if not  face_orientation_wrt_surf:
            face_normal = -face_normal
        return face_normal

    def vectors_parallel(self, v1, v2):
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

    def check_face_orientation_against_triangles(
            self,
            output_face,
            face
        ):
        output_face_orientation = output_face["surface_orientation"]
        face_orientation = topology_utils.orientation_to_sense(face.Orientation())
        self.assertTrue(output_face_orientation == face_orientation)
        surf = BRepAdaptor_Surface(face)
        location = TopLoc_Location()
        brep_tool = BRep_Tool()
        mesh = brep_tool.Triangulation(face, location)
        if mesh != None:
            # Loop over the triangles
            ntris = mesh.NbTriangles()
            for i in range(1, mesh.NbTriangles()+1):
                # Find the facet normal of each triangle
                index1, index2, index3 = mesh.Triangle(i).Get()

                # Sadly the triangles are not oriented.  At least if we
                # check against the triangles we can tell at a glance when something is
                # wrong.
                # Do we need to reverse the triangles?
                if not output_face_orientation:
                    temp = index1
                    index1 = index3
                    index3 = temp

                pt1 = self.get_tri_vertex_coord(mesh, index1)
                pt2 = self.get_tri_vertex_coord(mesh, index2)
                pt3 = self.get_tri_vertex_coord(mesh, index3)
                v1 = pt2-pt1
                v2 = pt2-pt3
                normal_from_triangle = np.cross(v1, v2)
            
                # Evaluate the normal on the surface.
                # If this is very different from the triangle
                # normal we will know something is wrong!
                uv1 = mesh.UVNode(index1)
                normal_from_face = self.get_face_normal(surf, uv1, face_orientation)
                self.assertTrue(self.vectors_parallel(normal_from_face, normal_from_triangle))
                

    def check_face_orientations_against_triangles(
            self,
            output,
            body, 
            entity_mapper
        ):

        # Loop over the faces
        top_exp = TopologyExplorer(body)
        faces = top_exp.faces()
        for face in faces:
            face_index = entity_mapper.face_index(face)
            output_face = output["faces"][face_index]
            self.check_face_orientation_against_triangles(output_face, face)

    def convert_gp_pnt3d_to_numpy(self, pt3d):
        return np.array([pt3d.X(), pt3d.Y(), pt3d.Z()])

    def convert_gp_pnt2d_to_numpy(self, pt2d):
        return np.array([pt2d.X(), pt2d.Y()])

    def area_np(self, points):        
        x = points[:,0]
        y = points[:,1]
        n = x.size
        shift_up = np.arange(-n+1, 1)
        shift_down = np.arange(-1, n-1)    
        return (x * (y.take(shift_up) - y.take(shift_down))).sum() / 2.0

    def create_3d_polygon(self, wire):
        wire_exp = WireExplorer(wire)
        halfedges = wire_exp.ordered_edges()
        points = []
        for halfedge in halfedges:
            curve_3d = BRepAdaptor_Curve(halfedge)
            halfedge_orientation = topology_utils.orientation_to_sense(halfedge.Orientation())
            num_points_per_curve = 10
            tmin = curve_3d.FirstParameter()
            tmax = curve_3d.LastParameter()

            if halfedge_orientation:
                t_params = np.linspace(tmin, tmax, num_points_per_curve)
            else:
                t_params = np.linspace(tmax, tmin, num_points_per_curve)

            for i in range(t_params.size):
                t = t_params[i]
                pt3d = curve_3d.Value(t)
                points.append(self.convert_gp_pnt3d_to_numpy(pt3d))
        return np.stack(points)

    def create_2d_polygon(self, wire, face):
        wire_exp = WireExplorer(wire)
        halfedges = wire_exp.ordered_edges()
        points = []
        for halfedge in halfedges:
            curve_2d = BRepAdaptor_Curve2d(halfedge, face)
            halfedge_orientation = topology_utils.orientation_to_sense(halfedge.Orientation())
            num_points_per_curve = 10
            tmin = curve_2d.FirstParameter()
            tmax = curve_2d.LastParameter()

            if halfedge_orientation:
                t_params = np.linspace(tmin, tmax, num_points_per_curve)
            else:
                t_params = np.linspace(tmax, tmin, num_points_per_curve)

            for i in range(t_params.size):
                t = t_params[i]
                pt2d = curve_2d.Value(t)
                points.append(self.convert_gp_pnt2d_to_numpy(pt2d))
        return np.stack(points)

    def display_poly(self, poly):
        fig, ax = plt.subplots()
        polygon = Polygon(poly, True)
        ax.add_patch(polygon)

        num_points = poly.shape[0]
        for i in range(num_points):
            text = f"{i}"
            ax.annotate(
                text,
                xy=poly[i, :]
            )
        plt.axis('off')
        ax.axis('equal')
        plt.show()

    def check_orientations_of_2d_and_3d_curves(self, wire, face):
        surf = BRepAdaptor_Surface(face)
        wire_exp = WireExplorer(wire)
        halfedges = wire_exp.ordered_edges()
        for halfedge in halfedges:
            curve3 = BRepAdaptor_Curve(halfedge)
            curve2 = BRepAdaptor_Curve2d(halfedge, face)
            tmin3d = curve3.FirstParameter()
            tmax3d = curve3.LastParameter()
            tmin2d = curve2.FirstParameter()
            tmax2d = curve2.LastParameter()
            self.assertAlmostEqual(tmin3d, tmin2d, places=3)
            self.assertAlmostEqual(tmax3d, tmax2d, places=3)
            num_points = 10
            t_params = np.linspace(tmin2d, tmax2d, num_points)

            # We only want to see errors when we made a mistake with the
            # code and don't understand how Open Cascade works...
            bt = BRep_Tool()
            edge_tolerance = bt.Tolerance(halfedge)
            extra_tolerance = 0.01 
            tolerance = edge_tolerance + extra_tolerance

            for i in range(num_points):
                t = t_params[i]
                uv = curve2.Value(t)
                pt_from_2d = self.convert_gp_pnt3d_to_numpy(surf.Value(uv.X(), uv.Y()))
                pt3d = self.convert_gp_pnt3d_to_numpy(curve3.Value(t))
                self.assertTrue(np.allclose(pt_from_2d, pt3d, atol=tolerance))


    def check_loop_orientation(self, wire, face):
        face_orientation = topology_utils.orientation_to_sense(face.Orientation())
        wire_orientation = topology_utils.orientation_to_sense(wire.Orientation())

        outer_wire = breptools.OuterWire(face)
        is_outer_wire =  (outer_wire == wire)

        # For an outer loop, the area of the UV polygon is:
        #    - Positive when the face normals agree with the surface normals
        #    - Negative when the face normals are opposite to the surface normals
        # For an inner loop we have the opposite
        #
        # Hence the loop winding rule is relative to the face rather than 
        # the surface
        expect_positive_area =  (face_orientation == is_outer_wire)

        poly = self.create_2d_polygon(wire, face)
        area = self.area_np(poly)
        found_positive_area = (area > 0.0)
        if expect_positive_area != found_positive_area:
            self.display_poly(poly)
            self.debug_print_wire_poly(wire)

        if expect_positive_area:
            self.assertTrue(area > 0.0)
        else:
            self.assertTrue(area < 0.0)


    def check_loop_order(
            self,
            output,
            wire,
            entity_mapper
        ):
        wire_exp = WireExplorer(wire)
        halfedges = wire_exp.ordered_edges()
        vertices = wire_exp.ordered_vertices()
        for halfedge, vertex in zip(halfedges, vertices):
            halfedge_index = entity_mapper.halfedge_index(halfedge)
            curve2d_index = output["halfedges"][halfedge_index]["2dcurve"]
            self.assertTrue(halfedge_index == curve2d_index)
            vertex_index = entity_mapper.vertex_index(vertex)

            halfedge_orientation = topology_utils.orientation_to_sense(halfedge.Orientation())
            output_halfedge_orientation = output["halfedges"][halfedge_index]["orientation_wrt_edge"]
            self.assertTrue(halfedge_orientation == output_halfedge_orientation)

            # The halfedge is really an edge along with a flag.  When 
            # we ask for the edge index the flag just gets ignored
            edge_index = entity_mapper.edge_index(halfedge)
            output_edge_index = output["halfedges"][halfedge_index]["edge"]
            self.assertTrue(edge_index == output_edge_index)

            output_edge_start_vertex = output["edges"][edge_index]["start_vertex"]
            output_edge_end_vertex = output["edges"][edge_index]["end_vertex"]
            if output_halfedge_orientation:
                self.assertTrue(output_edge_start_vertex == vertex_index)
            else:
                self.assertTrue(output_edge_end_vertex == vertex_index)


    def check_order_of_all_loops(
            self,
            output,
            body,
            entity_mapper
        ):
        top_exp = TopologyExplorer(body)
        faces = top_exp.faces()
        for face in faces:
            wires = top_exp.wires_from_face(face)
            for wire in wires:

                loop_index = entity_mapper.loop_index(wire)

                # Use the wire checker.  See 
                # https://old.opencascade.com/doc/occt-7.4.0/overview/html/occt_user_guides__shape_healing.html#occt_shg_3_1_2
                # The tolerance in the docs is 1e-04
                checking_tol = 1e-2
                wire_checker = ShapeAnalysis_Wire(wire, face, checking_tol)
                wire_checker.Perform()
                closed_ok = wire_checker.CheckClosed(checking_tol)
                # if not closed_ok:
                #     print("Warning!! - Open wire")
                order_ok = True # HACK wire_checker.CheckOrder()
                if order_ok:
                    self.check_loop_order(output, wire, entity_mapper)
                    self.check_loop_orientation(wire, face)
                    self.check_orientations_of_2d_and_3d_curves(wire, face)
                else:
                    print("Warning!! - Found bad wire order!")

    def find_faces_for_body(output, body_index):
        face_indices = set()
        body_data = output["bodies"][body_index]
        for region_index in body_data["regions"]:
            region_data = output["regions"][region_index]
            for shell_index in region_data["shells"]:
                shell_data = output["shells"][shell_index]
                for face in shell_face["faces"]:
                    face_index = face["face_index"]
                    face_indices.add(face_index)
        return face_indices


    def check_face_list_for_body(
            self,
            output,
            body,
            entity_mapper
        ):
        body_index = entity_mapper.body_index(body)
        face_indices = self.find_faces_for_body(output, body_index)
        face_indices_from_body = set()
        top_exp = TopologyExplorer(body)
        faces = top_exp.faces()
        for face in faces:
            face_index = entity_mapper.face_index(face)
            face_indices.add(face_index)

        self.assertTrue(face_indices == face_indices_from_body)


    def check_edge_and_vertex_order(
            self,
            output, 
            edge,
            entity_mapper
        ):
        index_of_edge = entity_mapper.edge_index(edge)
        edge_data = output["edges"][index_of_edge]

        start_vertex = topexp.FirstVertex(edge)
        end_vertex = topexp.LastVertex(edge)

        start_vertex_index = entity_mapper.vertex_index(start_vertex)
        end_vertex_index = entity_mapper.vertex_index(end_vertex)

        start_vertex_from_output = edge_data["start_vertex"]
        end_vertex_from_output = edge_data["end_vertex"]
        
        self.assertTrue(start_vertex_index == start_vertex_from_output)
        self.assertTrue(end_vertex_index == end_vertex_from_output)


        # Here we want to check that the start and end vertices are
        # consistent with the start and end points on the edges
        # 3d curve

        curve = BRepAdaptor_Curve(edge)
        t_start = curve.FirstParameter()
        t_end = curve.LastParameter()
        start_point = curve.Value(t_start)
        end_point = curve.Value(t_end)

        start_point_from_vertex = BRep_Tool.Pnt(start_vertex)
        end_point_from_vertex = BRep_Tool.Pnt(end_vertex)

        bt = BRep_Tool()
        vertex_tolerance = bt.Tolerance(start_vertex) + bt.Tolerance(end_vertex)
        edge_tolerance = bt.Tolerance(edge)

        # Some extra tolerance just to be sure something is really wrong
        # We only want to see errors when we made a mistake with the
        # code and don't understand how Open Cascade works...
        extra_tolerance = 0.01 
        tolerance = vertex_tolerance + edge_tolerance + extra_tolerance

        vertices_consistent = start_point.IsEqual(start_point_from_vertex, tolerance) and \
                              end_point.IsEqual(end_point_from_vertex, tolerance)
        if not vertices_consistent:
            print(f"start_point {self.point_to_str(start_point)}")
            print(f"start_point_from_vertex {self.point_to_str(start_point_from_vertex)}")
            print(f"end_point {self.point_to_str(end_point)}")
            print(f"end_point_from_vertex {self.point_to_str(end_point_from_vertex)}")
        self.assertTrue(start_point.IsEqual(start_point_from_vertex, tolerance))
        self.assertTrue(end_point.IsEqual(end_point_from_vertex, tolerance))

    def check_edges_and_vertices(
            self,
            output, 
            body, 
            entity_mapper
        ):
        top_exp = TopologyExplorer(body)
        edges = top_exp.edges()
        for edge in edges:
            self.check_edge_and_vertex_order(
                output, 
                edge,
                entity_mapper
            )


    def check_output_for_body(
            self, 
            output, 
            body, 
            entity_mapper, 
            expect_manifold
        ):
        # Mesh the solid.   We want to use the mesh to
        # double check all the geometry is correct
        mesh = BRepMesh_IncrementalMesh(body, 0.9, False, 0.5, True)
        mesh.Perform()
        self.assertTrue(mesh.IsDone())

        body_index = entity_mapper.body_index(body)

        # To view a body set this to the index of the body
        # you would like to look at
        view_body = -1
        if body_index == view_body:
            self.debug_view_body(body)
            self.debug_save_mesh("results/debug_mesh.obj", body)

        # If we have non-manifold bodies then there are some 
        # some faces appear twice in the list of face-uses in the 
        # shell
        if expect_manifold:
            self.check_face_orientation_wrt_shell(output)
            self.check_face_orientations_against_triangles(
                output,
                body, 
                entity_mapper
            )


        self.check_order_of_all_loops(
            output,
            body,
            entity_mapper
        )
        self.check_edges_and_vertices(
            output, 
            body, 
            entity_mapper
        )

    def build_dict_for_bodies(self, bodies, expect_manifold):
        entity_mapper = EntityMapper(bodies)
        dict_builder = TopologyDictBuilder(entity_mapper)
        output = dict_builder.build_dict_for_bodies(bodies)
        for body in bodies:
            self.check_output_for_body(output, body, entity_mapper, expect_manifold)
        return output



    def build_dicts_for_file(self, pathname):
        print(f"Processing file {pathname}")
        bodies = self.load_bodies_from_file(pathname)
        output = self.build_dict_for_bodies(bodies, expect_manifold=True)
        output_dir = Path("./results")
        output_yaml = output_dir / f"{pathname.stem}.yaml"
        with open(output_yaml, "w") as fp:
            yaml.dump(output, fp, indent=2, width=79, default_flow_style=None)

        for index, body in enumerate(bodies):
            output_obj = output_dir / f"{pathname.stem}_body_{index}.obj"
            self.debug_save_mesh(output_obj, body)

    def test_build_dicts_for_files(self):
        self.build_dict_for_non_manifold_body()

        data_dir = Path("./data")
        extensions = ["stp", "step"]
        step_files = []
        for ext in extensions:
            files = [ f for f in data_dir.glob(f"**/*.{ext}")]
            step_files.extend(files)

        for file in step_files:
            self.build_dicts_for_file(file)

if __name__ == '__main__':
    unittest.main()