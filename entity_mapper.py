# PythonOCC
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.TopoDS import TopoDS_Shape


# CAD
import topology_utils as topology_utils

# Open Cascade needs to know the maximum size of the hash value
# used to reference each entity.  We define this to be the
# max value for an int
intmax = 2147483647

class EntityMapper:
    """
    This class allows us to map between OpenCascade entities 
    and the indices which we will write into the topology file
    """
    def __init__(self, bodies):
        """
        Create a mapper object for this list of bodies
        """

        # Create the dictionaries which will map the
        # PythonOCC hash values to the indices used in 
        # the topology file
        self.body_map = dict()
        self.lump_map = dict()
        self.shell_map = dict()
        self.face_map = dict()
        self.loop_map = dict()
        self.edge_map = dict()
        self.halfedge_map = dict()
        self.vertex_map = dict()

        # In the non-manifold case some shells will return 
        # both "face-uses".  i.e. faces with two different
        # orientations depending on which shell they are 
        # used by.  Here we record the orientations of the 
        # "primary" faces which the topology explorer returns
        # with "ignore_orientation" set true
        self.primary_face_orientations_map = dict()
        
        # Create list if only one body is handed in
        if isinstance(bodies, TopoDS_Shape): 
            bodies = [bodies]

        for body in bodies:
            top_exp = TopologyExplorer(body)

            # Build the index lookup tables
            self.append_body(body)
            self.append_lumps(top_exp)
            self.append_shells(top_exp)
            self.append_faces(top_exp)
            self.append_loops(top_exp)
            self.append_edges(top_exp)
            self.append_halfedges(body)
            self.append_vertices(top_exp)

            # Build the orientations of the primary faces
            self.build_primary_face_orientations_map(top_exp)


    # The following functions are the interface for 
    # users of the class to access the indices
    # which will reptresent the Open Cascade entities
    
    def get_nr_of_edges(self):
        return len(self.edge_map.keys())

    def get_nr_of_surfaces(self):
        return len(self.face_map.keys())

    def body_index(self, body):
        """
        Find the index of a body
        """
        h = self.get_hash(body)
        return self.body_map[h]

    def lump_index(self, lump):
        """
        Find the index of a lump
        """
        h = self.get_hash(lump)
        return self.lump_map[h]

    def shell_index(self, shell):
        """
        Find the index of a shell
        """
        h = self.get_hash(shell)
        return self.shell_map[h]

    def face_index(self, face):
        """
        Find the index of a face
        """
        h = self.get_hash(face)
        return self.face_map[h]

    def loop_index(self, loop):
        """
        Find the index of a loop
        """
        h = self.get_hash(loop)
        return self.loop_map[h]

    def edge_index(self, edge):
        """
        Find the index of an edge
        """
        h = self.get_hash(edge)
        return self.edge_map[h]
    
    def halfedge_index(self, halfedge):
        """
        Find the index of a halfedge
        """
        h = self.get_hash(halfedge)
        orientation = halfedge.Orientation()
        tup = (h,orientation)
        return self.halfedge_map[tup]

    def halfedge_exists(self, halfedge):
        h = self.get_hash(halfedge)
        orientation = halfedge.Orientation()
        tup = (h,orientation)
        return tup in self.halfedge_map

    def vertex_index(self, vertex):
        """
        Find the index of a vertex
        """
        h = self.get_hash(vertex)
        return self.vertex_map[h]

    def primary_face_orientation(self, face):
        h = self.get_hash(face)
        return self.primary_face_orientations_map[h]


    # These functions are used internally to build the map

    def get_hash(self, ent):
        return ent.HashCode(intmax)

    def append_body(self, body):
        h = self.get_hash(body)
        index = len(self.body_map)
        assert not h in self.body_map
        self.body_map[h] = index

    def append_lumps(self, top_exp):
        lumps = top_exp.solids()
        for lump in lumps:
            self.append_lump(lump)

    def append_lump(self, lump):
        h = self.get_hash(lump)
        index = len(self.lump_map)
        assert not h in self.lump_map
        self.lump_map[h] = index

    def append_shells(self, top_exp):
        shells = top_exp.shells()
        for shell in shells:
            self.append_shell(shell)

    def append_shell(self, shell):
        h = self.get_hash(shell)
        index = len(self.shell_map)
        assert not h in self.shell_map
        self.shell_map[h] = index

    def append_faces(self, top_exp):
        faces = top_exp.faces()
        for face in faces:
            self.append_face(face)

    def append_face(self, face):
        h = self.get_hash(face)
        index = len(self.face_map)
        assert not h in self.face_map
        self.face_map[h] = index

    def append_loops(self, top_exp):
        loops = top_exp.wires()
        for loop in loops:
            self.append_loop(loop)

    def append_loop(self, loop):
        h = self.get_hash(loop)
        index = len(self.loop_map)
        assert not h in self.loop_map
        self.loop_map[h] = index

    def append_edges(self, top_exp):
        edges = top_exp.edges()
        for edge in edges:
            self.append_edge(edge)

    def append_edge(self, edge):
        h = self.get_hash(edge)
        index = len(self.edge_map)
        assert not h in self.edge_map
        self.edge_map[h] = index

    def append_halfedges(self, body):
        oriented_top_exp = TopologyExplorer(body, ignore_orientation=False)
        halfedges = oriented_top_exp.edges()
        for halfedge in halfedges:
            self.append_halfedge(halfedge)

    def append_halfedge(self, halfedge):
        h = self.get_hash(halfedge)
        orientation = halfedge.Orientation()
        tup = (h, orientation)
        index = len(self.halfedge_map)
        if not tup in self.halfedge_map:
            self.halfedge_map[tup] = index

    def append_vertices(self, top_exp):
        vertices = top_exp.vertices()
        for vertex in vertices:
            self.append_vertex(vertex)

    def append_vertex(self, vertex):
        h = self.get_hash(vertex)
        index = len(self.vertex_map)
        assert not h in self.vertex_map
        self.vertex_map[h] = index

    def build_primary_face_orientations_map(self, top_exp):
        faces = top_exp.faces()
        for face in faces:
            self.append_primary_face(face)

    def append_primary_face(self, face):
        h = self.get_hash(face)
        orientation = topology_utils.orientation_to_sense(face.Orientation())
        assert not h in self.primary_face_orientations_map
        self.primary_face_orientations_map[h] = orientation

