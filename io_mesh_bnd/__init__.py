# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

bl_info = {
    "name": "Angel Studios BND/BBND/TER Format",
    "author": "Dummiesman",
    "version": (0, 0, 2),
    "blender": (2, 83, 0),
    "location": "File > Import-Export",
    "description": "Import-Export BND files",
    "warning": "",
    "doc_url": "https://github.com/Dummiesman/BNDImportExport/",
    "tracker_url": "https://github.com/Dummiesman/BNDImportExport/",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

class ImportBND(bpy.types.Operator, ImportHelper):
    """Import from BND file format (.bnd)"""
    bl_idname = "import_scene.bnd"
    bl_label = 'Import BND'
    bl_options = {'UNDO'}

    filename_ext = ".bnd"
    filter_glob: StringProperty(default="*.bnd", options={'HIDDEN'})

    def execute(self, context):
        from . import import_bnd
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_bnd.load(self, context, **keywords)


class ExportBND(bpy.types.Operator, ExportHelper):
    """Export to PKG file format (.BND)"""
    bl_idname = "export_scene.bnd"
    bl_label = 'Export BND'

    filename_ext = ".bnd"
    filter_glob: StringProperty(
            default="*.bnd",
            options={'HIDDEN'},
            )

    export_binary: BoolProperty(
        name="Export Binary Bound",
        description="Export a binary bound along the ASCII bound",
        default=False,
        )
        
    #export_terrain: BoolProperty(
    #    name="Export Terrain Bound",
    #    description="Export a terrain bound along the binary bound",
    #    default=False,
    #    )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Do you desire modifiers to be applied in the PKG?",
        default=True,
        )
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "export_binary")
        #sub = layout.row()
        #sub.enabled = self.export_binary
        #sub.prop(self, "export_terrain")
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        
    def execute(self, context):
        from . import export_bnd
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_bnd.save(self, context, **keywords)


# Add to a menu
def menu_func_export(self, context):
    self.layout.operator(ExportBND.bl_idname, text="Angel Studios Bound (.bnd)")


def menu_func_import(self, context):
    self.layout.operator(ImportBND.bl_idname, text="Angel Studios Bound (.bnd)")


# Register factories
classes = (
    ImportBND,
    ExportBND
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
