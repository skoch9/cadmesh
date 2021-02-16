from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCCUtils.Topology import Topo, dumpTopology
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pnt2d
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
from OCC.Core.BRepTools import breptools_UVBounds
from OCC.Core.ShapeFix import ShapeFix_Shape as _ShapeFix_Shape
import logging
import os
import igl


from .entity_mapper import EntityMapper
from .geometry_dict_builder import GeometryDictBuilder
from .topology_dict_builder import TopologyDictBuilder
from .mesh_builder import MeshBuilder
from .geometry_utils import load_parts_from_step_file, write_dictionary_to_file



def setup_logger(name, log_file, formatter, level=logging.INFO, reset=True):
    """To setup as many loggers as you want"""
    if os.path.exists(log_file) and reset:
        os.remove(log_file)
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


class StepProcessor:
    """
    Processor class for step files. Takes as input a step file, an entity_mapper, a topology and geometry dict builder and a mesh processor.
    """
    def __init__(self, step_file, output_dir, log_dir, entity_mapper=EntityMapper, topology_builder=TopologyDictBuilder, geometry_builder=GeometryDictBuilder, mesh_builder=MeshBuilder, stats_builder=None):
        """
        Create the processor, initialize the logger
        """
        self.step_file = step_file
        self.entity_mapper = entity_mapper
        self.topology_builder = topology_builder
        self.geometry_builder = geometry_builder
        self.mesh_builder = mesh_builder
        self.stats_builder = stats_builder
        
        self.data_format = "yaml"
        
        self.extract_geometry = self.geometry_builder != None
        self.extract_meshes = self.mesh_builder != None
        self.extract_stats = self.stats_builder != None
        self.extract_topo = self.topology_builder != None
        
        # Initialize the parts list
        self.parts = []
        
        # Directory for output files
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        
        # Create log
        self.log_dir = log_dir #output_dir.stem.replace("results", "log")
        os.makedirs(self.log_dir, exist_ok=True)
        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        logger = setup_logger('%s_logger'%step_file.stem, os.path.join(log_dir, '%s.log'%step_file.stem), formatter)
        logger.info("Init step processing: %s"%step_file.stem)
        self.logger = logger


    def load_step_file(self):
        self.parts = load_parts_from_step_file(self.step_file, logger=self.logger)
        
    def process_parts(self, convert=False, fix=False, write_face_obj=True, write_part_obj=True, indices=[]):
        if len(self.parts) == 0:
            self.logger.info("No parts loaded to process.")
            return
        
        # If no indices are given, process all parts
        if len(indices) == 0:
            indices = range(len(self.parts))
            self.logger.info("Processing all %i parts of file."%len(indices))
        
        topo_dicts = []
        geo_dicts = []
        mesh_dicts = []
        stats_dicts = []
        
        # Iterate over all indices
        for index in indices:
            part = self.parts[index]
            
            # Convert complete part to NURBS surfaces
            if convert:
                try:
                    nurbs_converter = BRepBuilderAPI_NurbsConvert(part)
                    nurbs_converter.Perform(part)
                    part = nurbs_converter.Shape()
                except Exception as e:
                    #print("Conversion failed, processing unconverted")
                    #print(e.args.split("\n"))
                    self.logger.error("Nurbs conversion error: %s"%"".join(str(e).split("\n")[:2]))
                    continue
            
            # Fix shape with healing operations
            if fix:
                #print("Fixing shape")
                b = _ShapeFix_Shape(part)
                b.SetPrecision(1e-8)
                #b.SetMaxTolerance(1e-8)
                #b.SetMinTolerance(1e-8)
                b.Perform()
                part = b.Shape()
        
            # Extract information for part
            topo_dict, geo_dict, meshes, stats_dict = self.__process_part(part)
            
            topo_dicts.append(topo_dict)
            geo_dicts.append(geo_dict)
            stats_dicts.append(stats_dict)
            
            if write_face_obj:
                mesh_path = self.output_dir / f"{self.step_file.stem}_mesh"
                #print(str(mesh_path), mesh_path)
                os.makedirs(mesh_path, exist_ok=True)
                for idx, mesh in enumerate(meshes):
                    if len(mesh["vertices"]) > 0:
                        igl.write_triangle_mesh("%s/%03i_%05i_mesh.obj"%(str(mesh_path), index, idx), mesh["vertices"], mesh["faces"])
        
        # Write out dictionary lists
        self.logger.info("Writing dictionaries")
        topo_yaml = self.output_dir / f"{self.step_file.stem}_topo"
        write_dictionary_to_file(topo_yaml, {"parts": topo_dicts}, self.data_format)
        self.logger.info("Topo dict: Done")
        geo_yaml = self.output_dir / f"{self.step_file.stem}_geo"
        write_dictionary_to_file(geo_yaml, {"parts": geo_dicts}, self.data_format)
        self.logger.info("Geo dict: Done")
        stats_yaml = self.output_dir / f"{self.step_file.stem}_stat"
        write_dictionary_to_file(stats_yaml, {"parts": stats_dicts}, self.data_format)
        self.logger.info("Stat dict: Done")

            
    def __process_part(self, part):
        self.logger.info("Entity mapper: Init")
        entity_mapper = self.entity_mapper([part])
        self.logger.info("Entity mapper: Done")

        # Extract topology
        if self.extract_topo:
            self.logger.info("Extract topo: Init")
            topo_dict_builder = self.topology_builder(entity_mapper)
            self.logger.info("Extract topo: Build")
            topo_dict = topo_dict_builder.build_dict_for_parts(part)
            self.logger.info("Extract topo: Done")
        else:
            topo_dict = {}

        # Extract geometry
        if self.extract_geometry:
            self.logger.info("Extract geo: Init")
            geo_dict_builder = self.geometry_builder(entity_mapper)
            self.logger.info("Extract geo: Build")
            geo_dict = geo_dict_builder.build_dict_for_parts(part, self.logger)
            self.logger.info("Extract geo: Done")
        else:
            geo_dict = {}

        # Extract statistics
        if self.extract_stats:
            self.logger.info("Extract stats: Init")
            stats_dict = extract_statistical_information(part, entity_mapper, self.logger)
            self.logger.info("Extract stats: Done")
        else:
            stats_dict = {}

        # Extract meshes
        if self.extract_meshes:
            self.logger.info("Extract mesh: Init")
            mesh_builder = self.mesh_builder(entity_mapper, self.logger)
            meshes = mesh_builder.create_surface_meshes(part)
            self.logger.info("Extract mesh: Done")
        else:
            meshes = []

        return topo_dict, geo_dict, meshes, stats_dict            
