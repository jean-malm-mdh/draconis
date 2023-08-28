import dataclasses
import sys
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from Web_GUI.parser.AST.program import Program
from Web_GUI.parser.AST.connections import ConnectionDirection
from Web_GUI import Point


@dataclasses.dataclass
class DrawContext:
    canvas: ImageDraw
    fonts: dict[str, ImageFont]

    def __init__(self, img_width, img_height, scaler=None, bg_col="white"):
        self.image = Image.new("RGB", (img_width, img_height), color=bg_col)
        self.canvas = ImageDraw.Draw(self.image)
        self.fonts = {
            "__DEFAULT__": ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 10),
            "__HEADER__": ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 20),
        }
        self.scaler = scaler or (lambda e: e)

    @property
    def Width(self):
        return self.image.width

    @property
    def Height(self):
        return self.image.height

    def save_image_to_file(self, path):
        self.image.save(path)

    def draw_text_centered(
        self, msg, position: Tuple[int, int], font_name, col="black"
    ):
        font = self.fonts.get(font_name, None) or self.fonts["__DEFAULT__"]
        text_width, text_height = self.canvas.textsize(msg, font)
        p_x, p_y = position
        p_x -= text_width // 2
        p_y -= text_height // 2
        self.canvas.text((p_x, p_y), msg, fill=col, font=font)

    def draw_rect_filled(self, l_t, r_b, col):
        l, t = l_t
        r, b = r_b
        self.canvas.rectangle((l, t, r, b), fill=col)

    def draw_rect_outline(self, l_t, r_b, col, width):
        l, t = l_t
        r, b = r_b
        self.canvas.rectangle((l, t, r, b), outline=col, width=width)

    def render_message_box(
        self, pos_left_up: Tuple[int, int], header_msg, message, color, maxWidth
    ):
        def isWS_Or_Punct(c):
            return not c.isalnum()

        def trimMessageToWidth(_message, _font, _maxWidth):
            _msg_width, _msg_height = draw.textsize(_message, _font)
            while _msg_width > _maxWidth:
                message_len = len(_message)
                msg_split_point = message_len // 2
                while msg_split_point < message_len and not isWS_Or_Punct(
                    _message[msg_split_point]
                ):
                    msg_split_point += 1
                if msg_split_point == message_len:
                    msg_split_point = message_len // 2
                    while msg_split_point >= 0 and not isWS_Or_Punct(
                        _message[msg_split_point]
                    ):
                        msg_split_point -= 1
                _message = (
                    _message[:msg_split_point] + "\n" + _message[msg_split_point:]
                )
                _msg_width, _msg_height = draw.textsize(_message, header_font)
            return _message, _msg_width, _msg_height

        def position_message(font, header_font, header_msg, maxWidth, message):
            message, message_width, message_height = trimMessageToWidth(
                message, font, maxWidth
            )
            header_msg, header_width, header_height = trimMessageToWidth(
                header_msg, header_font, maxWidth
            )
            l, t = pos_left_up
            header_message_offset_height = 10
            message_max_width = max(header_width, message_width)
            r, b = (
                l + message_max_width,
                t + header_height + message_height + header_message_offset_height,
            )
            return (
                b,
                header_height,
                header_message_offset_height,
                header_msg,
                l,
                message,
                r,
                t,
            )

        draw = self.canvas
        header_font = self.fonts["__HEADER__"]
        font = self.fonts["__DEFAULT__"]
        (
            b,
            header_height,
            header_message_offset_height,
            header_msg,
            l,
            message,
            r,
            t,
        ) = position_message(font, header_font, header_msg, maxWidth, message)
        self.draw_rect_filled(pos_left_up, (r, b), col=color)
        draw.text((l, t), header_msg, fill="black", font=header_font)
        draw.text(
            (l, t + header_height + header_message_offset_height),
            message,
            fill="black",
            font=font,
        )
        return l, t, r, b

    def render_block(self, b):
        render_block(b, self.scaler, self.fonts["__DEFAULT__"], self.canvas)

    def render_line(self, line: Tuple[Point, Point], col="black", width=1):
        s_p, e_p = line
        s_s_x, s_s_y, e_s_x, e_s_y = map(self.scaler, (s_p.x, s_p.y, e_p.x, e_p.y))
        self.canvas.line((s_s_x, s_s_y, e_s_x, e_s_y), fill=col, width=width)

    def render_checker_grid_background(self, _grid_box_size):
        info_font = self.fonts["__DEFAULT__"]
        w, h, grid_box_size = map(
            self.scaler, (self.image.size[0], self.image.size[1], _grid_box_size)
        )
        self.canvas.rectangle((0, 0, w, h), outline="black", width=1)
        for i in range(1, h // grid_box_size):
            self.canvas.line(
                (i * grid_box_size, 0, i * grid_box_size, h), fill="black", width=1
            )
            if i % 5 == 0:
                self.canvas.text(
                    (i * grid_box_size, 0),
                    text=str(i * _grid_box_size),
                    font=info_font,
                    fill="black",
                )
        for i in range(1, w // grid_box_size):
            self.canvas.line(
                (0, i * grid_box_size, w, i * grid_box_size), fill="black", width=1
            )
            if i % 5 == 0:
                self.canvas.text(
                    (0, i * grid_box_size),
                    text=str(i * _grid_box_size),
                    font=info_font,
                    fill="black",
                )


def render_lines(lines, draw_context):
    for line in lines:
        # Not sure why scaling of 2.0 is required to get lines to proper places ...
        _line = (
            Point(line[0].x * 2, line[0].y * 2),
            (Point(line[1].x * 2, line[1].y * 2)),
        )
        draw_context.render_line(_line, width=2)


def render_blocks(blocks, draw_context):
    for b in blocks:
        draw_context.render_block(b)


def generate_image_of_program(
    program: Program, img_result_path: str, scale=1.0, generate_report_in_image=False
):
    """
    Generate an image of the program
    Args:
        generate_report_in_image: If image shall contain report information
        program: The program to render into an image
        img_result_path: The path to the result image
        scale: The scaling factor for the rendering

    Returns:
        if OK, returns path to created image file
    """

    def scaler(int_val):
        return int(int_val * scale)

    boundary = 25
    margin_size = 300 if generate_report_in_image else 0
    _height, _width = get_program_width_height(program, min_size=100)
    width = scaler(_width)
    height = scaler(_height)
    # Add some space for margins and annotations
    width += margin_size
    height += margin_size
    width += boundary
    height += boundary
    draw_context = DrawContext(width, height, scaler, bg_col="white")
    text = program.progName
    text_x = (width - margin_size) // 2
    draw_context.draw_text_centered(
        text, (text_x, 15), font_name="__HEADER__", col="black"
    )

    # render the FBD blocks
    render_blocks(program.behaviourElements, draw_context)

    render_lines(program.lines, draw_context)

    # Render comment boxes
    for comment in program.comments:
        draw_context.render_message_box(
            (comment.bounding_box.top_left.x, comment.bounding_box.top_left.y),
            message=comment.content,
            color="lightblue",
            header_msg="",
            maxWidth=scaler(comment.bounding_box.getSize().x),
        )

    if sys.gettrace() is not None:
        draw_context.render_checker_grid_background(_grid_box_size=10)
    if generate_report_in_image:
        render_reports(program, margin_size, draw_context)

    draw_context.save_image_to_file(img_result_path)


def render_reports(program: Program, margin_offset_size, draw_context: DrawContext):
    rule_checks = program.check_rules()
    margin_start_x = draw_context.Width - margin_offset_size
    b = 0
    for r in rule_checks:
        name, verdict, justification = r
        col = "yellow" if verdict == "Fail" else "lightgreen"
        _, _, _, b = draw_context.render_message_box(
            (margin_start_x, b),
            header_msg=name,
            message=f"{verdict}\n{justification}",
            color=col,
            maxWidth=margin_offset_size,
        )


def get_program_width_height(program, min_size=100):
    _width, _height = min_size, min_size
    # Find actual width and height, based on elements present
    for b in program.behaviourElements:
        _x, _y = b.data.boundary_box.bot_right.getAsTuple()
        _width = max(_width, _x)
        _height = max(_height, _y)
    for l in program.lines:
        s_p, e_p = l
        _width = max(_width, s_p.x, e_p.x)
        _height = max(_height, s_p.y, e_p.y)
    return _height, _width


def render_block(aBlock, scalerFunc, font: ImageFont, canvas: ImageDraw):
    def render_fbd_block(block):
        def draw_port_box(port_coord, block_left_coord, block_top_coord, color):
            port_box_width, port_box_height = map(scalerFunc, (4, 2))
            offset_x, offset_y = map(
                scalerFunc, (port_coord.data.position.x, port_coord.data.position.y)
            )
            # shift position of port depending on direction
            scaling_x = (
                scalerFunc(2)
                if port_coord.connectionDir == ConnectionDirection.Output
                else scalerFunc(-2)
            )
            inp_pos_x, inp_pos_y = (
                block_left_coord + offset_x + scaling_x,
                block_top_coord + offset_y,
            )
            canvas.rectangle(
                (
                    inp_pos_x - (port_box_width // 2),
                    inp_pos_y - (port_box_height // 2),
                    inp_pos_x + (port_box_width // 2),
                    inp_pos_y + (port_box_height // 2),
                ),
                fill=color,
            )

        inputs = block.getInputVars()
        input_connections = [i.connectionPoint for i in inputs]
        outputs = block.getOutputVars()
        output_connections = [i.connectionPoint for i in outputs]
        l, t, r, b = map(scalerFunc, block.data.boundary_box.getAsTuple())
        canvas.rectangle((l, t, r, b), outline="black", width=2)

        # Draw ports
        for in_port in input_connections:
            draw_port_box(in_port, l, t, color="red")
        for out_port in output_connections:
            draw_port_box(out_port, l, t, color="green")
        name = block.data.type
        text_width, text_height = canvas.textsize(name, font)
        block_width_scaled = r - l
        text_offset_x = (block_width_scaled - text_width) // 2
        text_offset_y = text_height // 2
        # Draw block name
        canvas.text(
            (l + text_offset_x, t + text_offset_y), name, font=font, fill="black"
        )

    def render_port_block(block):
        l, t, r, b = map(scalerFunc, block.data.boundary_box.getAsTuple())
        canvas.rectangle((l, t, r, b), outline="purple", width=2)
        expr_text = block.getVarExpr()
        text_width, text_height = canvas.textsize(expr_text, font=font)
        block_width_scaled = r - l
        text_offset_x = (block_width_scaled - text_width) // 2
        text_offset_y = 0
        canvas.text(
            (l + text_offset_x, t + text_offset_y), expr_text, font=font, fill="black"
        )

    if aBlock.getBlockType() == "FunctionBlock":
        render_fbd_block(aBlock)
    elif aBlock.getBlockType() == "Port":
        render_port_block(aBlock)
