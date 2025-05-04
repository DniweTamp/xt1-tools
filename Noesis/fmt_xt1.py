from inc_noesis import *

def registerNoesisTypes():
    handle = noesis.register("XT1 Texture", ".xt1")
    noesis.setHandlerTypeCheck(handle, xt1CheckType)
    noesis.setHandlerLoadRGBA(handle, xt1LoadRGBA)
    noesis.setHandlerWriteRGBA(handle, xt1WriteRGBA)

    # options based on FORMAT_DETAILS
    option_groups = {
        "ASTC": ["12x12", "10x10", "8x8", "6x6", "4x4"],
        "BC": ["BC1", "BC7"]
    }
    for group, sizes in option_groups.items():
        for size in sizes:
            option_name = "-xt1_{}".format(size.lower()) # standardize option names
            description = "Export {} XT1 Texture.".format(size.upper())
            if group == "ASTC" and size == "8x8":
                description = "Export {} XT1 Texture (Default).".format(size.upper())
            noesis.addOption(handle, option_name, description, 0)

    noesis.addOption(handle, "-xt1_UNORM", "Export UNORM XT1 Texture (Default).", 0)
    noesis.addOption(handle, "-xt1_SRGB", "Export SRGB XT1 Texture.", 0)

    return 1

FORMAT_DETAILS = {
    0x01: (1, 1, 1, "R8", "UNORM", rapi.imageDecodeRaw, "r8", None),
    0x25: (4, 1, 1, "R8G8B8A8", "UNORM", rapi.imageDecodeRaw, "r8g8b8a8", None),
    0x42: (8, 4, 4, "BC1", "UNORM", rapi.imageDecodeDXT, noesis.NOESISTEX_DXT1, "-xt1_BC1"),
    0x43: (16, 4, 4, "BC2", "UNORM", rapi.imageDecodeDXT, noesis.NOESISTEX_DXT3, None),
    0x44: (16, 4, 4, "BC3", "UNORM", rapi.imageDecodeDXT, noesis.NOESISTEX_DXT5, None),
    0x45: (8, 4, 4, "BC4", "UNORM", rapi.imageDecodeDXT, noesis.FOURCC_ATI1, None),
    0x46: (8, 4, 4, "BC1", "SRGB", rapi.imageDecodeDXT, noesis.NOESISTEX_DXT1, "-xt1_BC1"),
    0x47: (16, 4, 4, "BC2", "SRGB", rapi.imageDecodeDXT, noesis.NOESISTEX_DXT3, None),
    0x48: (16, 4, 4, "BC3", "SRGB", rapi.imageDecodeDXT, noesis.NOESISTEX_DXT5, None),
    0x49: (8, 4, 4, "BC4", "SNORM", rapi.imageDecodeDXT, noesis.FOURCC_ATI1, None),
    0x4B: (16, 4, 4, "BC5", "UNORM", rapi.imageDecodeDXT, noesis.FOURCC_ATI2, None),
    0x4C: (16, 4, 4, "BC5", "SRGB", rapi.imageDecodeDXT, noesis.FOURCC_ATI2, None),
    0x4D: (16, 4, 4, "BC7", "UNORM", rapi.imageDecodeDXT, noesis.FOURCC_BC7, "-xt1_BC7"),
    0x4E: (16, 4, 4, "BC7", "SRGB", rapi.imageDecodeDXT, noesis.FOURCC_BC7, "-xt1_BC7"),
    0x50: (16, 4, 4, "BC6H_UF16", "SRGB", rapi.imageDecodeDXT, noesis.FOURCC_BC6H, None),
    0x2D: (16, 4, 4, "ASTC_4x4", "UNORM", rapi.imageDecodeASTC, None, "-xt1_4x4"),
    0x38: (16, 8, 8, "ASTC_8x8", "UNORM", rapi.imageDecodeASTC, None, "-xt1_8x8"),
    0x3A: (16, 12, 12, "ASTC_12x12", "UNORM", rapi.imageDecodeASTC, None, "-xt1_12x12"),
    0x79: (16, 4, 4, "ASTC_4x4", "UNORM", rapi.imageDecodeASTC, None, "-xt1_4x4"),
    0x7B: (16, 5, 5, "ASTC_5x5", "UNORM", rapi.imageDecodeASTC, None, None),
    0x7D: (16, 6, 6, "ASTC_6x6", "UNORM", rapi.imageDecodeASTC, None, "-xt1_6x6"),
    0x80: (16, 8, 8, "ASTC_8x8", "UNORM", rapi.imageDecodeASTC, None, "-xt1_8x8"),
    0x84: (16, 10, 10, "ASTC_10x10", "UNORM", rapi.imageDecodeASTC, None, "-xt1_10x10"),
    0x87: (16, 4, 4, "ASTC_4x4", "SRGB", rapi.imageDecodeASTC, None, "-xt1_4x4"),
    0x89: (16, 5, 5, "ASTC_5x5", "SRGB", rapi.imageDecodeASTC, None, None),
    0x8B: (16, 6, 6, "ASTC_6x6", "SRGB", rapi.imageDecodeASTC, None, "-xt1_6x6"),
    0x8E: (16, 8, 8, "ASTC_8x8", "SRGB", rapi.imageDecodeASTC, None, "-xt1_8x8"),
    0x92: (16, 10, 10, "ASTC_10x10", "SRGB", rapi.imageDecodeASTC, None, "-xt1_10x10"),
    0x94: (16, 12, 12, "ASTC_12x12", "SRGB", rapi.imageDecodeASTC, None, "-xt1_12x12"),
}

class XT1Image:
    def __init__(self, reader):
        self.reader = reader
        self.header_data = {}

    def parseHeader(self):
        bs = self.reader
        bs.seek(0, NOESEEK_ABS)
        self.header_data['magic'] = bs.readBytes(4)
        if self.header_data['magic'] != b"XT1\0":
            return -1
        self.header_data['u_a'] = bs.readUInt()
        self.header_data['textureSize'] = bs.readUInt64()
        self.header_data['headerSize'] = bs.readUInt()
        self.header_data['numMipMap'] = bs.readUInt()
        self.header_data['textureType'] = bs.readUInt()
        self.header_data['format'] = bs.readUInt()
        self.header_data['width'] = bs.readUInt()
        self.header_data['height'] = bs.readUInt()
        self.header_data['depth'] = bs.readUInt()
        self.header_data['specialPad'] = bs.readUInt()
        self.header_data['blockHeightLog2'] = bs.readUByte()
        self.header_data['flags'] = bs.readUByte()
        self.header_data['u_b'] = bs.readUByte()
        self.header_data['u_c'] = bs.readUByte()
        self.header_data['u_f'] = bs.readUInt()
        return 0

    def decode(self):
        bs = self.reader
        remainingBuffer = bs.getBuffer()[self.header_data['headerSize']:self.header_data['headerSize'] + self.header_data['textureSize']]
        format_id = self.header_data['format']
        format_details = FORMAT_DETAILS.get(format_id)

        if not format_details:
            print("Unsupported format ID: {}".format(hex(format_id)))
            return None

        blockSize, blockWidth, blockHeight, formatName, colorSpace, decoderFunc, formatParam = format_details[:7]

        widthInBlocks = div_rnd_up(self.header_data['width'], blockWidth)
        heightInBlocks = div_rnd_up(self.header_data['height'], blockHeight)
        block_height_log2 = self.header_data['blockHeightLog2']
        special_pad = self.header_data['specialPad']
        flags = self.header_data['flags']

        if flags & 4: # directly from header data
            untiledData = image_untile_block_linear_gobs2(remainingBuffer, widthInBlocks, heightInBlocks, 1 << block_height_log2, blockSize, special_pad)
        else:
            untiledData = rapi.imageUntileBlockLinearGOB(remainingBuffer, widthInBlocks, heightInBlocks, blockSize, 1 << block_height_log2)

        if decoderFunc:
            decode_args = [untiledData, self.header_data['width'], self.header_data['height']]
            if decoderFunc == rapi.imageDecodeASTC:
                decode_args = [untiledData, blockWidth, blockHeight, 1, self.header_data['width'], self.header_data['height'], 1]
            elif formatParam:
                decode_args.append(formatParam)
            return decoderFunc(*decode_args)
        else:
            print("No decoder function defined for format: {}".format(formatName))
            return None


def div_rnd_up(x, y):
    return (x + y - 1) // y

def rnd_up(x, y):
    return ((x - 1) | (y - 1)) + 1

def get_offset_block_linear(x, y, w, bytes_per_elem, block_height, special_pad):
    image_width_in_gobs = div_rnd_up(rnd_up(w, special_pad) * bytes_per_elem, 64)
    gob_offset = (
        (y // (8 * block_height)) * 512 * block_height * image_width_in_gobs +
        (x * bytes_per_elem // 64) * 512 * block_height +
        (y % (8 * block_height) // 8) * 512
    )
    x *= bytes_per_elem
    return gob_offset + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16)

def image_untile_block_linear_gobs2(src, width, height, block_height, bytes_per_elem, special_pad):
    dest_size = width * height * bytes_per_elem
    dest = bytearray(dest_size)
    for y in range(height):
        for x in range(width):
            pos_tiled = get_offset_block_linear(x, y, width, bytes_per_elem, block_height, special_pad)
            pos_untiled = (y * width + x) * bytes_per_elem
            dest[pos_untiled:pos_untiled + bytes_per_elem] = src[pos_tiled:pos_tiled + bytes_per_elem]
    return dest

def image_tile_block_linear_gobs2(src, width, height, block_height, bytes_per_elem, special_pad):
    dest_size = div_rnd_up(rnd_up(width, special_pad) * bytes_per_elem, 64) * 512 * block_height * div_rnd_up(height, 8 * block_height)
    dest = bytearray(dest_size)
    for y in range(height):
        for x in range(width):
            pos_tiled = get_offset_block_linear(x, y, width, bytes_per_elem, block_height, special_pad)
            pos_untiled = (y * width + x) * bytes_per_elem
            dest[pos_tiled:pos_tiled + bytes_per_elem] = src[pos_untiled:pos_untiled + bytes_per_elem]
    return dest

def xt1CheckType(data):
    xt1 = XT1Image(NoeBitStream(data))
    if xt1.parseHeader() != 0:
        return 0
    return 1

def xt1LoadRGBA(data, texList):
    xt1 = XT1Image(NoeBitStream(data))
    if xt1.parseHeader() != 0:
        return 0

    format_id = xt1.header_data['format']
    format_details = FORMAT_DETAILS.get(format_id)
    width = xt1.header_data['width']
    height = xt1.header_data['height']

    if format_details:
        format_name = format_details[3]
        color_space = format_details[4]
        print("Loaded XT1 Texture: {} ({}_{}), {}x{}".format(hex(format_id), format_name, color_space, width, height))
    else:
        print("Warning: Unknown XT1 Format ID: {}.".format(hex(format_id)))

    texData = xt1.decode()
    if not texData:
        return 0
    texList.append(NoeTexture("xt1tex", width, height, texData, noesis.NOESISTEX_RGBA32))
    return 1

def getTextureFormat():
    requested_format_id = None
    requested_srgb = noesis.optWasInvoked("-xt1_SRGB")

    for format_id, details in FORMAT_DETAILS.items():
        option = details[7] if len(details) > 7 else None # get option if it exists
        if option and noesis.optWasInvoked(option):
            format_type = details[4]
            if requested_srgb and format_type == "SRGB":
                requested_format_id = format_id
                break # prioritize SRGB if both SRGB option and format option are set
            elif not requested_srgb and format_type == "UNORM":
                requested_format_id = format_id
                break

    if requested_format_id:
        return requested_format_id

    if requested_srgb: # if only SRGB is requested, find any SRGB format (default BC7_SRGB)
        for format_id, details in FORMAT_DETAILS.items():
            if details[4] == "SRGB":
                return format_id

    return 0x80  # default to ASTC_8x8_UNORM if no specific or valid format is found


def xt1WriteRGBA(data, width, height, bs):
    textureFormat = getTextureFormat()
    flags = 0x0
    specialPad = 0x0

    formatDetails = FORMAT_DETAILS.get(textureFormat)
    if not formatDetails:
        print("Warning: Could not determine texture format, defaulting to ASTC_8x8_UNORM.")
        textureFormat = 0x80 # default if getTextureFormat fails unexpectedly
        formatDetails = FORMAT_DETAILS.get(textureFormat)

    blockSize, blockWidth, blockHeight, formatName = formatDetails[:4]
    widthInBlocks = div_rnd_up(width, blockWidth)
    heightInBlocks = div_rnd_up(height, blockHeight)

    encoder_args = [data, 4, width, height]
    encoder_func = None

    if formatName.startswith("ASTC"):
        encoder_func = rapi.imageEncodeASTC
        encoder_args = [data, blockWidth, blockHeight, 1, width, height, 1, 2]
    elif formatName.startswith("BC"):
        encoder_func = rapi.imageEncodeDXT
        encoder_args.append(formatDetails[6]) # format parameter

    if encoder_func is None:
        print("Error: No encoder function found for format {}".format(formatName))
        return 0

    texturedata = encoder_func(*encoder_args)


    maxBlockHeight = rapi.imageBlockLinearGOBMaxBlockHeight(heightInBlocks)

    # block tiling for specific formats
    if formatName in ["ASTC_12x12", "ASTC_10x10", "ASTC_6x6", "ASTC_5x5", "ASTC_4x4"]:
        flags = 0x4
        specialPad = 0x20
        texturedata = image_tile_block_linear_gobs2(texturedata, widthInBlocks, heightInBlocks, 1 << maxBlockHeight, blockSize, specialPad)
    else:
        texturedata = rapi.imageTileBlockLinearGOB(texturedata, widthInBlocks, heightInBlocks, blockSize, 1 << maxBlockHeight)

    # write XT1 header (using dictionary for header data)
    bs.writeUInt(0x00315458) # "XT1" magic
    bs.writeUInt(0x01000101) # u_a
    bs.writeUInt64(len(texturedata)) # Texture size
    bs.writeUInt(0x38) # Header size
    bs.writeUInt(0x01) # Number of mipmaps
    bs.writeUInt(0x01) # 2D texture
    bs.writeUInt(textureFormat)
    bs.writeUInt(width)
    bs.writeUInt(height)
    bs.writeUInt(0x01)  # Depth
    bs.writeUInt(specialPad)
    bs.writeByte(maxBlockHeight)
    bs.writeByte(flags)  # flags
    bs.writeByte(0x00)  # u_b
    bs.writeByte(0x00)  # u_c
    bs.writeUInt(0x00010007)  # u_f
    bs.writeBytes(texturedata)
    return 1