import sys
from PIL import Image, ImageDraw, ImageFont
from AST.pou import Program

fonts = {"Arial_Unicode": "/Library/Fonts/Arial Unicode.ttf"}
def generate_image_of_program(program: Program, img_result_path: str, scale=1.0):
    """
    Generate an image of the program
    Args:
        program: The program to render into an image
        img_result_path: The path to the result image
        scale: The scaling factor for the rendering

    Returns:
        if OK, returns path to created image file

    """
    def scaler(int_val):
        return int(int_val * scale)
    _width, _height = 250, 250

    width = scaler(_width)
    height = scaler(_height)
    im = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(im)
    name_font = ImageFont.truetype(fonts["Arial_Unicode"], 20)
    info_font = ImageFont.truetype(fonts["Arial_Unicode"], 10)
    text = program.progName
    text_width, text_height = draw.textsize(text, font=name_font)
    text_x = (width - text_width) // 2
    text_y = text_height // 2
    draw.text((text_x, text_y), text, font=name_font, fill="black")

    # render the FBD blocks
    render_blocks(program.behaviourElements, scaler, info_font, draw)

    im.save(img_result_path)


def render_blocks(blocks, scaler, font, canvas):
    for b in blocks:
        render_block(b, scaler, font, canvas)


def render_port_block(b, scaler, font, canvas):
    l, t, r, b = map(scaler, b.data.boundary_box.getAsTuple())
    canvas.rectangle((l, t, r, b), outline="purple", width=2)


def render_block(b, scaler, font, canvas):
    if b.getBlockType() == "FunctionBlock":
        render_fbd_block(b, scaler, font, canvas)
    elif b.getBlockType() == "Port":
        render_port_block(b, scaler, font, canvas)


def render_fbd_block(block, scaler, text_font: ImageFont, canvas: ImageDraw):
    inputs = block.getInputVars()
    input_connections = [i.connectionPoint for i in inputs]
    outputs = block.getOutputVars()
    output_connections = [i.connectionPoint for i in outputs]
    l, t, r, b = map(scaler, block.data.boundary_box.getAsTuple())
    canvas.rectangle((l, t, r, b), outline="black", width=2)

    # Draw ports
    for inp in input_connections:
        draw_port_box(inp.data.position, l, t, scaler, "red", canvas)
    for outp in output_connections:
        draw_port_box(outp.data.position, l, t, scaler, "green", canvas)
    name = block.data.type
    text_width, text_height = canvas.textsize(name, text_font)
    block_width_scaled = r-l
    text_offset_x = (block_width_scaled - text_width) // 2
    text_offset_y = text_height // 2
    # Draw block name
    canvas.text((l+text_offset_x, t+text_offset_y), name, font=text_font, fill="black")

def draw_port_box(port_coord, block_left_coord, block_top_coord, scaler, color, draw):
    port_box_width, port_box_height = map(scaler, (4, 2))
    offset_x, offset_y = map(scaler, (port_coord.x, port_coord.y))
    inp_pos_x, inp_pos_y = block_left_coord + offset_x, block_top_coord + offset_y
    draw.rectangle((inp_pos_x - (port_box_width // 2), inp_pos_y - (port_box_height // 2),
                    inp_pos_x + (port_box_width // 2), inp_pos_y + (port_box_height // 2)), fill=color)