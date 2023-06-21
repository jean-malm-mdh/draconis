import sys
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from AST.pou import Program
from Web_GUI.parser.AST.connections import ConnectionDirection
from Web_GUI.parser.AST.fbdobject_base import Point

fonts = {"Arial_Unicode": "/Library/Fonts/Arial Unicode.ttf"}


def render_line(line:Tuple[Point, Point], scaler, info_font, draw):
    s_p, e_p = line
    # No idea why extra scaling of 2.0 is needed here, to put lines in correct locations compared to blocks.
    s_s_x, s_s_y, e_s_x, e_s_y = map(scaler, (s_p.x * 2, s_p.y * 2, e_p.x * 2, e_p.y * 2))
    draw.line((s_s_x, s_s_y, e_s_x, e_s_y), fill="black", width=2)


def render_lines(lines, scaler, info_font, draw):
    for line in lines:
        render_line(line, scaler, info_font, draw)

def render_checker_grid_background(_w, _h, _grid_box_size, info_font, draw, scaler):
    w, h, grid_box_size = map(scaler, (_w, _h, _grid_box_size))
    draw.rectangle((0, 0, w, h), outline="black", width=1)
    for i in range(1, h // grid_box_size):
        draw.line((i*grid_box_size, 0, i*grid_box_size, h), fill="black", width=1)
        if i % 5 == 0:
            draw.text((i*grid_box_size, 0), text=str(i*_grid_box_size), font=info_font, fill="black")
    for i in range(1, w // grid_box_size):
        draw.line((0, i*grid_box_size, w, i*grid_box_size), fill="black", width=1)
        if i % 5 == 0:
            draw.text((0, i*grid_box_size), text=str(i*_grid_box_size), font=info_font, fill="black")


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

    render_lines(program.lines, scaler, info_font, draw)
    if sys.gettrace() is not None:
        render_checker_grid_background(_width, _height, _grid_box_size=10, info_font=info_font, draw=draw, scaler=scaler)

    im.save(img_result_path)


def render_blocks(blocks, scaler, font, canvas):
    for b in blocks:
        render_block(b, scaler, font, canvas)


def render_port_block(block, scaler, font, canvas):
    l, t, r, b = map(scaler, block.data.boundary_box.getAsTuple())
    canvas.rectangle((l, t, r, b), outline="purple", width=2)
    expr_text = block.getVarExpr()
    text_width, text_height = canvas.textsize(expr_text, font=font)
    block_width_scaled = r-l
    text_offset_x = (block_width_scaled - text_width) // 2
    text_offset_y = 0
    canvas.text((l+text_offset_x, t+text_offset_y), expr_text, font=font, fill="black")


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
        draw_port_box(inp, l, t, scaler, "red", canvas)
    for outp in output_connections:
        draw_port_box(outp, l, t, scaler, "green", canvas)
    name = block.data.type
    text_width, text_height = canvas.textsize(name, text_font)
    block_width_scaled = r-l
    text_offset_x = (block_width_scaled - text_width) // 2
    text_offset_y = text_height // 2
    # Draw block name
    canvas.text((l+text_offset_x, t+text_offset_y), name, font=text_font, fill="black")

def draw_port_box(port_coord, block_left_coord, block_top_coord, scaler, color, draw):
    port_box_width, port_box_height = map(scaler, (4, 2))
    offset_x, offset_y = map(scaler, (port_coord.data.position.x, port_coord.data.position.y))
    scaling_x = (scaler(2) if port_coord.connectionDir == ConnectionDirection.Output else scaler(-2))
    inp_pos_x, inp_pos_y = block_left_coord + offset_x + scaling_x, block_top_coord + offset_y
    draw.rectangle((inp_pos_x - (port_box_width // 2), inp_pos_y - (port_box_height // 2),
                    inp_pos_x + (port_box_width // 2), inp_pos_y + (port_box_height // 2)), fill=color)