from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
import numpy as np
from OCC.Core.TopExp import topexp
from OCC.Core.TopAbs import (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE, TopAbs_WIRE,
                             TopAbs_SHELL, TopAbs_SOLID, TopAbs_COMPOUND,
                             TopAbs_COMPSOLID)
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh




class MeshBuilder:
    def __init__(self, entity_mapper, logger):
        self.entity_mapper = entity_mapper
        self.logger = logger
        
    def create_surface_meshes(self, part):
        top_exp = TopologyExplorer(part, ignore_orientation=False)
        
        mesh = BRepMesh_IncrementalMesh(part, 0.01, True, 0.1, True)
        #mesh.SetParallel(True)
        mesh.SetShape(part)
        mesh.Perform()
        assert mesh.IsDone()
        
        if self.logger:
            self.logger.info("Meshing body: Done")
        nr_faces = top_exp.number_of_faces()
        meshes = [None]*nr_faces
        # Iterate over faces
        faces = top_exp.faces()
        for face in faces:
            expected_face_index = self.entity_mapper.face_index(face)

            # TODO add proper meshing code
            try:
                verts, tris, _, _, _ = self.__process_face(face)
                assert meshes[expected_face_index] == None
                meshes[expected_face_index] = {"vertices": np.array(verts), "faces": np.array(tris)}
            except Exception as e:
                #print("Conversion failed, processing unconverted")
                #print(e.args.split("\n"))
                self.logger.error("Mesh processing error: %s"%str(e))
                meshes[expected_face_index] = {"vertices": np.array([]), "faces": np.array([])}
                continue

        return meshes
    

    def __process_face(self, face, first_vertex=0):
        #print("Face %i: ShapeType: %s, Closed: %s, Orientable: %s, Orientation: %s"%(face_idx, face.ShapeType(), face.Closed(), face.Orientable(), face.Orientation()))
        #surf = BRepAdaptor_Surface(face)
        face_orientation_wrt_surface_normal = face.Orientation()

        # Get mesh normals
        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        mesh = brep_tool.Triangulation(face, location)
        verts = []
        tris = []
        normals = []
        surf_normals = []
        centroids = []
        if mesh != None:
            # Get vertices
            num_vertices = mesh.NbNodes()
            for i in range(1, num_vertices+1):
                verts.append(list(mesh.Node(i).Coord()))
            verts = np.array(verts)

            # Get faces
            num_tris = mesh.NbTriangles()
            for i in range(1, num_tris+1):
                index1, index2, index3 = mesh.Triangle(i).Get()
                if face_orientation_wrt_surface_normal == 0:
                    tris.append([first_vertex + index1 - 1, first_vertex + index2 - 1, first_vertex + index3 - 1])
                elif face_orientation_wrt_surface_normal == 1:
                    tris.append([first_vertex + index3 - 1, first_vertex + index2 - 1, first_vertex + index1 - 1])
                else:
                    print("Broken face orientation", face_orientation_wrt_surface_normal)

    #             # Get mesh normals
    #             pt1 = verts[index1-1]
    #             pt2 = verts[index2-1]
    #             pt3 = verts[index3-1]
    #             centroid = (pt1 + pt2 + pt3)/3
    #             centroids.append(centroid)
    #             normal = np.cross(pt2-pt1, pt3-pt1)
    #             norm = np.linalg.norm(normal)
    #             if not np.isclose(norm, 0):
    #                 normal /= norm
    #             if face_orientation_wrt_surface_normal == 1:
    #                 normal = -normal
    #             normals.append(normal)

    #             # Get surface normals
    #             uv1 = convert_vec_to_np(mesh.UVNode(index1))
    #             uv2 = convert_vec_to_np(mesh.UVNode(index2))
    #             uv3 = convert_vec_to_np(mesh.UVNode(index3))
    #             #print(uv1, uv2, uv3)
    #             uvc = (uv1 + uv2 + uv3) / 3
    #             #print(uvc)
    #             uvc = gp_Pnt2d(uvc[0], uvc[1])
    #             surface_normal = get_surface_normal(uvc, surf)
    #             if face_orientation_wrt_surface_normal == 1:
    #                 surface_normal = -surface_normal
    #             surf_normals.append(surface_normal)

        return verts, tris, normals, centroids, surf_normals





