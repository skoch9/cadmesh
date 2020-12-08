

class TopologyDictBuilder:
    """
    A class which builds a python dictionary
    ready for export to the topology file
    """
    def __init__(self, entiy_mapper):
        """
        Construct from the entity mapper which gives
        us a mapping between the 
        """
        self.entity_mapper = entity_mapper


    def build_dict_for_body(self, body):
        """
        Build the dictionary for this body
        """
        top_exp = TopologyExplorer(body)
        body_dict = {
            "regions": self.build_regions_array(top_exp),
            "shells": self.build_shells_array(top_exp),
            "faces": self.build_faces_array(top_exp),
            "edges": self.build_edges_array(top_exp),
            "loops": self.build_loops_array(top_exp),
            "halfedges": self.build_halfedges_array(body)
        }

        return body_dict

    def build_regions_array(top_exp):
        regions_arr = []
        regions = top_exp.solids()
        for region in regions:
            regions_arr.append(self.build_region_data(top_exp, region))
        return regions_arr
        

    def build_shells_array(top_exp):
        shells_arr = []
        shells = top_exp.shells()
        for shell in shells:
            shells_arr.append(self.build_shell_data(top_exp, shell))
        return shells_arr

    def build_faces_array(top_exp):
        faces_arr = []
        faces = top_exp.faces()
        for face in facess:
            faces_arr.append(self.build_face_data(top_exp, face))
        return faces_arr

    def build_edges_array(top_exp):
        edges_arr = []
        edges = top_exp.edges()
        for edge in edges:
            edges_arr.append(self.build_edge_data(top_exp, edge))
        return edges_arr

    def build_loops_array(top_exp):
        loops_arr = []
        loops = top_exp.wires()
        for loop in loops:
            loops_arr.append(self.build_loop_data(top_exp, loop))
        return loops_arr

    def build_halfedges_array(body):
        halfedges_arr = []
        oriented_top_exp = TopologyExplorer(body, ignore_orientation=False)
        halfedges = oriented_top_exp.edges()
        for halfedge in halfedges:
            halfedges_arr.append(self.build_halfedge_data(halfedge))
        return halfedges_arr

    def build_region_data(self, top_exp, region):
        shell_indices = []
        shells = top_exp._loop_topo(TopoDS_Shell, region)
        for shell in shells:
            shell_indices.append(self.entity_mapper.shell_index(shell))
        return {
            "shells": shell_indices
        }

    def build_shell_data(self, top_exp, shell):
        face_list = []
        faces = self._loop_topo(TopAbs_FACE, shell)
        for face in faces:
            # It's not at all clear what this flag actually
            # does.   Are we finding the orientation of the
            # face wrt the surface or the face_use wrt the shell
            orientation = face.Orientation()
            assert orientation
            face_list.append(
                {
                    "face_index": self.entity_mapper.face_index(face),
                    "face_orientation_wrt_shell": True
                }
            )
        return {
            "faces": face_list
        }

    def build_face_data(self, top_exp, face):
        loop_indices = []
        loops = top_exp.wires_from_face(face)
        for loop in loops:
            loop_indices.append(self.entity_mapper.loop_index(loop))
        
        # It's not at all clear what this flag actually
        # does.   Are we finding the orientation of the
        # face wrt the surface or the face_use wrt the shell
        orientation = face.Orientation()
        assert orientation
        index_of_face = self.entity_mapper.face_index(face)
        
        return {
            "surface": index_of_face,
            "surface_orientation": orientation,
            "loops": loop_indices,
            "trim_domain": index_of_face
        }

    def build_edge_data(self, top_exp, edge):
        index_of_edge = self.entity_mapper.edge_index(edge)
        vertices = top_exp.vertices_from_edge(edge)
        vertex_indices = []
        occ_vertices = []
        for vertex in vertices:
            vertex_indices.append(self.entity_mapper.vertex_index(vertex))
            occ_vertices.append(vertex)
        
        assert len(vertex_indices) == 1 or len(vertex_indices) == 2
        start_vertex = vertex_indices[0]
        if len(vertex_indices) == 2:
            end_vertex = vertex_indices[1]
        else:
            end_vertex = vertex_indices[0]

        # Try to check we have the correct start and end vertices
        curve = BRepAdaptor_Curve(edge)
        t_start = curve.FirstParameter()
        t_end = curve.LastParameter()
        start_point = curve.Value(t_start)
        end_point = curve.Value(t_end)
        start_point_from_vertex = BRep_Tool.Pnt(occ_vertices[0])
        if len(occ_vertices) == 2:
            end_point_from_vertex = BRep_Tool.Pnt(occ_vertices[1])
        else:
            end_point_from_vertex = BRep_Tool.Pnt(occ_vertices[0])

        tolerance = 0.01
        assert start_point.IsEqual(start_point_from_vertex, tolerance)
        assert end_point.IsEqual(end_point_from_vertex, tolerance)

        return {
            "3dcurve": index_of_edge,
            "start_vertex": start_vertex,
            "end_vertex": end_vertex
        }


    def build_loop_data(self, top_exp, loop):
        wire_exp = WireExplorer(loop)
        halfedge_indices = []
        halfedges = wire_exp.ordered_edges()
        for halfedge in halfedges:
            halfedge_indices.append(self.entity_mapper.halfedge_index(halfedge))
        return {
            "halfedges": halfedge_indices
        }

    def build_halfedge_data(self, halfedge):
        orientation = halfedge.Orientation()
        mate = halfedge.Reversed()
        mates = []
        if self.entity_mapper.halfedge_exists(mate):
            mates.append(self.entity_mapper.halfedge_index(mate))
        
        edge_index = self.entity_mapper.edge_index(halfedge)
        hafedge_index = self.entity_mapper.halfedge_index(halfedge)

        return {
            "mates": mates,
            "2dcurve": hafedge_index,
            "edge": edge_index,
            "orientation_wrt_edge": orientation
        }