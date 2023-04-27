
import os
import json
import tempfile
import sys
sys.path.append('.')
from modules.data_handler.app import load_infos, save_infos, convert_to_yolo_format, find_file, get_credentials



def test_convert_to_yolo_format():
    label = {
        'class': 1,
        'xmin': 50,
        'xmax': 150,
        'ymin': 40,
        'ymax': 120,
    }
    img_width = 640
    img_height = 640

    result = convert_to_yolo_format(label, img_width, img_height)

    assert result == (1, 0.15625, 0.125, 0.15625, 0.125)

def test_find_file():
    test_filename = "test_file.txt"
    with open(test_filename, "w") as f:
        f.write("Test content")

    found_file = find_file(test_filename)

    os.remove(test_filename)

    assert found_file is not None

