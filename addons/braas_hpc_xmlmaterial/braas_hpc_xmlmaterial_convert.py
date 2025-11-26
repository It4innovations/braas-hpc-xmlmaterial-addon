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
import bpy
import xml.etree.ElementTree as ET
from xml.dom import minidom

from . import braas_hpc_xmlmaterial_map

import xml.etree.ElementTree as ET
import struct

import math
import numpy as np

class XMLWriter:
  def __init__(self):
    self.base = "" #path to xml #e:\\tmp\\braas_hpc_xmlmaterial\\

def float_array_to_string(value):
    """
    Converts a list of floats or a list of lists of floats to a space-separated string.

    :param value: List of floats or list of lists of floats
    :return: Space-separated string of float values
    """
    if any(isinstance(v, list) for v in value):
        # Flatten nested lists
        flat_list = [str(f) for sublist in value for f in sublist]
    else:
        # Convert single list of floats
        flat_list = [str(f) for f in value]

    return " ".join(flat_list)    

# Write an array to a binary file
def write_array_to_binary_file(writer_base, name, data):
    if len(writer_base.base) == 0:
       return float_array_to_string(data)

    filename = f"{writer_base.base}/{name}.array"

    try:
        with open(filename, "wb") as file:
            # Write the size of the array
            file.write(struct.pack('Q', len(data)))
            # Write the array data
            #file.write(bytearray(data))
            # Pack the entire array as binary data and write it to the file
            file.write(struct.pack(f'{len(data)}f', *data))
    except IOError as e:
        print(f"Error: Could not open file for writing: {filename}")
        return ""

    return filename

# Convert boolean value to "true" or "false"
def xml_write_boolean(value):
    return "true" if value else "false"

class CustomSocket:
  def __init__(self):
    self.identifier = None
    self.default_value = None
    self.type = None

  def __init__(self, id, value, type):
    self.identifier = id
    self.default_value = value
    self.type = type

def get_socket_identifier(socket, node):
  identifier = socket.identifier

  if node.type == 'MATH':
     if socket.identifier == 'Value':
        identifier = 'Value1'
     elif socket.identifier == 'Value_001':
        identifier = 'Value2'
     elif socket.identifier == 'Value_002':
        identifier = 'Value3'              

  return identifier    

def xml_write_socket(writer_base: XMLWriter, xml_node, node, socket):
    # Types: ('CUSTOM', 'VALUE', 'INT', 'BOOLEAN', 'VECTOR', 'ROTATION', 'MATRIX', 
    # 'STRING', 'RGBA', 'SHADER', 'OBJECT', 'IMAGE', 'GEOMETRY', 'COLLECTION', 
    # 'TEXTURE', 'MATERIAL', 'MENU')
    
    # if socket.type in ["CLOSURE", "UNDEFINED"] or socket.get('flags', 0) & socket.get('INTERNAL', 0):
    #     continue

    # if node.get('has_default_value', lambda x: False)(socket):
    #     continue

    if socket.type == "SHADER":
       #skip
       return
    
    socket_identifier = get_socket_identifier(socket, node)

    xml_node_socket = ET.SubElement(xml_node, "socket")
    xml_node_socket.set("ui_name", socket_identifier)

    xml_node_name = xml_node.get("name").replace(" ", "_")
    xml_socket_name = socket_identifier.replace(" ", "_")
    socket_file = f"{xml_node_name}_{xml_socket_name}"

    if socket.type in ["VALUE", "INT", "STRING", "ENUM"]: # Float
        xml_node_socket.set("value", str(socket.default_value))

    elif socket.type == "BOOLEAN":
        xml_node_socket.set("value", xml_write_boolean(socket.default_value))

    # elif socket.type == "BOOLEAN_ARRAY":
    #     value = node['get_bool_array'](socket)
    #     xml_node_socket.set(socket_identifier, write_array_to_binary_file(writer_base, socket_file, value))

    elif socket.type in ["FLOAT_ARRAY"]:
        value = socket.default_value
        xml_node_socket.set("value", write_array_to_binary_file(writer_base, socket_file, value))

    # elif socket.type == "INT_ARRAY":
    #     value = node['get_int_array'](socket)
    #     xml_node_socket.set(socket_identifier, write_array_to_binary_file(writer_base, socket_file, value))

    elif socket.type in ["RGBA", "VECTOR", "ROTATION"]:
        if len(socket.default_value) == 2:
            value = socket.default_value
            xml_node_socket.set("value", f"{value[0]} {value[1]} 0 0")
        elif len(socket.default_value) == 3:
            value = socket.default_value
            xml_node_socket.set("value", f"{value[0]} {value[1]} {value[2]} 0")
        elif len(socket.default_value) == 4:
            value = socket.default_value
            xml_node_socket.set("value", f"{value[0]} {value[1]} {value[2]} {value[3]}")
        else:
            print("not implemented: ", socket_identifier, socket.type, str(socket.default_value))                

    # elif socket.type == "TRANSFORM":
    #     tfm = node['get_transform'](socket)
    #     xml_node_socket.set(socket_identifier, " ".join(
    #         [" ".join(map(str, row)) for row in tfm]
    #     ))

    # elif socket.type == "NODE":
    #     value = node['get_node'](socket)
    #     if value:
    #         xml_node_socket.set(socket_identifier, value)

    # elif socket.type == "NODE_ARRAY":
    #     value = node['get_node_array'](socket)
    #     xml_node_socket.set(socket_identifier, " ".join(
    #         v if v else "" for v in value
    #     ))
    else:
        print("not implemented: ", socket_identifier, socket.type, str(socket))

def xml_write_node_name(xml_root, node, cycles_node, cycles_type = 0):
    cycles_node_xml_type = cycles_node[braas_hpc_xmlmaterial_map.CyclesNode][cycles_type][braas_hpc_xmlmaterial_map.CyclesNodeXml]
    xml_node = ET.SubElement(xml_root, cycles_node_xml_type)
    xml_node_name = node.name
    xml_node.set("name", xml_node_name)   

    return xml_node
   
def xml_write_enum(writer_base, xml_node, node, id, value, value_name):   
   ivalue = node.bl_rna.properties[value_name].enum_items[value].value
   xml_write_socket(writer_base, xml_node, node, CustomSocket(id, value=ivalue, type="ENUM"))
   
#########################################################################################
def b_node_is_a(cycles_node, struct_name):
    return cycles_node[braas_hpc_xmlmaterial_map.StructName] == struct_name

def curvemap_minmax_curve(curve, min_x, max_x):
    min_x = min(min_x, curve.points[0].location[0])
    max_x = max(max_x, curve.points[len(curve.points) - 1].location[0])

    return min_x, max_x

def curvemapping_minmax(cumap, num_curves):
    min_x = float('inf')
    max_x = float('-inf')
    for i in range(num_curves):
        map_curve = cumap.curves[i]
        min_x, max_x = curvemap_minmax_curve(map_curve, min_x, max_x)

    return min_x, max_x

def curvemapping_to_array(cumap, size):
    cumap.update()
    curve = cumap.curves[0]
    full_size = size + 1
    data = []
    for i in range(full_size):
        t = float(i) / float(size)
        data.append(cumap.evaluate(curve, t))

    return data

def curvemapping_float_to_array(cumap, size):   
    min_x, max_x = curvemapping_minmax(cumap, 1)
    
    range_x = max_x - min_x
    
    cumap.update()

    curve = cumap.curves[0]
    full_size = size + 1
    data = []
    for i in range(full_size):
        t = min_x + (float(i) / float(size)) * range_x
        data.append(cumap.evaluate(curve, t))

    return data

def curvemapping_color_to_array(cumap, size, rgb_curve):   
    num_curves = 4 if rgb_curve else 3
    min_x, max_x = curvemapping_minmax(cumap, num_curves)
    
    range_x = max_x - min_x
    
    cumap.update()
    
    map_r = cumap.curves[0]
    map_g = cumap.curves[1]
    map_b = cumap.curves[2]
    
    full_size = size + 1
    data = []
    
    if rgb_curve:
        map_i = cumap.curves[3]
        for i in range(full_size):
            t = min_x + (float(i) / float(size)) * range_x
            intensity = cumap.evaluate(map_i, t)
            data.append(cumap.evaluate(map_r, intensity))
            data.append(cumap.evaluate(map_g, intensity))
            data.append(cumap.evaluate(map_b, intensity))
    else:
        for i in range(full_size):
            t = min_x + (float(i) / float(size)) * range_x
            data.append(cumap.evaluate(map_r, t))
            data.append(cumap.evaluate(map_g, t))
            data.append(cumap.evaluate(map_b, t))

    return data        

def colorramp_to_array(ramp, size):
    """
    Convert a color ramp to arrays of colors and alpha values.

    Parameters:
    ramp : A color ramp object that has an `evaluate` method.
    ramp_color : List to store the color values (as tuples of three floats).
    ramp_alpha : List to store the alpha values (as floats).
    size : The number of divisions in the ramp.
    """
    full_size = size + 1
    
    # Resize the output lists.
    ramp_color = []
    ramp_alpha = []

    for i in range(full_size):
        color = ramp.evaluate(float(i) / float(size))  # Evaluate the ramp.
        
        ramp_color.append(color[0])  # Extract RGB.
        ramp_color.append(color[1])  # Extract RGB.
        ramp_color.append(color[2])  # Extract RGB.
        ramp_color.append(color[3])  # Extract RGB.

        ramp_alpha.append(color[3])  # Extract Alpha.

    return ramp_color, ramp_alpha

# Define the attribute prefixes
OBJECT_ATTR_PREFIX = "\x01object:"
INSTANCER_ATTR_PREFIX = "\x01instancer:"
VIEW_LAYER_ATTR_PREFIX = "\x01layer:"

def blender_attribute_name_add_type(name: str, attr_type: str) -> str:
    if attr_type == 'OBJECT':
        return f"{OBJECT_ATTR_PREFIX}{name}"
    elif attr_type == 'INSTANCER':
        return f"{INSTANCER_ATTR_PREFIX}{name}"
    elif attr_type == 'VIEW_LAYER':
        return f"{VIEW_LAYER_ATTR_PREFIX}{name}"
    else:
        return name

#########################################################################################

def create_xml_node(writer_base: XMLWriter, xml_root, node):
  xml_node = None

  cycles_node = braas_hpc_xmlmaterial_map.find_by_enum_type(node.type)

  RAMP_TABLE_SIZE = 256

  if b_node_is_a(cycles_node, "RGBCurve"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeRGBCurve b_curve_node(b_node);
    # BL::CurveMapping mapping(b_curve_node.mapping());
    # RGBCurvesNode *curves = graph->create_node<RGBCurvesNode>();
    # array<float3> curve_mapping_curves;
    # float min_x, max_x;
    curve_mapping_curves = curvemapping_color_to_array(node.mapping, RAMP_TABLE_SIZE, True)
    min_x, max_x = curvemapping_minmax(node.mapping, 4)
    # curves->set_min_x(min_x);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Min X", value=min_x, type="VALUE"))
    # curves->set_max_x(max_x);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Max X", value=max_x, type="VALUE"))
    # curves->set_curves(curve_mapping_curves);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Curves", value=curve_mapping_curves, type="FLOAT_ARRAY"))
    # curves->set_extrapolate(mapping.extend() == mapping.extend_EXTRAPOLATED);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Extrapolate", value=(node.mapping.extend=="EXTRAPOLATED"), type="BOOLEAN"))
    # node = curves;
  
  elif b_node_is_a(cycles_node, "VectorCurve"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeVectorCurve b_curve_node(b_node);
    # BL::CurveMapping mapping(b_curve_node.mapping());
    # VectorCurvesNode *curves = graph->create_node<VectorCurvesNode>();
    # array<float3> curve_mapping_curves;
    # float min_x, max_x;
    curve_mapping_curves = curvemapping_color_to_array(node.mapping, RAMP_TABLE_SIZE, False)
    min_x, max_x = curvemapping_minmax(node.mapping, 3)
    # curves->set_min_x(min_x);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Min X", value=min_x, type="VALUE"))
    # curves->set_max_x(max_x);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Max X", value=max_x, type="VALUE"))
    # curves->set_curves(curve_mapping_curves);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Curves", value=curve_mapping_curves, type="FLOAT_ARRAY"))
    # curves->set_extrapolate(mapping.extend() == mapping.extend_EXTRAPOLATED);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Extrapolate", value=(node.mapping.extend=="EXTRAPOLATED"), type="BOOLEAN"))
    # node = curves;
  
  elif b_node_is_a(cycles_node, "FloatCurve"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeFloatCurve b_curve_node(b_node);
    # BL::CurveMapping mapping(b_curve_node.mapping());
    # FloatCurveNode *curve = graph->create_node<FloatCurveNode>();
    # array<float> curve_mapping_curve;
    # float min_x, max_x;
    curve_mapping_curve = curvemapping_float_to_array(node.mapping, RAMP_TABLE_SIZE)
    min_x, max_x = curvemapping_minmax(node.mapping, 1)
    # curve->set_min_x(min_x);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Min X", value=min_x, type="VALUE"))
    # curve->set_max_x(max_x);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Max X", value=max_x, type="VALUE"))
    # curve->set_curve(curve_mapping_curve);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Curve", value=curve_mapping_curve, type="FLOAT_ARRAY"))
    # curve->set_extrapolate(mapping.extend() == mapping.extend_EXTRAPOLATED);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Extrapolate", value=(node.mapping.extend=="EXTRAPOLATED"), type="BOOLEAN"))
    # node = curve;
  
  elif b_node_is_a(cycles_node, "ValToRGB"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # RGBRampNode *ramp = graph->create_node<RGBRampNode>();
    # BL::ShaderNodeValToRGB b_ramp_node(b_node);
    # BL::ColorRamp b_color_ramp(b_ramp_node.color_ramp());
    # array<float3> ramp_values;
    # array<float> ramp_alpha;
    ramp_values, ramp_alpha = colorramp_to_array(node.color_ramp, RAMP_TABLE_SIZE);
    # ramp->set_ramp(ramp_values);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Ramp", value=ramp_values, type="FLOAT_ARRAY"))
    # ramp->set_ramp_alpha(ramp_alpha);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Ramp Alpha", value=ramp_alpha, type="FLOAT_ARRAY"))
    # 'EASE', 'CARDINAL', 'LINEAR', 'B_SPLINE', 'CONSTANT'
    # ramp->set_interpolate(b_color_ramp.interpolation() != BL::ColorRamp::interpolation_CONSTANT);
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Interpolate", value=(node.color_ramp.interpolation!="CONSTANT"), type="BOOLEAN"))
    # node = ramp;
  
  elif b_node_is_a(cycles_node, "RGB"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # ColorNode *color = graph->create_node<ColorNode>();
    # color->set_value(get_node_output_rgba(b_node, "Color"));
    # node = color;
  elif b_node_is_a(cycles_node, "Value"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # ValueNode *value = graph->create_node<ValueNode>();
    # value->set_value(get_node_output_value(b_node, "Value"));
    # node = value;
  elif b_node_is_a(cycles_node, "CameraData"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<CameraNode>();
  elif b_node_is_a(cycles_node, "Invert"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<InvertNode>();
  elif b_node_is_a(cycles_node, "Gamma"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<GammaNode>();
  elif b_node_is_a(cycles_node, "BrightContrast"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<BrightContrastNode>();
  elif b_node_is_a(cycles_node, "MixRGB"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeMixRGB b_mix_node(b_node);
    # MixNode *mix = graph->create_node<MixNode>();
    # mix->set_mix_type((NodeMix)b_mix_node.blend_type());
    # mix->set_use_clamp(b_mix_node.use_clamp());
    # node = mix;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Mix"):
    #BL::ShaderNodeMix b_mix_node(b_node);
    # ["MIX",                      "Mix",                     "Mix",                      [["MixVectorNode",              "mix_vector"],
    #                                                                                      ["MixVectorNonUniformNode",    "mix_vector_non_uniform"],
    #                                                                                      ["MixColorNode",               "mix_color"],
    #                                                                                      ["MixFloatNode",               "mix_float"]]],    
    #'FLOAT', 'VECTOR', 'RGBA'
    if node.data_type == 'VECTOR':
      #'UNIFORM', 'NON_UNIFORM'
      if node.factor_mode == 'UNIFORM':
        xml_node = xml_write_node_name(xml_root, node, cycles_node, cycles_type=0)
        # MixVectorNode *mix_node = graph->create_node<MixVectorNode>();
        # mix_node->set_use_clamp(b_mix_node.clamp_factor());
        xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Use Clamp", value=node.clamp_factor, type="BOOLEAN"))
        # node = mix_node;
      else:
        xml_node = xml_write_node_name(xml_root, node, cycles_node, cycles_type=1)
        # MixVectorNonUniformNode *mix_node = graph->create_node<MixVectorNonUniformNode>();
        # mix_node->set_use_clamp(b_mix_node.clamp_factor());
        xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Use Clamp", value=node.clamp_factor, type="BOOLEAN"))
        # node = mix_node;
    elif node.data_type == 'RGBA':
      xml_node = xml_write_node_name(xml_root, node, cycles_node, cycles_type=2)
      #   MixColorNode *mix_node = graph->create_node<MixColorNode>();
      #   mix_node->set_blend_type((NodeMix)b_mix_node.blend_type());
      #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Blend Type", value=node.blend_type, type="ENUM"))
      xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Blend Type", value=node.blend_type, value_name="blend_type")
      #   mix_node->set_use_clamp(b_mix_node.clamp_factor());
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Use Clamp", value=node.clamp_factor, type="BOOLEAN"))
      #   mix_node->set_use_clamp_result(b_mix_node.clamp_result());
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Use Clamp Result", value=node.clamp_result, type="BOOLEAN"))
      #   node = mix_node;
    else:
      xml_node = xml_write_node_name(xml_root, node, cycles_node, cycles_type=3)
      #   MixFloatNode *mix_node = graph->create_node<MixFloatNode>();
      #   mix_node->set_use_clamp(b_mix_node.clamp_factor());
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Use Clamp", value=node.clamp_factor, type="BOOLEAN"))
      #   node = mix_node;
  elif b_node_is_a(cycles_node, "SeparateRGB"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<SeparateRGBNode>();
  elif b_node_is_a(cycles_node, "CombineRGB"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<CombineRGBNode>();
  elif b_node_is_a(cycles_node, "SeparateHSV"):
     xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<SeparateHSVNode>();
  elif b_node_is_a(cycles_node, "CombineHSV"):
     xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<CombineHSVNode>();
  elif b_node_is_a(cycles_node, "SeparateColor"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeSeparateColor b_separate_node(b_node);
    # SeparateColorNode *separate_node = graph->create_node<SeparateColorNode>();
    # separate_node->set_color_type((NodeCombSepColorType)b_separate_node.mode());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Color Type", value=node.mode, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Color Type", value=node.mode, value_name="mode")
    # node = separate_node;
  elif b_node_is_a(cycles_node, "CombineColor"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeCombineColor b_combine_node(b_node);
    # CombineColorNode *combine_node = graph->create_node<CombineColorNode>();
    # combine_node->set_color_type((NodeCombSepColorType)b_combine_node.mode());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Color Type", value=node.mode, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Color Type", value=node.mode, value_name="mode")
    # node = combine_node;
  elif b_node_is_a(cycles_node, "SeparateXYZ"):
     xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<SeparateXYZNode>();    
  elif b_node_is_a(cycles_node, "CombineXYZ"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<CombineXYZNode>();    
  elif b_node_is_a(cycles_node, "HueSaturation"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<HSVNode>();
  elif b_node_is_a(cycles_node, "RGBToBW"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<RGBToBWNode>();   
  elif b_node_is_a(cycles_node, "MapRange"):
    # ["MAP_RANGE",                "MapRange",                "Map Range",                [["VectorMapRangeNode",         "vector_map_range"],
    #                                                                                      ["MapRangeNode",               "map_range"]]],    
    #BL::ShaderNodeMapRange b_map_range_node(b_node);
    if node.data_type == 'FLOAT_VECTOR':
      xml_node = xml_write_node_name(xml_root, node, cycles_node, cycles_type=0)
      #   VectorMapRangeNode *vector_map_range_node = graph->create_node<VectorMapRangeNode>();
      #   vector_map_range_node->set_use_clamp(b_map_range_node.clamp());
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Clamp", value=node.clamp, type="BOOLEAN"))
      #   vector_map_range_node->set_range_type(
      #       (NodeMapRangeType)b_map_range_node.interpolation_type());
      #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Range Type", value=node.interpolation_type, type="ENUM"))
      xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Range Type", value=node.interpolation_type, value_name="interpolation_type")
      #   node = vector_map_range_node;
    else:
      xml_node = xml_write_node_name(xml_root, node, cycles_node, cycles_type=1)
      #   MapRangeNode *map_range_node = graph->create_node<MapRangeNode>();
      #   map_range_node->set_clamp(b_map_range_node.clamp());
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Clamp", value=node.clamp, type="BOOLEAN"))
      #   map_range_node->set_range_type((NodeMapRangeType)b_map_range_node.interpolation_type());
      #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Range Type", value=node.interpolation_type, type="ENUM"))
      xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Range Type", value=node.interpolation_type, value_name="interpolation_type")
      #   node = map_range_node;
  elif b_node_is_a(cycles_node, "Clamp"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeClamp b_clamp_node(b_node);
    # ClampNode *clamp_node = graph->create_node<ClampNode>();
    # clamp_node->set_clamp_type((NodeClampType)b_clamp_node.clamp_type());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Clamp Type", value=node.clamp_type, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Clamp Type", value=node.clamp_type, value_name="clamp_type")
    # node = clamp_node;
  elif b_node_is_a(cycles_node, "Math"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeMath b_math_node(b_node);
    # MathNode *math_node = graph->create_node<MathNode>();
    # math_node->set_math_type((NodeMathType)b_math_node.operation());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Math Type", value=node.operation, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Type", value=node.operation, value_name="operation")

    # math_node->set_use_clamp(b_math_node.use_clamp());
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Use Clamp", value=node.use_clamp, type="BOOLEAN"))
    # node = math_node;
  elif b_node_is_a(cycles_node, "VectorMath"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeVectorMath b_vector_math_node(b_node);
    # VectorMathNode *vector_math_node = graph->create_node<VectorMathNode>();
    # vector_math_node->set_math_type((NodeVectorMathType)b_vector_math_node.operation());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Math Type", value=node.operation, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Math Type", value=node.operation, value_name="operation")
    # node = vector_math_node;
  elif b_node_is_a(cycles_node, "VectorRotate"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeVectorRotate b_vector_rotate_node(b_node);
    # VectorRotateNode *vector_rotate_node = graph->create_node<VectorRotateNode>();
    # vector_rotate_node->set_rotate_type(
    #     (NodeVectorRotateType)b_vector_rotate_node.rotation_type());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Rotate Type", value=node.rotation_type, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Rotate Type", value=node.rotation_type, value_name="rotation_type")
    # vector_rotate_node->set_invert(b_vector_rotate_node.invert());
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Invert", value=node.invert, type="BOOLEAN"))
    # node = vector_rotate_node;
  elif b_node_is_a(cycles_node, "VectorTransform"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeVectorTransform b_vector_transform_node(b_node);
    # VectorTransformNode *vtransform = graph->create_node<VectorTransformNode>();
    # vtransform->set_transform_type((NodeVectorTransformType)b_vector_transform_node.vector_type());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Transform Type", value=node.vector_type, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Transform Type", value=node.vector_type, value_name="vector_type")
    # vtransform->set_convert_from(
    #     (NodeVectorTransformConvertSpace)b_vector_transform_node.convert_from());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Convert From", value=node.convert_from, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Convert From", value=node.convert_from, value_name="convert_from")
    # vtransform->set_convert_to(
    #     (NodeVectorTransformConvertSpace)b_vector_transform_node.convert_to());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Convert To", value=node.convert_to, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Convert To", value=node.convert_to, value_name="convert_to")
    # node = vtransform;
  elif b_node_is_a(cycles_node, "Normal"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::Node::outputs_iterator out_it;
    # b_node.outputs.begin(out_it);

    # NormalNode *norm = graph->create_node<NormalNode>();
    # norm->set_direction(get_node_output_vector(b_node, "Normal"));
    # node = norm;
  elif b_node_is_a(cycles_node, "Mapping"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeMapping b_mapping_node(b_node);
    # MappingNode *mapping = graph->create_node<MappingNode>();
    # mapping->set_mapping_type((NodeMappingType)b_mapping_node.vector_type());
    #xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Mapping Type", value=node.vector_type, type="ENUM"))
    xml_write_enum(writer_base=writer_base, xml_node=xml_node, node=node, id="Mapping Type", value=node.vector_type, value_name="vector_type")
    # node = mapping;
  elif b_node_is_a(cycles_node, "Fresnel"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<FresnelNode>();
  elif b_node_is_a(cycles_node, "LayerWeight"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<LayerWeightNode>();
  elif b_node_is_a(cycles_node, "AddShader"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<AddClosureNode>();
  elif b_node_is_a(cycles_node, "MixShader"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<MixClosureNode>();
  elif b_node_is_a(cycles_node, "Attribute"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeAttribute b_attr_node(b_node);
    # AttributeNode *attr = graph->create_node<AttributeNode>();
    # attr->set_attribute(blender_attribute_name_add_type(b_attr_node.attribute_name(),
    #                                                     b_attr_node.attribute_type()));
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Attribute", value=blender_attribute_name_add_type(node.attribute_name,node.attribute_type), type="STRING"))
    # node = attr;    
  elif b_node_is_a(cycles_node, "Background"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<BackgroundNode>();
  elif b_node_is_a(cycles_node, "Holdout"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<HoldoutNode>();
  elif b_node_is_a(cycles_node, "BsdfDiffuse"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<DiffuseBsdfNode>();
  elif b_node_is_a(cycles_node, "SubsurfaceScattering"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeSubsurfaceScattering b_subsurface_node(b_node);

    # SubsurfaceScatteringNode *subsurface = graph->create_node<SubsurfaceScatteringNode>();

    if node.falloff == 'BURLEY':
    #   case BL::ShaderNodeSubsurfaceScattering::falloff_BURLEY:
    #     subsurface->set_method(CLOSURE_BSSRDF_BURLEY_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Method", value='26', type="ENUM"))
    #     break;
    elif node.falloff == 'RANDOM_WALK':
    #   case BL::ShaderNodeSubsurfaceScattering::falloff_RANDOM_WALK:
    #     subsurface->set_method(CLOSURE_BSSRDF_RANDOM_WALK_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Method", value='27', type="ENUM"))
    #     break;
    elif node.falloff == 'RANDOM_WALK_SKIN':
    #   case BL::ShaderNodeSubsurfaceScattering::falloff_RANDOM_WALK_SKIN:
    #     subsurface->set_method(CLOSURE_BSSRDF_RANDOM_WALK_SKIN_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Method", value='28', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])

    # node = subsurface;
  elif b_node_is_a(cycles_node, "BsdfAnisotropic"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfAnisotropic b_glossy_node(b_node);
    # GlossyBsdfNode *glossy = graph->create_node<GlossyBsdfNode>();

    # switch (b_glossy_node.distribution("):
    if node.distribution == 'BECKMANN':
    #   case BL::ShaderNodeBsdfAnisotropic::distribution_BECKMANN:
    #     glossy->set_distribution(CLOSURE_BSDF_MICROFACET_BECKMANN_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='9', type="ENUM"))
    #     break;
    elif node.distribution == 'GGX':
    #   case BL::ShaderNodeBsdfAnisotropic::distribution_GGX:
    #     glossy->set_distribution(CLOSURE_BSDF_MICROFACET_GGX_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='8', type="ENUM"))
    #     break;
    elif node.distribution == 'ASHIKHMIN_SHIRLEY':
    #   case BL::ShaderNodeBsdfAnisotropic::distribution_ASHIKHMIN_SHIRLEY:
    #     glossy->set_distribution(CLOSURE_BSDF_ASHIKHMIN_SHIRLEY_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='11', type="ENUM"))
    #     break;
    elif node.distribution == 'MULTI_GGX':
    #   case BL::ShaderNodeBsdfAnisotropic::distribution_MULTI_GGX:
    #     glossy->set_distribution(CLOSURE_BSDF_MICROFACET_MULTI_GGX_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='10', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = glossy;
  elif b_node_is_a(cycles_node, "BsdfGlass"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfGlass b_glass_node(b_node);
    # GlassBsdfNode *glass = graph->create_node<GlassBsdfNode>();
    # switch (b_glass_node.distribution("):
    if node.distribution == 'BECKMANN':
    #   case BL::ShaderNodeBsdfGlass::distribution_BECKMANN:
    #     glass->set_distribution(CLOSURE_BSDF_MICROFACET_BECKMANN_GLASS_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='19', type="ENUM"))
    #     break;
    elif node.distribution == 'GGX':
    #   case BL::ShaderNodeBsdfGlass::distribution_GGX:
    #     glass->set_distribution(CLOSURE_BSDF_MICROFACET_GGX_GLASS_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='20', type="ENUM"))
    #     break;
    elif node.distribution == 'MULTI_GGX':
    #   case BL::ShaderNodeBsdfGlass::distribution_MULTI_GGX:
    #     glass->set_distribution(CLOSURE_BSDF_MICROFACET_MULTI_GGX_GLASS_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='21', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = glass;
  elif b_node_is_a(cycles_node, "BsdfRefraction"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfRefraction b_refraction_node(b_node);
    # RefractionBsdfNode *refraction = graph->create_node<RefractionBsdfNode>();
    # switch (b_refraction_node.distribution("):
    if node.distribution == 'BECKMANN':
    #   case BL::ShaderNodeBsdfRefraction::distribution_BECKMANN:
    #     refraction->set_distribution(CLOSURE_BSDF_MICROFACET_BECKMANN_REFRACTION_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='16', type="ENUM"))
    #     break;
    elif node.distribution == 'GGX':
    #   case BL::ShaderNodeBsdfRefraction::distribution_GGX:
    #     refraction->set_distribution(CLOSURE_BSDF_MICROFACET_GGX_REFRACTION_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='17', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = refraction;
  elif b_node_is_a(cycles_node, "BsdfToon"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfToon b_toon_node(b_node);
    # ToonBsdfNode *toon = graph->create_node<ToonBsdfNode>();
    # switch (b_toon_node.component("):
    if node.component == 'DIFFUSE':
    #   case BL::ShaderNodeBsdfToon::component_DIFFUSE:
    #     toon->set_component(CLOSURE_BSDF_DIFFUSE_TOON_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Component", value='6', type="ENUM"))
    #     break;
    elif node.component == 'GLOSSY':
    #   case BL::ShaderNodeBsdfToon::component_GLOSSY:
    #     toon->set_component(CLOSURE_BSDF_GLOSSY_TOON_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Component", value='14', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = toon;
  elif b_node_is_a(cycles_node, "BsdfHair"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfHair b_hair_node(b_node);
    # HairBsdfNode *hair = graph->create_node<HairBsdfNode>();
    # switch (b_hair_node.component("):
    if node.component == 'Reflection':
    #   case BL::ShaderNodeBsdfHair::component_Reflection:
    #     hair->set_component(CLOSURE_BSDF_HAIR_REFLECTION_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Component", value='15', type="ENUM"))
    #     break;
    elif node.component == 'Transmission':
    #   case BL::ShaderNodeBsdfHair::component_Transmission:
    #     hair->set_component(CLOSURE_BSDF_HAIR_TRANSMISSION_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Component", value='18', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = hair;
  elif b_node_is_a(cycles_node, "BsdfHairPrincipled"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfHairPrincipled b_principled_hair_node(b_node);
    # PrincipledHairBsdfNode *principled_hair = graph->create_node<PrincipledHairBsdfNode>();    
    # principled_hair->set_model((NodePrincipledHairModel)get_enum(b_principled_hair_node.ptr,
    #                                                              "model",
    #                                                              NODE_PRINCIPLED_HAIR_MODEL_NUM,
    #                                                              NODE_PRINCIPLED_HAIR_HUANG));
    if node.model == 'CHIANG':
       xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Model", value='0', type="ENUM"))
    elif node.model == 'HUANG':
       xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Model", value='1', type="ENUM"))
    # principled_hair->set_parametrization(
    #     (NodePrincipledHairParametrization)get_enum(b_principled_hair_node.ptr,
    #                                                 "parametrization",
    #                                                 NODE_PRINCIPLED_HAIR_PARAMETRIZATION_NUM,
    #                                                 NODE_PRINCIPLED_HAIR_REFLECTANCE));

    if node.parametrization == 'ABSORPTION':
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Parametrization", value='0', type="ENUM"))
    elif node.parametrization == 'MELANIN':
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Parametrization", value='1', type="ENUM"))
    elif node.parametrization == 'COLOR':
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Parametrization", value='2', type="ENUM"))

    # node = principled_hair;
  elif b_node_is_a(cycles_node, "BsdfPrincipled"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfPrincipled b_principled_node(b_node);
    # PrincipledBsdfNode *principled = graph->create_node<PrincipledBsdfNode>();
    # switch (b_principled_node.distribution("):
    if node.distribution == 'GGX':
    #   case BL::ShaderNodeBsdfPrincipled::distribution_GGX:
    #     principled->set_distribution(CLOSURE_BSDF_MICROFACET_GGX_GLASS_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='20', type="ENUM"))
    #     break;
    elif node.distribution == 'MULTI_GGX':
    #   case BL::ShaderNodeBsdfPrincipled::distribution_MULTI_GGX:
    #     principled->set_distribution(CLOSURE_BSDF_MICROFACET_MULTI_GGX_GLASS_ID);
    #     break;
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='21', type="ENUM"))
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    
    # switch (b_principled_node.subsurface_method("):
    if node.subsurface_method == 'BURLEY':
    #   case BL::ShaderNodeBsdfPrincipled::subsurface_method_BURLEY:
    #     principled->set_subsurface_method(CLOSURE_BSSRDF_BURLEY_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Subsurface Method", value='26', type="ENUM"))
    #     break;
    elif node.subsurface_method == 'RANDOM_WALK':
    #   case BL::ShaderNodeBsdfPrincipled::subsurface_method_RANDOM_WALK:
    #     principled->set_subsurface_method(CLOSURE_BSSRDF_RANDOM_WALK_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Subsurface Method", value='27', type="ENUM"))
    #     break;
    elif node.subsurface_method == 'RANDOM_WALK_SKIN':
    #   case BL::ShaderNodeBsdfPrincipled::subsurface_method_RANDOM_WALK_SKIN:
    #     principled->set_subsurface_method(CLOSURE_BSSRDF_RANDOM_WALK_SKIN_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Subsurface Method", value='28', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = principled;
  elif b_node_is_a(cycles_node, "BsdfTranslucent"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<TranslucentBsdfNode>();
  elif b_node_is_a(cycles_node, "BsdfTransparent"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<TransparentBsdfNode>();
  elif b_node_is_a(cycles_node, "BsdfRayPortal"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<RayPortalBsdfNode>();
  elif b_node_is_a(cycles_node, "BsdfSheen"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBsdfSheen b_sheen_node(b_node);
    # SheenBsdfNode *sheen = graph->create_node<SheenBsdfNode>();
    # switch (b_sheen_node.distribution("):
    if node.distribution == 'ASHIKHMIN':
    #   case BL::ShaderNodeBsdfSheen::distribution_ASHIKHMIN:
    #     sheen->set_distribution(CLOSURE_BSDF_ASHIKHMIN_VELVET_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='12', type="ENUM"))
    #     break;
    elif node.distribution == 'MICROFIBER':
    #   case BL::ShaderNodeBsdfSheen::distribution_MICROFIBER:
    #     sheen->set_distribution(CLOSURE_BSDF_SHEEN_ID);
      xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Distribution", value='5', type="ENUM"))
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = sheen;
  elif b_node_is_a(cycles_node, "Emission"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<EmissionNode>();
  elif b_node_is_a(cycles_node, "AmbientOcclusion"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeAmbientOcclusion b_ao_node(b_node);
    # AmbientOcclusionNode *ao = graph->create_node<AmbientOcclusionNode>();
    # ao->set_samples(b_ao_node.samples());
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Samples", value=node.samples, type="INT"))
    # ao->set_inside(b_ao_node.inside());
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Inside", value=node.inside, type="BOOLEAN"))
    # ao->set_only_local(b_ao_node.only_local());
    xml_write_socket(writer_base, xml_node, node, CustomSocket(id="Only Local", value=node.only_local, type="BOOLEAN"))
    # node = ao;
  elif b_node_is_a(cycles_node, "VolumeScatter"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<ScatterVolumeNode>();
  elif b_node_is_a(cycles_node, "VolumeAbsorption"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    #node = graph->create_node<AbsorptionVolumeNode>();
  elif b_node_is_a(cycles_node, "VolumePrincipled"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # PrincipledVolumeNode *principled = graph->create_node<PrincipledVolumeNode>();
    # node = principled;
  elif b_node_is_a(cycles_node, "NewGeometry"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<GeometryNode>();
  elif b_node_is_a(cycles_node, "Wireframe"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeWireframe b_wireframe_node(b_node);
    # WireframeNode *wire = graph->create_node<WireframeNode>();
    # wire->set_use_pixel_size(b_wireframe_node.use_pixel_size());
    # node = wire;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Wavelength"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<WavelengthNode>();
  elif b_node_is_a(cycles_node, "Blackbody"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<BlackbodyNode>();
  elif b_node_is_a(cycles_node, "LightPath"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<LightPathNode>();
  elif b_node_is_a(cycles_node, "LightFalloff"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<LightFalloffNode>();
  elif b_node_is_a(cycles_node, "ObjectInfo"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<ObjectInfoNode>();
  elif b_node_is_a(cycles_node, "ParticleInfo"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<ParticleInfoNode>();
  elif b_node_is_a(cycles_node, "HairInfo"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<HairInfoNode>();    
  elif b_node_is_a(cycles_node, "PointInfo"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<PointInfoNode>();
  elif b_node_is_a(cycles_node, "VolumeInfo"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # node = graph->create_node<VolumeInfoNode>();
  elif b_node_is_a(cycles_node, "VertexColor"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeVertexColor b_vertex_color_node(b_node);
    # VertexColorNode *vertex_color_node = graph->create_node<VertexColorNode>();
    # vertex_color_node->set_layer_name(ustring(b_vertex_color_node.layer_name()));
    # node = vertex_color_node;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Bump"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBump b_bump_node(b_node);
    # BumpNode *bump = graph->create_node<BumpNode>();
    # bump->set_invert(b_bump_node.invert());
    # node = bump;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Script"):
# #ifdef WITH_OSL
#     if (scene->shader_manager->use_osl("):
#       /* create script node */
#       BL::ShaderNodeScript b_script_node(b_node);

#       ShaderManager *manager = scene->shader_manager;
#       string bytecode_hash = b_script_node.bytecode_hash();

#       if (!bytecode_hash.empty("):
#         node = OSLShaderManager::osl_node(
#             graph, manager, "", bytecode_hash, b_script_node.bytecode());
#         print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
#       else {
#         string absolute_filepath = blender_absolute_path(
#             b_data, b_ntree, b_script_node.filepath());
#         node = OSLShaderManager::osl_node(graph, manager, absolute_filepath, "");
#         print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
#       print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
# #else
#     (void)b_data;
#     (void)b_ntree;
# #endif
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexImage"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexImage b_image_node(b_node);
    # BL::Image b_image(b_image_node.image());
    # BL::ImageUser b_image_user(b_image_node.image_user());
    # ImageTextureNode *image = graph->create_node<ImageTextureNode>();

    # image->set_interpolation(get_image_interpolation(b_image_node));
    # image->set_extension(get_image_extension(b_image_node));
    # image->set_projection((NodeImageProjection)b_image_node.projection());
    # image->set_projection_blend(b_image_node.projection_blend());
    # BL::TexMapping b_texture_mapping(b_image_node.texture_mapping());
    # get_tex_mapping(image, b_texture_mapping);

    # if (b_image) {
    #   BL::Image::source_enum b_image_source = b_image.source();
    #   PointerRNA colorspace_ptr = b_image.colorspace_settings().ptr;
    #   image->set_colorspace(ustring(get_enum_identifier(colorspace_ptr, "name")));

    #   image->set_animated(is_image_animated(b_image_source, b_image_user));
    #   image->set_alpha_type(get_image_alpha_type(b_image));

    #   array<int> tiles;
    #   for (BL::UDIMTile &b_tile : b_image.tiles) {
    #     tiles.push_back_slow(b_tile.number());
    #     print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #   image->set_tiles(tiles);

    #   /* builtin images will use callback-based reading because
    #    * they could only be loaded correct from blender side
    #    */
    #   bool is_builtin = b_image.packed_file() || b_image_source == BL::Image::source_GENERATED ||
    #                     b_image_source == BL::Image::source_MOVIE ||
    #                     (b_engine.is_preview() && b_image_source != BL::Image::source_SEQUENCE);

    #   if (is_builtin) {
    #     /* for builtin images we're using image datablock name to find an image to
    #      * read pixels from later
    #      *
    #      * also store frame number as well, so there's no differences in handling
    #      * builtin names for packed images and movies
    #      */
    #     int scene_frame = b_scene.frame_current();
    #     int image_frame = image_user_frame_number(b_image_user, b_image, scene_frame);
    #     if (b_image_source != BL::Image::source_TILED) {
    #       image->handle = scene->image_manager->add_image(
    #           new BlenderImageLoader(b_image, image_frame, 0, b_engine.is_preview()),
    #           image->image_params());
    #       print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #     else {
    #       vector<ImageLoader *> loaders;
    #       loaders.reserve(image->get_tiles().size());
    #       for (int tile_number : image->get_tiles("):
    #         loaders.push_back(
    #             new BlenderImageLoader(b_image, image_frame, tile_number, b_engine.is_preview()));
    #         print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])

    #       image->handle = scene->image_manager->add_image(loaders, image->image_params());
    #       print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #     print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #   else {
    #     ustring filename = ustring(
    #         image_user_file_path(b_data, b_image_user, b_image, b_scene.frame_current()));
    #     image->set_filename(filename);
    #     print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = image;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexEnvironment"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexEnvironment b_env_node(b_node);
    # BL::Image b_image(b_env_node.image());
    # BL::ImageUser b_image_user(b_env_node.image_user());
    # EnvironmentTextureNode *env = graph->create_node<EnvironmentTextureNode>();

    # env->set_interpolation(get_image_interpolation(b_env_node));
    # env->set_projection((NodeEnvironmentProjection)b_env_node.projection());
    # BL::TexMapping b_texture_mapping(b_env_node.texture_mapping());
    # get_tex_mapping(env, b_texture_mapping);

    # if (b_image) {
    #   BL::Image::source_enum b_image_source = b_image.source();
    #   PointerRNA colorspace_ptr = b_image.colorspace_settings().ptr;
    #   env->set_colorspace(ustring(get_enum_identifier(colorspace_ptr, "name")));
    #   env->set_animated(is_image_animated(b_image_source, b_image_user));
    #   env->set_alpha_type(get_image_alpha_type(b_image));

    #   bool is_builtin = b_image.packed_file() || b_image_source == BL::Image::source_GENERATED ||
    #                     b_image_source == BL::Image::source_MOVIE ||
    #                     (b_engine.is_preview() && b_image_source != BL::Image::source_SEQUENCE);

    #   if (is_builtin) {
    #     int scene_frame = b_scene.frame_current();
    #     int image_frame = image_user_frame_number(b_image_user, b_image, scene_frame);
    #     env->handle = scene->image_manager->add_image(
    #         new BlenderImageLoader(b_image, image_frame, 0, b_engine.is_preview()),
    #         env->image_params());
    #     print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #   else {
    #     env->set_filename(
    #         ustring(image_user_file_path(b_data, b_image_user, b_image, b_scene.frame_current())));
    #     print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = env;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexGradient"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexGradient b_gradient_node(b_node);
    # GradientTextureNode *gradient = graph->create_node<GradientTextureNode>();
    # gradient->set_gradient_type((NodeGradientType)b_gradient_node.gradient_type());
    # BL::TexMapping b_texture_mapping(b_gradient_node.texture_mapping());
    # get_tex_mapping(gradient, b_texture_mapping);
    # node = gradient;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexVoronoi"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexVoronoi b_voronoi_node(b_node);
    # VoronoiTextureNode *voronoi = graph->create_node<VoronoiTextureNode>();
    # voronoi->set_dimensions(b_voronoi_node.voronoi_dimensions());
    # voronoi->set_feature((NodeVoronoiFeature)b_voronoi_node.feature());
    # voronoi->set_metric((NodeVoronoiDistanceMetric)b_voronoi_node.distance());
    # voronoi->set_use_normalize(b_voronoi_node.normalize());
    # BL::TexMapping b_texture_mapping(b_voronoi_node.texture_mapping());
    # get_tex_mapping(voronoi, b_texture_mapping);
    # node = voronoi;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexMagic"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexMagic b_magic_node(b_node);
    # MagicTextureNode *magic = graph->create_node<MagicTextureNode>();
    # magic->set_depth(b_magic_node.turbulence_depth());
    # BL::TexMapping b_texture_mapping(b_magic_node.texture_mapping());
    # get_tex_mapping(magic, b_texture_mapping);
    # node = magic;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexWave"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexWave b_wave_node(b_node);
    # WaveTextureNode *wave = graph->create_node<WaveTextureNode>();
    # wave->set_wave_type((NodeWaveType)b_wave_node.wave_type());
    # wave->set_bands_direction((NodeWaveBandsDirection)b_wave_node.bands_direction());
    # wave->set_rings_direction((NodeWaveRingsDirection)b_wave_node.rings_direction());
    # wave->set_profile((NodeWaveProfile)b_wave_node.wave_profile());
    # BL::TexMapping b_texture_mapping(b_wave_node.texture_mapping());
    # get_tex_mapping(wave, b_texture_mapping);
    # node = wave;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexChecker"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexChecker b_checker_node(b_node);
    # CheckerTextureNode *checker = graph->create_node<CheckerTextureNode>();
    # BL::TexMapping b_texture_mapping(b_checker_node.texture_mapping());
    # get_tex_mapping(checker, b_texture_mapping);
    # node = checker;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexBrick"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexBrick b_brick_node(b_node);
    # BrickTextureNode *brick = graph->create_node<BrickTextureNode>();
    # brick->set_offset(b_brick_node.offset());
    # brick->set_offset_frequency(b_brick_node.offset_frequency());
    # brick->set_squash(b_brick_node.squash());
    # brick->set_squash_frequency(b_brick_node.squash_frequency());
    # BL::TexMapping b_texture_mapping(b_brick_node.texture_mapping());
    # get_tex_mapping(brick, b_texture_mapping);
    # node = brick;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexNoise"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexNoise b_noise_node(b_node);
    # NoiseTextureNode *noise = graph->create_node<NoiseTextureNode>();
    # noise->set_dimensions(b_noise_node.noise_dimensions());
    # noise->set_type((NodeNoiseType)b_noise_node.noise_type());
    # noise->set_use_normalize(b_noise_node.normalize());
    # BL::TexMapping b_texture_mapping(b_noise_node.texture_mapping());
    # get_tex_mapping(noise, b_texture_mapping);
    # node = noise;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexCoord"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexCoord b_tex_coord_node(b_node);
    # TextureCoordinateNode *tex_coord = graph->create_node<TextureCoordinateNode>();
    # tex_coord->set_from_dupli(b_tex_coord_node.from_instancer());
    # if (b_tex_coord_node.object("):
    #   tex_coord->set_use_transform(true);
    #   tex_coord->set_ob_tfm(get_transform(b_tex_coord_node.object().matrix_world()));
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = tex_coord;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexSky"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexSky b_sky_node(b_node);
    # SkyTextureNode *sky = graph->create_node<SkyTextureNode>();
    # sky->set_sky_type((NodeSkyType)b_sky_node.sky_type());
    # sky->set_sun_direction(normalize(get_float3(b_sky_node.sun_direction())));
    # sky->set_turbidity(b_sky_node.turbidity());
    # sky->set_ground_albedo(b_sky_node.ground_albedo());
    # sky->set_sun_disc(b_sky_node.sun_disc());
    # sky->set_sun_size(b_sky_node.sun_size());
    # sky->set_sun_intensity(b_sky_node.sun_intensity());
    # sky->set_sun_elevation(b_sky_node.sun_elevation());
    # sky->set_sun_rotation(b_sky_node.sun_rotation());
    # sky->set_altitude(b_sky_node.altitude());
    # sky->set_air_density(b_sky_node.air_density());
    # sky->set_dust_density(b_sky_node.dust_density());
    # sky->set_ozone_density(b_sky_node.ozone_density());
    # BL::TexMapping b_texture_mapping(b_sky_node.texture_mapping());
    # get_tex_mapping(sky, b_texture_mapping);
    # node = sky;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexIES"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexIES b_ies_node(b_node);
    # IESLightNode *ies = graph->create_node<IESLightNode>();
    # switch (b_ies_node.mode("):
    #   case BL::ShaderNodeTexIES::mode_EXTERNAL:
    #     ies->set_filename(ustring(blender_absolute_path(b_data, b_ntree, b_ies_node.filepath())));
    #     break;
    #   case BL::ShaderNodeTexIES::mode_INTERNAL:
    #     ustring ies_content = ustring(get_text_datablock_content(b_ies_node.ies().ptr));
    #     if (ies_content.empty("):
    #       ies_content = "\n";
    #       print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    #     ies->set_ies(ies_content);
    #     break;
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    # node = ies;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexWhiteNoise"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexWhiteNoise b_tex_white_noise_node(b_node);
    # WhiteNoiseTextureNode *white_noise_node = graph->create_node<WhiteNoiseTextureNode>();
    # white_noise_node->set_dimensions(b_tex_white_noise_node.noise_dimensions());
    # node = white_noise_node;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "NormalMap"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeNormalMap b_normal_map_node(b_node);
    # NormalMapNode *nmap = graph->create_node<NormalMapNode>();
    # nmap->set_space((NodeNormalMapSpace)b_normal_map_node.space());
    # nmap->set_attribute(ustring(b_normal_map_node.uv_map()));
    # node = nmap;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Tangent"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTangent b_tangent_node(b_node);
    # TangentNode *tangent = graph->create_node<TangentNode>();
    # tangent->set_direction_type((NodeTangentDirectionType)b_tangent_node.direction_type());
    # tangent->set_axis((NodeTangentAxis)b_tangent_node.axis());
    # tangent->set_attribute(ustring(b_tangent_node.uv_map()));
    # node = tangent;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "UVMap"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeUVMap b_uvmap_node(b_node);
    # UVMapNode *uvm = graph->create_node<UVMapNode>();
    # uvm->set_attribute(ustring(b_uvmap_node.uv_map()));
    # uvm->set_from_dupli(b_uvmap_node.from_instancer());
    # node = uvm;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "TexPointDensity"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeTexPointDensity b_point_density_node(b_node);
    # PointDensityTextureNode *point_density = graph->create_node<PointDensityTextureNode>();
    # point_density->set_space((NodeTexVoxelSpace)b_point_density_node.space());
    # point_density->set_interpolation(get_image_interpolation(b_point_density_node));
    # point_density->handle = scene->image_manager->add_image(
    #     new BlenderPointDensityLoader(b_depsgraph, b_point_density_node),
    #     point_density->image_params());

    # b_point_density_node.cache_point_density(b_depsgraph);
    # node = point_density;

    # /* Transformation form world space to texture space.
    #  *
    #  * NOTE: Do this after the texture is cached, this is because getting
    #  * min/max will need to access this cache.
    #  */
    # BL::Object b_ob(b_point_density_node.object());
    # if (b_ob) {
    #   float3 loc, size;
    #   point_density_texture_space(b_depsgraph, b_point_density_node, loc, size);
    #   point_density->set_tfm(transform_translate(-loc) * transform_scale(size) *
    #                          transform_inverse(get_transform(b_ob.matrix_world())));
    #   print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Bevel"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeBevel b_bevel_node(b_node);
    # BevelNode *bevel = graph->create_node<BevelNode>();
    # bevel->set_samples(b_bevel_node.samples());
    # node = bevel;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "Displacement"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeDisplacement b_disp_node(b_node);
    # DisplacementNode *disp = graph->create_node<DisplacementNode>();
    # disp->set_space((NodeNormalMapSpace)b_disp_node.space());
    # node = disp;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "VectorDisplacement"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeVectorDisplacement b_disp_node(b_node);
    # VectorDisplacementNode *disp = graph->create_node<VectorDisplacementNode>();
    # disp->set_space((NodeNormalMapSpace)b_disp_node.space());
    # disp->set_attribute(ustring(""));
    # node = disp;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])
  elif b_node_is_a(cycles_node, "OutputAOV"):
    xml_node = xml_write_node_name(xml_root, node, cycles_node)
    # BL::ShaderNodeOutputAOV b_aov_node(b_node);
    # OutputAOVNode *aov = graph->create_node<OutputAOVNode>();
    # aov->set_name(ustring(b_aov_node.aov_name()));
    # node = aov;
    print("Not implemented: ", cycles_node[braas_hpc_xmlmaterial_map.StructName])

  return xml_node

#########################################################################################
def get_link_from_socket_identifier(link):
  identifier = link.from_socket.identifier

  if link.from_node.type == 'ADD_SHADER':
     if link.from_socket.identifier == 'Shader':
        identifier = 'Closure'

  elif link.from_node.type == 'MIX_SHADER':
     if link.from_socket.identifier == 'Shader':
        identifier = 'Closure'        

  return identifier

def get_link_to_socket_identifier(link):
  identifier = link.to_socket.identifier

  if link.to_node.type == 'ADD_SHADER':
     if link.to_socket.identifier == 'Shader':
        identifier = 'Closure1'
     elif link.to_socket.identifier == 'Shader_001':
        identifier = 'Closure2'

  elif link.to_node.type == 'MIX_SHADER':
     if link.to_socket.identifier == 'Shader':
        identifier = 'Closure1'
     elif link.to_socket.identifier == 'Shader_001':
        identifier = 'Closure2'

  elif link.to_node.type == 'MATH':
     if link.to_socket.identifier == 'Value':
        identifier = 'Value1'
     elif link.to_socket.identifier == 'Value_001':
        identifier = 'Value2'
     elif link.to_socket.identifier == 'Value_002':
        identifier = 'Value3'              

  return identifier
#########################################################################################

# Write a node and its attributes to XML
def xml_write_node(writer_base: XMLWriter, node, xml_root: ET.Element):   
    xml_node = create_xml_node(writer_base, xml_root, node)

    # Types: ('CUSTOM', 'VALUE', 'INT', 'BOOLEAN', 'VECTOR', 'ROTATION', 'MATRIX', 
    # 'STRING', 'RGBA', 'SHADER', 'OBJECT', 'IMAGE', 'GEOMETRY', 'COLLECTION', 
    # 'TEXTURE', 'MATERIAL', 'MENU')
    for socket in node.inputs:
        xml_write_socket(writer_base, xml_node, node, socket)

    # for socket in node.outputs:
    #     xml_write_socket(writer_base, xml_node, node, socket)       

    return xml_node

def export_shader(shader, node_tree):
    # Create the root element
    shader_xml = ET.Element("shader")
    shader_xml.set("name", shader.name)

    writer_base = XMLWriter()
    writer_base.base = ""

    for node in node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            continue

        xml_write_node(writer_base, node, shader_xml)
        # Create a child element for principled_volume
        #node_xml = ET.SubElement(shader_xml, braas_hpc_xmlmaterial_map.enum_to_xml_type(node.type))
        #node_xml.set("name", node.name)

        #for input in node.inputs:
        #    node_xml.set(input.identifier, "")
        # principled_volume.set("temperature_attribute", "temperature")

    for node in node_tree.nodes:
        for output in node.outputs:
            for link in output.links:
                # xml_node connect_node = xml_root.append_child("connect");
                connect_node = ET.SubElement(shader_xml, "connect")

                # xml_attribute attr_from_node = connect_node.append_attribute("from_node");
                # attr_from_node = xml_pointer_to_name(output->parent).c_str();
                connect_node.set("from_node", link.from_node.name)

                # xml_attribute attr_from_socket = connect_node.append_attribute("from_socket");
                # attr_from_socket = output->socket_type.name.c_str();                

                # xml_attribute attr_from_socket_ui = connect_node.append_attribute("from_socket_ui");
                # attr_from_socket_ui = output->socket_type.ui_name.c_str();
                connect_node.set("from_socket_ui", get_link_from_socket_identifier(link))

                # xml_attribute attr_to_node = connect_node.append_attribute("to_node");
                # string to_name = xml_pointer_to_name(input->parent);
                # if (OutputNode* output_node = dynamic_cast<OutputNode*>(input->parent))
                # 	to_name = input->parent->name.string(); // output
                # attr_to_node = to_name.c_str();
                connect_node.set("to_node", link.to_node.name)
                	
                # xml_attribute attr_to_socket = connect_node.append_attribute("to_socket");
                # attr_to_socket = input->socket_type.name.c_str();

                # xml_attribute attr_to_socket_ui = connect_node.append_attribute("to_socket_ui");
                # attr_to_socket_ui = input->socket_type.ui_name.c_str();
                connect_node.set("to_socket_ui", get_link_to_socket_identifier(link))

    # # Create a child element for connect
    # connect = ET.SubElement(shader, "connect")
    # connect.set("from", "2257750539968 volume")
    # connect.set("to", "output volume")

    # Convert the ElementTree to a string
    #xml_string = ET.tostring(shader_xml, encoding="unicode")
    # Pretty print the XML
    xml_string = ET.tostring(shader_xml, encoding="unicode")
    parsed_xml = minidom.parseString(xml_string)
    pretty_xml = parsed_xml.toprettyxml()

    # shader_xml_path = "e:\\tmp\\braas_hpc_xmlmaterial\\shader.xml"
    # # Write the XML string to a file
    # with open(shader_xml_path, "w", encoding="utf-8") as xml_file:
    #     xml_file.write(pretty_xml)

    # print("XML file created successfully: ", shader_xml_path)

    return pretty_xml


def export_node(shader, node):
    # Create the root element
    shader_xml = ET.Element("shader")
    shader_xml.set("name", shader.name)

    writer_base = XMLWriter()
    writer_base.base = ""
    xml_write_node(writer_base, node, shader_xml)

    # Pretty print the XML
    xml_string = ET.tostring(shader_xml, encoding="unicode")
    parsed_xml = minidom.parseString(xml_string)
    pretty_xml = parsed_xml.toprettyxml()

    return pretty_xml