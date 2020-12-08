from collections import OrderedDict
from OCC.Extend.TopologyUtils import TopologyExplorer

# Open Cascade needs to know the maximum size of the hash value
# used to reference each entity.  We define this to be the
# max value for an int
intmax = 2147483647

class EntityMapper:
    """
    This class allows us to map between OpenCascade entities 
    and the indices which we will write into the topology file
    """
    def __init__(self, body):
        """
        Create a mapper object for this body
        """

        # Create the dictionaries which will map the
        # PythonOCC hash values to the indices used in 
        # the topology file
        self.region_map = OrderedDict()
        self.shell_map = OrderedDict()
        self.face_map = OrderedDict()
        self.loop_map = OrderedDict()
        self.edge_map = OrderedDict()
        self.halfedge_map = OrderedDict()
        self.vertex_map = OrderedDict()


        top_exp = TopologyExplorer(body)

        self.append_regions(top_exp)
        self.append_shells(top_exp)
        self.append_faces(top_exp)
        self.append_loops(top_exp)
        self.append_edges(top_exp)
        self.append_halfedges(body)
        self.append_vertices(top_exp)


    # The following functions are the interface for 
    # users of the class to access the indices
    # which will reptresent the Open Cascade entities

    def region_index(self, region):
        """
        Find the index of a region
        """
        h = self.get_hash(region)
        return self.region_map[h]

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
        h = self.get_index(face)
        return self.face_map[face]

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
        assert orientation == TopAbs_FORWARD or orientation == TopAbs_REVERSED
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



    # These functions are used internally to build the map

    def get_hash(self, ent):
        return ent.HashCode(intmax)

    def append_regions(self, top_exp):
        regions = top_exp.solids()
        for region in regions:
            self.append_region(region)

    def append_region(self, region):
        h = self.get_hash(region)
        index = len(self.region_map)
        self.region_map[h] = index

    def append_shells(self, top_exp):
        shells = top_exp.shells()
        for shell in shells:
            self.append_shell(shell)

    def append_shell(self, shell):
        h = self.get_hash(shell)
        index = len(self.shell_map)
        self.shell_map[h] = index

    def append_faces(self, top_exp):
        faces = top_exp.face()
        for face in faces:
            self.append_face(face)

    def append_face(self, face):
        h = self.get_hash(face)
        index = len(self.face_map)
        self.face_map[h] = index

    def append_loops(self, top_exp):
        loops = top_exp.wires()
        for loop in loops:
            self.append_loop(loop)

    def append_loop(self, loop):
        h = self.get_hash(loop)
        index = len(self.loop_map)
        self.loop_map[h] = index

    def append_edges(self, top_exp):
        edges = top_exp.edges()
        for edge in edges:
            self.append_edge(edge)

    def append_edge(self, edge):
        h = self.get_hash(edge)
        index = len(self.edge_map)
        self.edge_map[h] = index

    def append_halfedges(self, body):
        oriented_top_exp = TopologyExplorer(body, ignore_orientation=False)
        halfedges = oriented_top_exp.edges()
        for halfedge in halfedges:
            self.append_halfedge(halfedge)

    def append_halfedge(self, halfedge):
        h = get_hash(coedge)
        orientation = coedge.Orientation()
        tup = (h, orientation)
        index = len(self.halfedge_map)
        self.halfedge_map[tup] = index

    def append_vertices(self, top_exp):
        vertices = top_exp.vertices()
        for vertex in vertices:
            self.append_vertex(vertex)

    def append_vertex(self, vertex):



