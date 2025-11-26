#####################################################################################################################
# Copyright(C) 2011-2025 IT4Innovations National Supercomputing Center, VSB - Technical University of Ostrava
#
# This program is free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#####################################################################################################################
bl_info = {
    "name": "BRaaS-HPC-XMLMaterial",
    "author": "Milan Jaros, Petr Strakos, Lubomir Riha",
    "description": "",
    "blender": (4, 0, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Material"
}
#####################################################################################################################

def register():
    from . import braas_hpc_xmlmaterial_pref
    from . import braas_hpc_xmlmaterial_panel

    braas_hpc_xmlmaterial_pref.register()
    braas_hpc_xmlmaterial_panel.register()   

def unregister():
    from . import braas_hpc_xmlmaterial_pref
    from . import braas_hpc_xmlmaterial_panel
    
    try:        
        braas_hpc_xmlmaterial_pref.unregister()
        braas_hpc_xmlmaterial_panel.unregister()

    except RuntimeError:
        pass 
