import dataclasses
import sys
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from AST.pou import Program
from Web_GUI.parser.AST.connections import ConnectionDirection
from Web_GUI.parser.AST.fbdobject_base import Point


@dataclasses.dataclass
class DrawContext:
    canvas: ImageDraw
    fonts: dict[str, ImageFont]

    def __init__(self, img_width, img_height, scaler=None, bg_col="white"):
        self.image = Image.new("RGB", (img_width, img_height), color=bg_col)
        self.canvas = ImageDraw.Draw(self.image)
        self.fonts = {"__DEFAULT__": ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 10),
                      "__HEADER__": ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 20)}
        self.scaler = scaler or (lambda e: e)

    def save_image_to_file(self, path):
        self.image.save(path)

    def draw_text_centered(self, msg, position: Tuple[int, int], font_name, col="black"):
        font = self.fonts.get(font_name, None) or self.fonts["__DEFAULT__"]
        text_width, text_height = self.canvas.textsize(msg, font)
        p_x, p_y = position
        p_x -= (text_width // 2)
        p_y -= (text_height // 2)
        self.canvas.text((p_x, p_y), msg, fill=col, font=font)

    def draw_rect_filled(self, l_t, r_b, col):
        l, t = l_t
        r, b = r_b
        self.canvas.rectangle((l, t, r, b), fill=col)

    def draw_rect_outline(self, l_t, r_b, col, width):
        l, t = l_t
        r, b = r_b
        self.canvas.rectangle((l, t, r, b), outline=col, width=width)
    def render_message_box(self, pos_upper_left, header_msg, message, color, font, draw):
        header_font = self.fonts["__HEADER__"]
        header_width, header_height = draw.textsize(header_msg, header_font)
        message_width, message_height = draw.textsize(message, font)
        l, t = (pos_upper_left[0], pos_upper_left[1])
        header_message_offset_height = 10
        r, b = (l + max(header_width, message_width), t + header_height + message_height + header_message_offset_height)
        self.draw_rect_filled(pos_upper_left, (r, b), col=color)
        draw.text((l, t), header_msg, fill="black", font=header_font)
        draw.text((l, t + header_height + header_message_offset_height), message, fill="black", font=font)

    def render_block(self, b):
        render_block(b, self.scaler, self.fonts["__DEFAULT__"], self.canvas)

    def render_line(self, line: Tuple[Point, Point], col="black", width=1):
        s_p, e_p = line
        s_s_x, s_s_y, e_s_x, e_s_y = map(self.scaler, (s_p.x, s_p.y, e_p.x, e_p.y))
        self.canvas.line((s_s_x, s_s_y, e_s_x, e_s_y), fill=col, width=width)

    def render_checker_grid_background(self, _grid_box_size):
        info_font = self.fonts["__DEFAULT__"]
        w, h, grid_box_size = map(self.scaler, (self.image.size[0], self.image.size[1], _grid_box_size))
        self.canvas.rectangle((0, 0, w, h), outline="black", width=1)
        for i in range(1, h // grid_box_size):
            self.canvas.line((i * grid_box_size, 0, i * grid_box_size, h), fill="black", width=1)
            if i % 5 == 0:
                self.canvas.text((i * grid_box_size, 0), text=str(i * _grid_box_size), font=info_font, fill="black")
        for i in range(1, w // grid_box_size):
            self.canvas.line((0, i * grid_box_size, w, i * grid_box_size), fill="black", width=1)
            if i % 5 == 0:
                self.canvas.text((0, i * grid_box_size), text=str(i * _grid_box_size), font=info_font, fill="black")


def render_lines(lines, draw_context):
    for line in lines:
        # Not sure why scaling of 2.0 is required to get lines to proper places ...
        _line = (Point(line[0].x * 2, line[0].y * 2), (Point(line[1].x * 2, line[1].y * 2)))
        draw_context.render_line(_line, width=2)


def render_blocks(blocks, draw_context):
    for b in blocks:
        draw_context.render_block(b)


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

    _height, _width = get_program_width_height(program)
    width = scaler(_width)
    height = scaler(_height)
    draw_context = DrawContext(width, height, scaler, bg_col="white")
    text = program.progName
    text_x = width // 2
    draw_context.draw_text_centered(text, (text_x, 15), font_name="__HEADER__", col="black")

    # render the FBD blocks
    render_blocks(program.behaviourElements, draw_context)

    render_lines(program.lines, draw_context)
    if sys.gettrace() is not None:
        draw_context.render_checker_grid_background(_grid_box_size=10)
    draw_context.save_image_to_file(img_result_path)


def get_program_width_height(program):
    _width, _height = 100, 100
    # Find actual width and height, based on elements present
    for b in program.behaviourElements:
        _x, _y = b.data.boundary_box.bot_right.getAsTuple()
        _width = max(_width, _x)
        _height = max(_height, _y)
    for l in program.lines:
        s_p, e_p = l
        _width = max(_width, s_p.x, e_p.x)
        _height = max(_height, s_p.y, e_p.y)
    # Add some space for annotations etc
    _width += 50
    _height += 50
    return _height, _width


def render_block(b, scaler, font, canvas):
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
        block_width_scaled = r - l
        text_offset_x = (block_width_scaled - text_width) // 2
        text_offset_y = text_height // 2
        # Draw block name
        canvas.text((l + text_offset_x, t + text_offset_y), name, font=text_font, fill="black")

    def render_port_block(block, scaler, font, canvas):
        l, t, r, b = map(scaler, block.data.boundary_box.getAsTuple())
        canvas.rectangle((l, t, r, b), outline="purple", width=2)
        expr_text = block.getVarExpr()
        text_width, text_height = canvas.textsize(expr_text, font=font)
        block_width_scaled = r - l
        text_offset_x = (block_width_scaled - text_width) // 2
        text_offset_y = 0
        canvas.text((l + text_offset_x, t + text_offset_y), expr_text, font=font, fill="black")

    def draw_port_box(port_coord, block_left_coord, block_top_coord, scaler, color, draw):
        port_box_width, port_box_height = map(scaler, (4, 2))
        offset_x, offset_y = map(scaler, (port_coord.data.position.x, port_coord.data.position.y))
        scaling_x = (scaler(2) if port_coord.connectionDir == ConnectionDirection.Output else scaler(-2))
        inp_pos_x, inp_pos_y = block_left_coord + offset_x + scaling_x, block_top_coord + offset_y
        draw.rectangle((inp_pos_x - (port_box_width // 2), inp_pos_y - (port_box_height // 2),
                        inp_pos_x + (port_box_width // 2), inp_pos_y + (port_box_height // 2)), fill=color)

    if b.getBlockType() == "FunctionBlock":
        render_fbd_block(b, scaler, font, canvas)
    elif b.getBlockType() == "Port":
        render_port_block(b, scaler, font, canvas)
