# BRaaS-HPC-XMLMaterial Blender Addon

A Blender addon for exporting Cycles shader node trees to XML format, designed for high-performance computing (HPC) workflows and external rendering engines.

## Overview

**BRaaS-HPC-XMLMaterial** is a Blender addon that allows users to export Cycles shader materials and individual shader nodes to XML format. This enables material data to be used in HPC rendering pipelines, custom rendering engines, or external visualization tools that can parse and interpret Cycles shader networks.

The addon provides a simple interface in Blender's Shader Editor, allowing you to export complete shader networks or individual nodes with their parameters, connections, and properties preserved in a structured XML format.

## Features

- **Export Complete Shaders**: Export entire shader node trees including all nodes and their connections
- **Export Individual Nodes**: Export a single selected node with all its properties and parameters
- **Comprehensive Node Support**: Supports 80+ Cycles shader nodes including:
  - BSDF shaders (Principled, Diffuse, Glossy, Glass, etc.)
  - Texture nodes (Image, Noise, Voronoi, etc.)
  - Color manipulation nodes (Mix, Color Ramp, etc.)
  - Math and vector operations
  - Input nodes (Texture Coordinate, Geometry, etc.)
  - Output nodes and volume shaders
- **XML Output**: Generates well-formatted XML that can be integrated into external rendering systems
- **Socket Value Preservation**: Exports default values for all node sockets including:
  - Scalar values (float, int, boolean)
  - Vector and color values (RGB, RGBA, XYZ)
  - Arrays and curve data
  - Enum properties

## Requirements

- **Blender**: Version 5.2.0 or higher
- **Operating System**: Windows, macOS, or Linux (any platform that supports Blender 5.2+)
- **Reader**: [CyclesPhi](https://github.com/It4innovations/cyclesphi) (`src/app/cycles_xml_bin.cpp`)

## Installation

### Step 1: Download the Addon

1. Download the add-on in zip format: https://github.com/It4innovations/braas-hpc-xmlmaterial-addon/releases

### Step 2: Install in Blender

1. Open Blender
2. Go to `Edit` → `Preferences` → `Add-ons`
3. Click `Install...` button
4. Navigate to the downloaded ZIP file and select it
5. Enable the addon by checking the checkbox next to "BRaaS-HPC-XMLMaterial"

## Usage

### Accessing the Addon

Once installed, the addon adds a new panel to Blender's **Shader Editor**:

1. Switch to the **Shading** workspace or open the **Shader Editor**
2. Look for the **XML** tab in the right sidebar (press `N` if the sidebar is hidden)
3. The panel contains two buttons: **Export Shader** and **Export Node**

### Exporting a Complete Shader

To export an entire shader material:

1. Select an object with a material in your scene
2. Open the **Shader Editor** with the material's node tree visible
3. In the **XML** panel (right sidebar), click **Export Shader**
4. The addon will generate XML code and display it in Blender's **Text Editor**
5. Open the **Text Editor** window to view the exported XML (look for a text block named "XML_EXPORT")
6. You can save this text to a file or copy it for use in external applications

### Exporting a Single Node

To export an individual node:

1. In the **Shader Editor**, select the node you want to export (click on it to make it active)
2. In the **XML** panel (right sidebar), click **Export Node**
3. The addon will generate XML code for just that node and display it in the **Text Editor**
4. Open the **Text Editor** to view the exported XML in "XML_EXPORT"

### Understanding the Output

The conversion follows Blender's Cycles synchronization (`intern/cycles/blender/shader.cpp`), so
CyclesPhi builds the same shader graph as Cycles inside Blender. The exported XML includes:

- **Shader root element**: The shader name (`default_background` for a World, which CyclesPhi
  assigns to the scene background) and the material settings as `<socket>` children
- **Node elements**: The Cycles node type (e.g. `principled_bsdf`) and a unique node name
- **Socket elements**: Node parameters and input values, written with both the Cycles socket
  `name` and `ui_name`, which the reader requires to match
- **Connect elements**: Links between Cycles sockets; `output` is the shader graph output

Node groups are inlined, reroutes and muted nodes are resolved, and only the active Cycles
material output is used, all connected through proxy nodes (`convert_<type>_to_<type>`) like in
Blender.

Example XML structure:
```xml
<?xml version="1.0" ?>
<shader name="Material">
  <socket name="volume_step_rate" ui_name="Volume Step Rate" value="1.0" />
  <principled_bsdf name="Principled BSDF">
    <socket name="base_color" ui_name="Base Color" value="0.8 0.8 0.8 0.0" />
    <socket name="roughness" ui_name="Roughness" value="0.5" />
  </principled_bsdf>
  <connect from_node="Principled BSDF" from_socket="BSDF" from_socket_ui="BSDF"
           to_node="output" to_socket="surface" to_socket_ui="Surface" />
</shader>
```

Array values (color ramps, curves) are written inline, as read by
`xml_read_shader_graph_from_string()`. When the shader is part of a scene file loaded with its
`.xml.bin` companion, pass a `bytearray` as `binary` to `export_shader()`; the arrays are then
appended to it and the sockets hold byte offsets into it.

Not exported: Script (OSL) nodes, sampled attribute outputs of the Raycast node, and Boolean Math,
Integer Math and Get Vector Component nodes (not available in CyclesPhi). Packed and generated
images are exported by their file path.

## Technical Details

### Supported Node Types

The addon maps Blender's Cycles shader nodes to XML elements. The mapping includes:

- **Shaders**: Add Shader, Mix Shader, Principled BSDF, Diffuse BSDF, Glossy BSDF, Glass BSDF, Refraction BSDF, Emission, Transparent BSDF, Translucent BSDF, Subsurface Scattering, Principled Hair BSDF, Toon BSDF, Sheen BSDF, and more
- **Textures**: Image Texture, Noise Texture, Wave Texture, Voronoi Texture, Magic Texture, Gradient Texture, Brick Texture, Checker Texture, Environment Texture, IES Texture, Sky Texture, White Noise Texture
- **Color**: RGB, MixRGB, Mix Color, Brightness/Contrast, Gamma, Hue/Saturation, Invert, RGB Curves, Color Ramp, Combine/Separate RGB/HSV/Color
- **Vector**: Mapping, Normal Map, Bump, Vector Transform, Vector Rotate, Vector Curves, Combine/Separate XYZ
- **Input**: Texture Coordinate, Geometry, Camera Data, Layer Weight, Fresnel, Object Info, Attribute, UV Map, Tangent, Wireframe, Ambient Occlusion
- **Math**: Math, Vector Math, Map Range, Clamp
- **Other**: Value, RGB input nodes, Float Curve nodes

### File Structure

- `__init__.py`: Addon registration and metadata
- `braas_hpc_xmlmaterial_panel.py`: GUI panel and operators
- `braas_hpc_xmlmaterial_convert.py`: Core export logic and XML generation
- `braas_hpc_xmlmaterial_map.py`: Blender node to Cycles node class mapping
- `braas_hpc_xmlmaterial_sockets.py`: Cycles node sockets, generated from the CyclesPhi sources by
  `tools/generate_cycles_sockets.py` (re-run it when the Cycles shader nodes change:
  `python tools/generate_cycles_sockets.py <cyclesphi_root>`)
- `braas_hpc_xmlmaterial_pref.py`: Addon preferences (currently minimal)

# License
This software is licensed under the terms of the [GNU General Public License](https://github.com/It4innovations/braas-hpc-xmlmaterial-addon/blob/main/LICENSE).


# Acknowledgement
This work was supported by the Ministry of Education, Youth and Sports of the Czech Republic through the e-INFRA CZ (ID:90254).

This work was supported by the SPACE project. This project has received funding from the European High- Performance Computing Joint Undertaking (JU) under grant agreement No 101093441. This project has received funding from the Ministry of Education, Youth and Sports of the Czech Republic (ID: MC2304).