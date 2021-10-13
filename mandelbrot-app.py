#!/usr/bin/env python3
#%%
import os
import struct
import usb

from kivy.app           import App
from kivy.uix.button    import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget    import Widget
from kivy.graphics      import Canvas, Point, Color
from functools          import partial

dev=usb.core.find(idVendor=0x1209, idProduct=0xDECA)

debug=False
if debug: print(dev)

import struct
import time

scale = 8*8

def send_command(bytewidth, no_pixels_x, no_pixels_y, max_iterations, bottom_left_corner_x, bottom_left_corner_y, step, debug=False):
    command_bytes = struct.pack("HHI", no_pixels_x, no_pixels_y, max_iterations)

    command_bytes += bottom_left_corner_x.to_bytes(bytewidth, byteorder='little', signed=True)
    command_bytes += bottom_left_corner_y.to_bytes(bytewidth, byteorder='little', signed=True)
    command_bytes += step.to_bytes(bytewidth, byteorder='little', signed=True)
    command_bytes += bytes([0xa5])
    if debug: print(f"command: {str(bytes(command_bytes))}")

    dev.write(0x01, command_bytes)

    time.sleep(0.05)

    result = []
    try:
        while True:
            if debug: print("read")
            r = dev.read(0x81, 256, timeout=10)
            if debug: print("Got: "+ str(len(r)))
            if debug: print(str(r))
            result += r
    except usb.USBError:
        print(f"Got Total: {len(result)}")

    if len(result) > 0:
        first_separator_index = result.index(0xa5)
        if first_separator_index != 9:
            print(f"Warning: Chop until index {first_separator_index}")
            result = result[first_separator_index+1:]
        pixels = [struct.unpack("HHIBx", bytes(p)) for p in [result[i:i+10] for i in range(0, len(result), 10)] if len(p) == 10]
        for pixel in pixels:
            if debug: print(f"x: {pixel[0]} y: {pixel[1]} iterations: {pixel[2]}\t escape: {pixel[3] >> 4} maxed: {pixel[3] & 0xf}")

        print(f"Total number of pixels: {len(pixels)}")

        return pixels

colortable = [
    [ 66,  30,  15],
    [ 25,   7,  26],
    [  9,   1,  47],
    [  4,   4,  73],
    [  0,   7, 100],
    [ 12,  44, 138],
    [ 24,  82, 177],
    [ 57, 125, 209],
    [134, 181, 229],
    [211, 236, 248],
    [241, 233, 191],
    [248, 201,  95],
    [255, 170,   0],
    [204, 128,   0],
    [153,  87,   0],
    [106,  52,   3],
]

class MandelWidget(Widget):
    def draw(self, pixels, max_iterations):
        with self.canvas:
            histogram = [0] * 16

            for pixel in pixels:
                escape = (pixel[3] >> 4) == 1
                maxed  = pixel[3] & 0x1  == 1
                if (maxed):
                    Color(0, 0, 0)
                if (escape):
                    i = pixel[2] % len(colortable)
                    histogram[i] += 1
                    if debug: print(f"iter: {pixel[2]} max: {max_iterations} i: {i}")
                    Color(*[c/255.0 for c in colortable[i]])

                Point(points=(pixel[0], pixel[1]), pointsize=1)
                if escape == maxed:
                    print(f"ESCAPED && MAXXED: {pixel}")

            print(str(histogram))

class MandelGUI(App):
    def __init__(self, *, max_iterations=255, **kwargs):
        self.max_iterations = max_iterations
        super().__init__(**kwargs)

    def render(self, instance, *args):
        pixels = send_command(9, image_width, image_height, self.max_iterations, corner_x, corner_y, step)
        self.image.draw(pixels, self.max_iterations)
        pass

    def build(self):
        self.mainBox = BoxLayout(orientation='vertical', spacing=10)
        self.buttonBox = BoxLayout(orientation='horizontal', spacing=10)
        self.buttonBox.size_hint_max_y = 50

        self.renderButton = Button(text='Render', height=48)
        self.renderButton.bind(on_press=partial(self.render, self.renderButton))

        self.image = MandelWidget()
        self.buttonBox.add_widget(self.renderButton)
        self.mainBox.add_widget(self.buttonBox)
        self.mainBox.add_widget(self.image)
        return self.mainBox

corner_x = -2 << scale
corner_y = -5 << (scale - 2)
step = 1 << (scale - 9)

image_width  = 1920 # 256+128
image_height = 1300 # 256+64

def fix2float(fix):
    return fix/2**scale

print(f"left_corner_x: {corner_x/2**scale} corner_y: {corner_y/2**scale}, step: {step/2**scale}")
print(f"right_corner_x: {(corner_x + image_width*step)/2**scale} upper_corner_y: {(corner_y + image_height*step)/2**scale}")

from sys import argv
if __name__ == "__main__":
    if len(argv) > 1:
        if argv[1] == "gui":
            app = MandelGUI(max_iterations=256)
            app.run()

        if argv[1] == "plot":
            p = send_command(9, image_width, image_height, 2048, corner_x, corner_y, step, debug=False)
            r = [e for e in p if e[3] & 0x1 > 0]
            x = [fix2float(corner_x) + fix2float(step) * e[0] for e in r]
            y = [fix2float(corner_y) + fix2float(step) * e[1] for e in r]

            coords = list(zip(x, y))
            print(coords)

            import matplotlib.pyplot as plt
            plt.scatter(x, y, c ="black")

            # To show the plot
            plt.show()

            import code
            code.interact(local=locals())

    else:
        send_command(9, image_width, image_height, 255, corner_x, corner_y, step, debug=True)