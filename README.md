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

- **Blender**: Version 4.5.0 or higher
- **Operating System**: Windows, macOS, or Linux (any platform that supports Blender 4.5+)

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

The exported XML includes:

- **Shader root element**: Contains the shader name
- **Node elements**: Each node is represented with its type and name
- **Socket elements**: Node input parameters with their default values
- **Connect elements**: Links between nodes, showing data flow
- **Attributes**: Node-specific properties (e.g., blend mode, interpolation type)

Example XML structure:
```xml
<?xml version="1.0" ?>
<shader name="Material">
  <principled_bsdf name="Principled BSDF">
    <socket ui_name="Base Color" value="0.8 0.8 0.8 1.0"/>
    <socket ui_name="Metallic" value="0.0"/>
    <socket ui_name="Roughness" value="0.5"/>
  </principled_bsdf>
  <connect from="Principled BSDF BSDF" to="Material Output Surface"/>
</shader>
```

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
- `braas_hpc_xmlmaterial_map.py`: Node type mappings between Blender and XML
- `braas_hpc_xmlmaterial_pref.py`: Addon preferences (currently minimal)

# License
This software is licensed under the terms of the [GNU General Public License](https://github.com/It4innovations/braas-hpc-xmlmaterial-addon/blob/main/LICENSE).


# Acknowledgement
This work was supported by the Ministry of Education, Youth and Sports of the Czech Republic through the e-INFRA CZ (ID:90254).

This work was supported by the SPACE project. This project has received funding from the European High- Performance Computing Joint Undertaking (JU) under grant agreement No 101093441. This project has received funding from the Ministry of Education, Youth and Sports of the Czech Republic (ID: MC2304).