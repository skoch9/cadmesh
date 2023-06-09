import h5py
import meshio
import yaml
import os
from pathlib import Path
import numpy as np


def load_dict_from_yaml(path):
    with open(path, "r") as fp:
        return yaml.load(fp, Loader=yaml.CLoader)


def convert_dict_to_hdf5(data, group):
    for key, value in data.items():
        if isinstance(value, dict):
            subgroup = group.create_group(key)
            convert_dict_to_hdf5(value, subgroup)
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            if key == "faces" and all(
                isinstance(item, dict) and "face_index" in item and "face_orientation_wrt_shell" in item for item in
                value):
                array_data = np.array([(item['face_index'], item['face_orientation_wrt_shell']) for item in value],
                                      dtype=[('face_index', int), ('face_orientation_wrt_shell', bool)])
                group.create_dataset(key, data=array_data)
            else:
                subgroup = group.create_group(key)
                for i, item in enumerate(value):
                    if key == 'parts':
                        convert_dict_to_hdf5(item, subgroup.create_group('part_' + str(i + 1).zfill(3)))
                    else:
                        convert_dict_to_hdf5(item, subgroup.create_group(str(i).zfill(3)))
        elif isinstance(value, list) and all(isinstance(item, (int, float)) for item in value):
            if key == "bbox" and len(value) == 6:
                array_data = np.array(value).reshape((2, 3))
                group.create_dataset(key, data=array_data)
            elif key == "trim_domain" and len(value) == 4:
                array_data = np.array(value).reshape((2, 2))
                group.create_dataset(key, data=array_data)
            else:
                array_data = np.array(value)
                group.create_dataset(key, data=array_data)
        elif isinstance(value, list):
            if key == "poles" or key == "vertices":
                array_data = np.array(value)
                group.create_dataset(key, data=array_data)
            else:
                subgroup = group.create_group(key)
                for i, item in enumerate(value):
                    subgroup.create_dataset(str(i), data=np.array(item))
        else:
            group.create_dataset(key, data=value)


def convert_stat_to_hdf5(data, group):
    for key, value in data.items():
        if isinstance(value, dict):
            subgroup = group.create_group(key)
            convert_stat_to_hdf5(value, subgroup)
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            subgroup = group.create_group(key)
            for i, item in enumerate(value):
                convert_stat_to_hdf5(item, subgroup.create_group(str(i).zfill(3)))
        elif isinstance(value, list) and all(isinstance(item, (int, float)) for item in value):
            array_data = np.array(value)
            group.create_dataset(key, data=array_data)
        elif isinstance(value, list):
            if key == "parts" and isinstance(value[0], list) and group.name == "/stat":
                subgroup = group.create_group(key)
                for i, inner_list in enumerate(value):
                    subgroup_1 = subgroup.create_group('part_' + str(i + 1).zfill(3))
                    for j, item in enumerate(inner_list):
                        convert_stat_to_hdf5(item, subgroup_1.create_group(str(j).zfill(3)))
            else:
                subgroup = group.create_group(key)
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        convert_stat_to_hdf5(item, subgroup.create_group(str(i).zfill(3)))
                    else:
                        subgroup.create_dataset(str(i), data=np.array(item))
        else:
            group.create_dataset(key, data=value)


def convert_data_to_hdf5(geometry_data, topology_data, stat_data, meshPath, output_file):
    with h5py.File(output_file, 'w') as hdf:
        geometry_group = hdf.create_group('geometry')
        convert_dict_to_hdf5(geometry_data, geometry_group)

        topology_group = hdf.create_group('topology')
        convert_dict_to_hdf5(topology_data, topology_group)

        stat_group = hdf.create_group('stat')
        convert_stat_to_hdf5(stat_data, stat_group)

        mesh_group = hdf.create_group('mesh')
        for index, mesh_file in enumerate(sorted(os.listdir(meshPath))):
            if mesh_file.endswith(".obj"):
                mesh = meshio.read(os.path.join(meshPath, mesh_file))
                points = mesh.points
                cells = mesh.cells
                cell_data = mesh.cell_data

                mesh_subgroup = mesh_group.create_group(str(index).zfill(3))
                mesh_subgroup.create_dataset('points', data=points)
                for cell in cells:
                    cell_type = cell.type
                    cell_indices = cell.data
                    mesh_subgroup.create_dataset(cell_type, data=cell_indices)

                for data_key, data_value in cell_data.items():
                    if data_key == "obj:group_ids":
                        data_key = "group_ids"
                    if isinstance(data_value, list):
                        mesh_subgroup.create_dataset(data_key, data=data_value)
                    else:
                        subgroup = mesh_subgroup.create_group(data_key)
                        for field_key, field_value in data_value.items():
                            subgroup.create_dataset(field_key, data=field_value)
