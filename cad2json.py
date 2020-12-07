
import json
from pathlib import Path
import argparse
from collections import OrderedDict
import unittest
import yaml
import sys

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.TopExp import TopExp_Explorer, topexp_MapShapesAndAncestors
from OCC.Core.TopoDS import (topods, TopoDS_Wire, TopoDS_Vertex, TopoDS_Edge,
                             TopoDS_Face, TopoDS_Shell, TopoDS_Solid, TopoDS_Shape,
                             TopoDS_Compound, TopoDS_CompSolid, topods_Edge,
                             topods_Vertex, TopoDS_Iterator)
from OCC.Extend.DataExchange import read_step_file_with_names_colors

from OCC.Core.BRepAdaptor import BRepAdaptor_Surface

from OCC.Core.Standard import *

from OCC.Core.TopAbs import TopAbs_EDGE

from OCCUtils.edge import Edge
from OCCUtils.vertex import Vertex
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopExp import topexp

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool,
                              XCAFDoc_ColorGen)
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
#from OCC.Core.IFSelect import IFSelect_RetDone
#from OCC.Core.Quantity import Quantity_Color, Quantity_TypeOfColor
from OCC.Core.TDF import TDF_LabelSequence
from  OCC.Core.TDF import *
from OCC.Core.XSControl import XSControl_WorkSession
from OCC.Core.STEPControl import STEPControl_AsIs
#from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDF import TDF_Attribute

intmax = 2147483647
surf_map = {0: "Plane", 1: "Cylinder", 2: "Cone", 3: "Sphere", 4: "Torus", 5: "Bezier", 6: "BSpline", 7: "Revolution", 8: "Extrusion", 9: "Offset", 10: "Other"}

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=str, help="The STEP file to convert")
parser.add_argument("--output_folder", type=str, help="The output folder for the json data")
args = parser.parse_args()

def read_step_file(filename, return_as_shapes=False, verbosity=False):
    assert filename.exists()
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(str(filename))
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


    
def test_read_step_file_with_attributes(pathname)-> None:
    ''' Reads the previous step file '''
    # https://github.com/tpaviot/pythonocc-core/blob/bb5fdd1ec108bc6f5c773f7088453eb99683290f/src/Extend/DataExchange.py
    # create an handle to a document
    doc = TDocStd_Document(TCollection_ExtendedString("pythonocc-doc"))
    # Get root assembly
    shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
    color_tool = XCAFDoc_DocumentTool.ColorTool(doc.Main())
    step_reader = STEPCAFControl_Reader()
    step_reader.SetColorMode(True)
    step_reader.SetLayerMode(True)
    step_reader.SetNameMode(True)
    step_reader.SetMatMode(True)
    status = step_reader.ReadFile(str(pathname))
    if status == IFSelect_RetDone:
        step_reader.Transfer(doc)

    labels = TDF_LabelSequence()
    #color_labels = TDF_LabelSequence()

    shape_tool.GetFreeShapes(labels)

    print(f"labels length {labels.Length()}")
    sub_shapes_labels = TDF_LabelSequence()

    shape_tool.GetSubShapes(labels.Value(1), sub_shapes_labels)
    print(f"sub_shapes_labels length {sub_shapes_labels.Length()}")
    all_indices = set()
    for i in range(sub_shapes_labels.Length()):
        label_sub = sub_shapes_labels.Value(i+1)
        #print(label_sub.DumpToString())
        #print(f"label_sub.GetLabelName() {label_sub.GetLabelName()}")
        shape_sub = shape_tool.GetShape(label_sub)
        c = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB) 
        color_tool.GetColor(label_sub, 0, c)
        color_tool.GetColor(label_sub, 1, c)
        color_tool.GetColor(label_sub, 2, c)
        r = int(c.Red()*256)
        g = int(c.Green()*256*256)
        b = int(c.Blue()*256*256*256)
        recovered_index = r+g+b
        all_indices.add(recovered_index)

        # print(f"Colour red {c.Red()}")
        # shape_type = shape_sub.ShapeType()
        # print(shape_type)
        # surf = BRepAdaptor_Surface(shape_sub)
        # surf_type = surf.GetType()
        # type_str = surf_map[surf_type]
        # print(f"Debug face  type {type_str}")

        # if shape_tool.IsReference(label):
        #     #print("\n########  reference label :", label)
        #     label_reference = TDF_Label()
        #     shape_tool.GetReferredShape(label, label_reference)

    for i in range(len(all_indices)):
        assert i in all_indices

    #id = TDataStd_Name.GetID()

    #color_tool.GetColors(color_labels)
    #print(f"color_labels.Length() {color_labels.Length()}")


    #label_shp = labels.Value(1)

    #name = label_shp.GetLabelName()

def ordered_dict_representer(self, value):  # can be a lambda if that's what you prefer
    return self.represent_mapping('tag:yaml.org,2002:map', value.items())

def get_hash(ent):
    return ent.HashCode(intmax)

def find_face_index(face, face_map):
    h = get_hash(face)
    if not h in face_map:
        return None
    return face_map[h]["face_index"]

def find_parent_edge_index(coedge, edge_map):
    h = get_hash(coedge)
    if not h in edge_map:
        return None
    return edge_map[h]["edge_index"]

def find_partner_coedge_index(coedge, coedge_map):
    h = get_hash(coedge)
    orientation = coedge.Orientation()
    other_orientation = not orientation
    tup = (h, other_orientation)
    if not tup in coedge_map:
        # We have an open edge
        return None
    partner_index = coedge_map[tup]["coedge_index"]
    return partner_index

def find_loop_index(loop, loop_map):
    h = get_hash(loop)
    if not h in loop_map:
        return None
    return loop_map[h]["loop_index"]

def find_coedge_index(coedge, coedge_map):
    h = get_hash(coedge)
    orientation = coedge.Orientation()
    tup = (h, orientation)
    if not tup in coedge_map:
        return None
    return coedge_map[tup]["coedge_index"]

def has_coedge(edge, orientation, coedge_map):
    h = get_hash(edge)
    tup = (h, orientation)
    return tup in coedge_map

def find_coedge_index_from_edge(edge, orientation, coedge_map):
    h = get_hash(edge)
    tup = (h, orientation)
    assert tup in coedge_map
    return coedge_map[tup]["coedge_index"]

def find_vertex_index(vertex, vertex_map):
    h = get_hash(vertex)
    assert h in vertex_map
    return vertex_map[h]["vertex_index"]

def add_face_to_map(face, face_map):
    h = get_hash(face)
    if h in face_map:
        return
    face_map[h] = {
        "face": face,
        "face_index": len(face_map)
    }

def add_loop_to_map(loop, loop_map):
    h = get_hash(loop)
    if h in loop_map:
        return
    loop_map[h] = {
        "loop": loop,
        "loop_index": len(loop_map)
    }

def add_parent_edge_to_map(coedge, edge_map):
    h = get_hash(coedge)
    if h in edge_map:
        return
    edge_map[h] = {
        "random_coedge": coedge,
        "edge_index": len(edge_map)
    }

def add_coedge_to_map(coedge, coedge_map):
    h = get_hash(coedge)
    orientation = coedge.Orientation()
    tup = (h, orientation)
    coedge_map[tup] = {
        "coedge": coedge,
        "coedge_index": len(coedge_map)
    }

def add_vertex_to_map(vertex, vertex_map):
    h = get_hash(vertex)
    if h in vertex_map:
        return
    vertex_map[h] = {
        "vertex": vertex,
        "vertex_index": len(vertex_map)
    }

class TopologyChecker(unittest.TestCase):

    def check_coedge_consistency(self, coedge_index, topology):
        # Loop is checked by check_loop_consistency()
        # Edge is checked by check_edge_consistency()
        coedges = topology["coedges"]
        coedge = coedges[coedge_index]

        next_coedge_index = coedge["next"]
        next_coedge =  coedges[next_coedge_index]
        self.assertEqual(coedge_index, next_coedge["previous"])

        previous_coedge_index = coedge["previous"]
        previous_coedge = coedges[previous_coedge_index]
        self.assertEqual(coedge_index, previous_coedge["next"])

        if "partner" in coedge:
            partner_coedge_index = coedge["partner"]
            partner_coedge = coedges[partner_coedge_index]
            self.assertEqual(coedge_index, partner_coedge["partner"])

    def check_loop_consistency(self, loop_index, topology):
        faces = topology["faces"]
        loops = topology["loops"]
        coedges = topology["coedges"]
        loop = loops[loop_index]
        for coedge_index in loop["coedges"]:
            coedge = coedges[coedge_index]
            self.assertEqual(loop_index, coedge["loop"])
        face_index = loop["face"]
        face = faces[face_index]
        found = False
        for loop_index_of_face in face["loops"]:
            if loop_index_of_face == loop_index:
                found = True
                break
        self.assertTrue(found)


    def check_edge_consistency(self, edge_index, topology):
        edges = topology["edges"]
        coedges = topology["coedges"]
        edge = edges[edge_index]
        coedge_list = []
        if "left_coedge" in edge:
            coedge_list.append(edge["left_coedge"])
        if "right_coedge" in edge:
            coedge_list.append(edge["right_coedge"])
        for coedge_index in coedge_list:
            coedge = coedges[coedge_index]
            self.assertEqual(edge_index, coedge["edge"])

    def check_face_consistency(self, face_index, topology):
        faces = topology["faces"]
        loops = topology["loops"]
        face = faces[face_index]
        for loop_index in face["loops"]:
            loop = loops[loop_index]
            self.assertEqual(face_index, loop["face"])


    def check_topology_consistency(self, topology):

        for i in range(len(topology["faces"])):
            self.check_face_consistency(i, topology)

        for i in range(len(topology["edges"])):
            self.check_edge_consistency(i, topology)

        for i in range(len(topology["loops"])):
            self.check_loop_consistency(i, topology)
                
        for i in range(len(topology["coedges"])):
            self.check_coedge_consistency(i, topology)



def convert_step_file(input_file, output_pathname):
    bodies = read_step_file(input_file)
    for body in bodies:

        face_map = OrderedDict()
        loop_map = OrderedDict()
        edge_map = OrderedDict()
        coedge_map = OrderedDict()
        vertex_map = OrderedDict()


        top_exp = TopologyExplorer(body)
        bt = BRep_Tool()

        # Loop over all the faces
        faces = top_exp.faces()
        for fci, face in enumerate(faces):
            add_face_to_map(face, face_map)
            surf = BRepAdaptor_Surface(face)
            surf_type = surf.GetType()
            type_str = surf_map[surf_type]
            print(f"Debug face {fci} type {type_str}")

        # Loop over all the edges
        edges = top_exp.edges()
        for edge_index, edge in enumerate(edges):
            add_parent_edge_to_map(edge, edge_map)

        # Loop over all the coedges.  Here we need to switch off the
        # ignore_orientation flag so that we get each coedge
        oriented_top_exp = TopologyExplorer(body, ignore_orientation=False)
        coedges = oriented_top_exp.edges()
        for coedge in coedges:
            add_coedge_to_map(coedge, coedge_map)

        # Loop over all the loops
        loops = top_exp.wires()
        for loop in loops:
            add_loop_to_map(loop, loop_map)


        vertices = top_exp.vertices()
        for vertex in vertices:
            add_vertex_to_map(vertex, vertex_map)


        # Now that we have maps set up to go from the entities to
        # the indices we plan to use we can start to query the structure
        # and fill in the data
        topology = {}
        top_face_list = []
        top_edge_list = []
        top_loop_list = []
        top_coedge_list = []
        top_coedge_sparse = {}
        top_vertex_list = []

        for fci, face_hash in enumerate(face_map):
            face = face_map[face_hash]
            face_index = find_face_index(face["face"], face_map)
            assert fci == face_index

            loops = top_exp.wires_from_face(face["face"])
            loop_list = []
            for loop in loops:
                loop_index = find_loop_index(loop, loop_map)
                loop_list.append(loop_index)
            top_face_list.append(
                {
                    "loops": loop_list
                }
            )

        for loop_index, loop_hash in enumerate(loop_map):
            loop_struct = loop_map[loop_hash]
            assert loop_struct["loop_index"] == loop_index
            loop = loop_struct["loop"]
            faces = top_exp.faces_from_wire(loop)
            face_index = -1
            for face in faces:
                assert face_index == -1, "One loop has many parent faces??"
                face_index = find_face_index(face, face_map)


            edge_list = []
            coedge_list = []
            coedge_sense_list = []
            partner_list = []
            coedges_in_loop = top_exp.ordered_edges_from_wire(loop)
            vertices_in_loop = top_exp.ordered_vertices_from_wire(loop)
            for coedge, vertex in zip(coedges_in_loop, vertices_in_loop):
                coedge_index = find_coedge_index(coedge, coedge_map)
                coedge_list.append(coedge_index)
                coedge_sense_list.append(coedge.Orientation())

                vertex_index = find_vertex_index(vertex, vertex_map)

                edge_index = find_parent_edge_index(coedge, edge_map)
                edge_list.append(edge_index)

                # Now find the partner
                partner_index = find_partner_coedge_index(coedge, coedge_map)
                partner_list.append(partner_index)

            top_loop_list.append(
                {
                    "coedges": coedge_list,
                    "face": face_index
                }
            )


            # At this point we have all the indices we need to build
            # the structure
            for index, coedge_index in enumerate(coedge_list):
                prev_coedge = coedge_list[-1]
                next_coedge = coedge_list[0]
                if index > 0:
                    prev_coedge = coedge_list[index-1]
                if index+1 < len(coedge_list):
                    next_coedge = coedge_list[index+1]
                top_coedge_sparse[coedge_index] = {
                    "loop": loop_index,
                    "edge": edge_list[index],
                    "is_left_coedge":  coedge_sense_list[index],
                    "next": next_coedge,
                    "previous": prev_coedge
                }
                # Cope when we have an open edge.  i.e. no partner coedge
                if partner_list[index] is not None:
                    top_coedge_sparse[coedge_index]["partner"] = partner_list[index]

        for tup in coedge_map:
            coedge_struct = coedge_map[tup]
            coedge_index = coedge_struct["coedge_index"]
            top_coedge_list.append(top_coedge_sparse[coedge_index])

        for eci, edge_struct in enumerate(edge_map.values()):
            edge = edge_struct["random_coedge"]
            edge_index = find_parent_edge_index(edge, edge_map)
            assert edge_index == eci

            edge_struct = {}
            if has_coedge(edge, True, coedge_map):
                edge_struct["left_coedge"] = find_coedge_index_from_edge(edge, True, coedge_map)

            if has_coedge(edge, False, coedge_map):
                edge_struct["right_coedge"] = find_coedge_index_from_edge(edge, False, coedge_map)
            
            e = Edge(edge)
            start = e.first_vertex()
            end = e.last_vertex()
            edge_struct["start_vertex"] = find_vertex_index(start, vertex_map)
            edge_struct["end_vertex"] = find_vertex_index(end, vertex_map)
            top_edge_list.append(edge_struct)

        top_vertex_list = []
        for vertex_struct in vertex_map.values():
            pnt = bt.Pnt(vertex_struct["vertex"])
            top_vertex_list.append(-999)
            print(f"Vertex position: ({pnt.X()}, {pnt.Y()}, {pnt.Z()})")

        topology["faces"] = top_face_list
        topology["edges"] = top_edge_list
        topology["loops"] = top_loop_list
        topology["coedges"] = top_coedge_list

        checker = TopologyChecker()
        checker.check_topology_consistency(topology)


        simple_top = {}
        simple_face_list = []
        for face in top_face_list:
            simple_face_list.append(
                { 
                    "surface": -1,
                    "surface_orientation": True,
                    "loops": face["loops"]
                }
            )
        simple_top["faces"] = simple_face_list

        simple_edge_list = []
        for edge in top_edge_list:
            edge_struct = {
                "halfedges": []
            }
            edge_struct["3dcurve"] = -1
            if "left_coedge" in edge:
                edge_struct["halfedges"].append(edge["left_coedge"])
            if "right_coedge" in edge:
                edge_struct["halfedges"].append(edge["right_coedge"])
            edge_struct["start_vertex"] = edge["start_vertex"]
            edge_struct["end_vertex"] = edge["end_vertex"]
            simple_edge_list.append(edge_struct)
        simple_top["edges"] = simple_edge_list

        simple_loop_list = []
        for loop in top_loop_list:
            simple_loop = {}
            simple_loop["halfedges"] = loop["coedges"]
            simple_loop_list.append(simple_loop)

        simple_top["loops"] = simple_loop_list

        simple_halfedge_list = []
        for halfedge in top_coedge_list:
            simple_halfedge_list.append(
                {
                    "mates": [halfedge["partner"]],
                    "2dcurve": 890,
                    "edge": 123,
                    "orientation_wrt_edge": True
                }
            )
        simple_top["halfedges"] = simple_halfedge_list
        simple_top["vertices"] = top_vertex_list


        shells = {
            "faces": [
                {
                    "face_index": 1,
                    "face_orientation_wrt_shell": True
                },
                {
                    "face_index": 2,
                    "face_orientation_wrt_shell": True
                },
                {
                    "face_index": 3,
                    "face_orientation_wrt_shell": True
                },
            ]
        }
        simple_top["shells"] = shells

        data = {
            "topo": simple_top
        }

        with open(output_pathname, 'w', encoding='utf8') as fp:
            json.dump(data, fp, indent=4, ensure_ascii=False, sort_keys=False)

        yaml_pathname = output_pathname.with_suffix(".yaml")
        yaml.default_flow_style = True
        yaml.width = 5
        yaml.add_representer(dict, ordered_dict_representer)
        with open(yaml_pathname, 'w') as yaml_file:
            yaml.dump(data, yaml_file, indent=2, width=79, default_flow_style=None)


if __name__ == "__main__":
    input_file = Path(args.input)
    output_folder = Path(args.output_folder)

    if not input_file.exists():
        print(f"The STEP file {input_file} doesn't exist")
        sys.exit(1)

    if not output_folder.exists():
        output_folder.mkdir()
    
    output_pathname = (output_folder / (input_file.stem)).with_suffix(".json")

    #read_step_file_with_names_colors(str(input_file))
    test_read_step_file_with_attributes(input_file)
    #convert_step_file(input_file, output_pathname)