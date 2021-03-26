Cloth Exporter Blender Addon
---
This is a custom made [Blender](https://blender.org) Addon that is targeted for the use case of my [GPUClothSimulationInUnity](https://github.com/voxell-tech/GPUClothSimulationInUnity) project.
This add-on converts any face with more than 3 vertices into proportional triangles (optional) and then exports it into a JSON file.

How to use?
---
1. Zip this repository in a `.zip` file or download a [release](https://github.com/voxell-tech/ClothExporter/releases).
2. Open Blender, go to `Edit > Preferences > Add-ons > Install` and choose the `.zip` file.
3. In the 3D View port, press `n` to view the side bar.
4. Select `Cloth Exporter` in the side bar.
5. Select a Mesh in the scene and press `Tab` into edit mode.
6. Once you are satisfied with the mesh, press `Transform to PBD`.
7. Choose your export location and export filename.
8. Press `Export Data for Unity`.
9. You will get an exported JSON file.

License
---
This project is under the GNU Public License, Version 3.
