use std::env;
use std::fs::File;
use std::io::{Read, Write, Seek, SeekFrom};
use std::path::Path;
use ddsfile::DxgiFormat; // DxgiFormat is only for the display helper
use tegra_swizzle::{surface::swizzle_surface, surface::BlockDim};
use num_traits::cast::FromPrimitive;
use std::num::NonZeroU32;

struct DdsHeaderInfo {
    width: u32,
    height: u32,
    mipmap_count: u32,
    dxgi_format_value: u32,
    data: Vec<u8>,
}

fn read_dds_header(file: &mut File) -> Result<DdsHeaderInfo, Box<dyn std::error::Error>> {
    let header_size = 128 + 20;
    let mut header_bytes = vec![0u8; header_size];
    file.read_exact(&mut header_bytes)?;
    let read_u32_le = |slice: &[u8]| -> Result<u32, std::array::TryFromSliceError> {
        Ok(u32::from_le_bytes(slice.try_into()?))
    };

    // Validate DDS header
    let dw_magic = read_u32_le(&header_bytes[0..4])?;
    if dw_magic != 0x20534444 { // 'DDS '
        return Err("Invalid DDS magic number".into());
    }

    let dw_size = read_u32_le(&header_bytes[4..8])?;
    if dw_size != 124 {
         eprintln!("Warning: DDS header size field is {} instead of 124.", dw_size);
    }

    let dw_height = read_u32_le(&header_bytes[12..16])?;
    let dw_width = read_u32_le(&header_bytes[16..20])?;
    let dw_mipmap_count = read_u32_le(&header_bytes[28..32])?;

    let ddspf_offset = 76;
    let ddspf_size = read_u32_le(&header_bytes[ddspf_offset..ddspf_offset+4])?;
    if ddspf_size != 32 {
        return Err(format!("Invalid DDS pixel format size: {}", ddspf_size).into());
    }

    let ddspf_flags = read_u32_le(&header_bytes[ddspf_offset+4..ddspf_offset+8])?;
    let ddspf_fourcc = read_u32_le(&header_bytes[ddspf_offset+8..ddspf_offset+12])?;

    const DDPF_FOURCC: u32 = 0x4;
    const FOURCC_DX10: u32 = 0x30315844;

    if !(ddspf_flags & DDPF_FOURCC != 0 && ddspf_fourcc == FOURCC_DX10) {
         return Err("DDS file does not indicate a DX10 header (missing DDPF_FOURCC or FourCC is not 'DX10')".into());
    }
    let dx10_header_offset = 128;
    let dxgi_format_value = read_u32_le(&header_bytes[dx10_header_offset..dx10_header_offset+4])?;
    let mut data = Vec::new();
    file.read_to_end(&mut data)?;

    Ok(DdsHeaderInfo {
        width: dw_width,
        height: dw_height,
        // The mipmap count in the DDS header can be 0 for files with only the base image.
        // Assume at least 1 mipmap if the header says 0.
        mipmap_count: dw_mipmap_count.max(1),
        dxgi_format_value,
        data,
    })
}


fn get_user_format(dxgi_format_value: u32) -> Option<u32> {
    match dxgi_format_value {
        71 => Some(0x42), // DXGI_FORMAT_BC1_UNorm
        72 => Some(0x46), // DXGI_FORMAT_BC1_UNorm_sRGB
        74 => Some(0x43), // DXGI_FORMAT_BC2_UNorm
        75 => Some(0x47), // DXGI_FORMAT_BC2_UNorm_sRGB
        77 => Some(0x44), // DXGI_FORMAT_BC3_UNorm
        78 => Some(0x48), // DXGI_FORMAT_BC3_UNorm_sRGB
        80 => Some(0x45), // DXGI_FORMAT_BC4_UNorm
        81 => Some(0x49), // DXGI_FORMAT_BC4_SNorm
        83 => Some(0x4B), // DXGI_FORMAT_BC5_UNorm
        84 => Some(0x4C), // DXGI_FORMAT_BC5_SNorm
        98 => Some(0x4D), // DXGI_FORMAT_BC7_UNorm
        99 => Some(0x4E), // DXGI_FORMAT_BC7_UNorm_sRGB
        95 => Some(0x50), // DXGI_FORMAT_BC6H_UF16
        96 => Some(0x51), // DXGI_FORMAT_BC6H_SF16

        134 => Some(0x79), // DXGI_FORMAT_ASTC_4X4_UNORM
        135 => Some(0x87), // DXGI_FORMAT_ASTC_4X4_UNORM_SRGB
        142 => Some(0x7B), // DXGI_FORMAT_ASTC_5X5_UNORM
        143 => Some(0x89), // DXGI_FORMAT_ASTC_5X5_UNORM_SRGB
        150 => Some(0x7D), // DXGI_FORMAT_ASTC_6X6_UNORM
        151 => Some(0x8B), // DXGI_FORMAT_ASTC_6X6_UNORM_SRGB
        162 => Some(0x80), // DXGI_FORMAT_ASTC_8X8_UNORM
        163 => Some(0x8E), // DXGI_FORMAT_ASTC_8X8_UNORM_SRGB
        178 => Some(0x84), // DXGI_FORMAT_ASTC_10X10_UNORM
        179 => Some(0x92), // DXGI_FORMAT_ASTC_10X10_UNORM_SRGB
        186 => Some(0x3A), // DXGI_FORMAT_ASTC_12X12_UNORM
        187 => Some(0x94), // DXGI_FORMAT_ASTC_12X12_UNORM_SRGB

        _ => None,
    }
}

fn get_block_size_in_bytes(dxgi_format_value: u32) -> Option<usize> {
    match dxgi_format_value {
        71 | 72 | 80 | 81 | 95 | 96 => Some(8), // BC1, BC4, BC6H
        74 | 75 | 77 | 78 | 83 | 84 | 98 | 99 => Some(16), // BC2, BC3, BC5, BC7
        134 | 135 | 142 | 143 | 150 | 151 | 162 | 163 | 178 | 179 | 186 | 187 => Some(16), // ASTC
        _ => None,
    }
}

fn get_block_dim(dxgi_format_value: u32) -> Option<BlockDim> {
    match dxgi_format_value {
        71 | 72 | 74 | 75 | 77 | 78 | 80 | 81 | 83 | 84 | 95 | 96 | 98 | 99
         => Some(BlockDim { width: NonZeroU32::new(4).unwrap(), height: NonZeroU32::new(4).unwrap(), depth: NonZeroU32::new(1).unwrap(), }),
        134 | 135 => Some(BlockDim { width: NonZeroU32::new(4).unwrap(), height: NonZeroU32::new(4).unwrap(), depth: NonZeroU32::new(1).unwrap(), }), // 4x4
        142 | 143 => Some(BlockDim { width: NonZeroU32::new(5).unwrap(), height: NonZeroU32::new(5).unwrap(), depth: NonZeroU32::new(1).unwrap(), }), // 5x5
        150 | 151 => Some(BlockDim { width: NonZeroU32::new(6).unwrap(), height: NonZeroU32::new(6).unwrap(), depth: NonZeroU32::new(1).unwrap(), }), // 6x6
        162 | 163 => Some(BlockDim { width: NonZeroU32::new(8).unwrap(), height: NonZeroU32::new(8).unwrap(), depth: NonZeroU32::new(1).unwrap(), }), // 8x8
        178 | 179 => Some(BlockDim { width: NonZeroU32::new(10).unwrap(), height: NonZeroU32::new(10).unwrap(), depth: NonZeroU32::new(1).unwrap(), }), // 10x10
        186 | 187 => Some(BlockDim { width: NonZeroU32::new(12).unwrap(), height: NonZeroU32::new(12).unwrap(), depth: NonZeroU32::new(1).unwrap(), }), // 12x12
        _ => None,
    }
}


fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("Usage: drag_and_drop_converter <input_dds_file>");
        return Err("No input file provided".into());
    }
    let input_path_str = &args[1];
    let input_path = Path::new(input_path_str);
    let output_dir = input_path.parent().unwrap_or_else(|| Path::new("."));
    let output_file_stem = input_path.file_stem().ok_or("Invalid input file name")?;
    let output_path = output_dir.join(output_file_stem).with_extension("xt1");
    let input_filename = input_path.display();
    let output_filename = output_path.display();

    println!("Attempting to read and parse header from {}...", input_filename);
    let mut file = File::open(input_path)?;
    let header_info = read_dds_header(&mut file)?;
    println!("Successfully parsed header.");

    // Extract info from manually read header
    let dxgi_format_value = header_info.dxgi_format_value;
    let width = header_info.width;
    let height = header_info.height;
    let total_mipmaps = header_info.mipmap_count;
    let dds_data = header_info.data;


    println!("Raw DXGI Format value: {}", dxgi_format_value);

    // This uses the ddsfile crate *only* for displaying a known format name.
    let dxgi_format_display = DxgiFormat::from_u32(dxgi_format_value)
        .map(|f| format!("{:?}", f))
        .unwrap_or_else(|| "Unknown/ASTC DXGI Format".to_string());
    println!("DXGI Format (enum display): {}", dxgi_format_display);


    let texture_format = get_user_format(dxgi_format_value).ok_or(format!("Unsupported raw DXGI format value: {}", dxgi_format_value))?;
    println!("Texture Format (XT1): {:#x}", texture_format);

    let block_size_in_bytes = get_block_size_in_bytes(dxgi_format_value).ok_or(format!("Could not determine block size for raw DXGI format value: {}", dxgi_format_value))?;
    println!("Block size in bytes: {}", block_size_in_bytes);

    let block_dim = get_block_dim(dxgi_format_value).ok_or(format!("Could not determine block dimensions for raw DXGI format value: {}", dxgi_format_value))?;
    println!("Block dimensions (pixels): {:?}", block_dim);


    println!("Width: {}, Height: {}", width, height);
    println!("Total Mipmaps: {}", total_mipmaps);

    let block_height_mip0_log2: u8;
    let block_height_mip0 = tegra_swizzle::block_height_mip0(tegra_swizzle::div_round_up(height, u32::from(block_dim.height)));
     match block_height_mip0 {
         tegra_swizzle::BlockHeight::One => block_height_mip0_log2 = 0,
         tegra_swizzle::BlockHeight::Two => block_height_mip0_log2 = 1,
         tegra_swizzle::BlockHeight::Four => block_height_mip0_log2 = 2,
         tegra_swizzle::BlockHeight::Eight => block_height_mip0_log2 = 3,
         tegra_swizzle::BlockHeight::Sixteen => block_height_mip0_log2 = 4,
         tegra_swizzle::BlockHeight::ThirtyTwo => block_height_mip0_log2 = 5,
     }
    println!("Block Height Mip0 (based on texture height): {:?}", block_height_mip0);


    println!("Attempting to tile data...");
    let tiled_data = swizzle_surface(
        width,
        height,
        1, // depth
        &dds_data,
        block_dim,
        None, // tile_mode
        block_size_in_bytes.try_into().expect("block_size_in_bytes should fit in u32"),
        total_mipmaps,
        1, // array_layer_count
    )?;
    println!("Successfully tiled data. Tiled data size: {} bytes", tiled_data.len());


    println!("Attempting to write {}...", output_filename);
    let mut output = File::create(output_path.clone())?;
    output.write_all(&0x00315458u32.to_le_bytes())?; // "XT1" (little endian)
    output.write_all(&0x01000101u32.to_le_bytes())?; // u_a
    output.write_all(&(tiled_data.len() as u64).to_le_bytes())?; // texture size (total swizzled data size)
    output.write_all(&0x38u32.to_le_bytes())?; // header size
    output.write_all(&total_mipmaps.to_le_bytes())?; // number of mipmaps
    output.write_all(&1u32.to_le_bytes())?; // 2D texture (0x01)
    output.write_all(&texture_format.to_le_bytes())?; // textureFormat
    output.write_all(&width.to_le_bytes())?; // width
    output.write_all(&height.to_le_bytes())?; // height
    output.write_all(&1u32.to_le_bytes())?; // depth
    output.write_all(&0u32.to_le_bytes())?; // specialPad
    output.write_all(&[block_height_mip0_log2 as u8])?; // maxBlockHeight
    output.write_all(&[0u8])?; // flags
    output.write_all(&[0u8])?; // u_b
    output.write_all(&[0u8])?; // u_c
    output.write_all(&65543u32.to_le_bytes())?; // u_f
    output.write_all(&tiled_data)?;
    println!("Successfully wrote {}", output_filename);

    Ok(())
}