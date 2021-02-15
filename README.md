# Cadmesh

Topology, geometry and mesh extraction from CAD files. 


# Installation

conda env create -f environment.yml



## EntityMapper

The entity mapper is used to translate between Open Cascade Topo_DS entities and the indices which will be written into the file.   The entity mapper uses the Open Cascade hash value as a unique identifier to each Topo_DS.

A simple example of usage

```
entity_mapper = EntityMapper(shapes)
for shape in shapes:
    top_exp = TopologyExplorer(shape)
    faces = top_exp.faces()
    for face in faces:
        face_index_for_file = entity_mapper.face_index(face)
```

In the special case of edges, two different indices can be enquired.   

The index of an edge ignoring the Orientation flag can be found using
```
edge_index = entity_mapper.edge_index(edge)
```

The index of an edge taking account of its orientation can be found like this
```
halfedge_index = entity_mapper.halfedge_index(edge)
```

## TopologyDictBuilder

This class can be used to create the python dictionary which we can serialize to generate the topology file.  It uses the entity mapper to define the indices of each Open Cascade entity.   An example of usage

```
entity_mapper = EntityMapper(shapes)
builder = TopologyDictBuilder(shapes)
body_dict = builder.build_dict_for_bodies(shape)
```

## topology_utils.orientation_to_sense()

Utility to convert Open Cascade TopAbs_Orientation enum to a kind of "sense" flag.
TopAbs_FORWARD -> True
TopAbs_REVERSED -> False
All other values trigger an assert.

## utest_topology_dict_builder.py

This contains tests for the functionality in the TopologyDictBuilder

## New test data

![image](https://user-images.githubusercontent.com/17026486/102238227-6bb30e00-3eed-11eb-8969-89d2df760697.png)

The AVoid.stp test example contains an internal void inside the block
![image](https://user-images.githubusercontent.com/17026486/102238376-956c3500-3eed-11eb-9a5e-631c61b68465.png)

