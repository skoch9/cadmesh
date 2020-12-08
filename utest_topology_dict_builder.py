#!/usr/bin/python

# System
import unittest
from pathlib import Path

# CAD
from entity_mapper import EntityMapper

# PythonOCC
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

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

    def build_dicttest_output_for_body_for_body(self, output, body):
        return

    def build_dict_for_body(self, body):
        entity_mapper = EntityMapper(body)
        dict_builder = TopologyDictBuilder(entity_mapper)
        output = dict_builder.build_dict_for_body(body)
        self.test_output_for_body(output, body)

    def build_dicts_for_file(self, pathname):
        bodies = self.load_bodies_from_file(pathname)
        for body in bodies:
            self.build_dict_for_body(body)



    def test_build_dicts_for_files(self):
        data_dir = Path("./data")
        stp_files = [ f for f in data_dir.glob("**/*.stp")]
        for file in stp_files:
            self.build_dicts_for_file(file)

if __name__ == '__main__':
    unittest.main()