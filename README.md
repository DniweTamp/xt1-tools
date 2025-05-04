# xt1-tools
## dds to xt1
### Usage instructions:
- Drag and drop dds file on the exe to create an xt1 file.
- Only supports dds files with DX10 header.
- Only tested with dds files saved with NVTT
- Supports exporting BCn formats as well as ASTC, with properly tiled mipmaps (using tegra-swizzle).
## Noesis plugin
### Installation instructions:
- Put the .py file in `Noesis\plugins\python`.
### Usage instructions:
- You can just open any .xt1 file extracted by `wtb_wta_extractor.rb` from [bayonetta_tools](https://github.com/Kerilk/bayonetta_tools)
- You can export any image from noesis straight to .xt1, by default it will export to `ASTC_8x8_UNORM`, but you can specify other formats using additional arguments (see screenshot)
- Noesis also supports commandline mode: `noesis.exe ?cmode input.png output.xt1 -xt1_8x8 -xt1_SRGB`
### Known issues:
- Unorthodox formats like `ASTC_6x6` etc. will appear correctly in noesis, but won't display properly ingame.
- Some very specific image resolutions will not tile correctly. You can work around this by resizing your input texture

For convenience I also made batch files that use noesis cli, you need to edit path to noesis exe on top of each one and then you can just drag and drop any image on it to generate .xt1 file
