import sys
sys.path.append('.')
import pytest
from detection_module import DetectionModule

def test_detection_module():
    # Instantiate the DetectionModule class with test=True
    detection_module = DetectionModule(model_path='best.pt', camera=False, cameraid=1, test=True)
    print('***')
    # Test if the detection_module object is created successfully
    assert detection_module is not None

    # Test if the model object is loaded correctly
    assert detection_module.model is not None


    # Test if the prepare_parkings_data method returns the correct data format
    data_to_prepare = {0: {"id": 0, "source": "test", "detections": {}, "image": None, "freespace": 0, "sourceInfos": None}}
    prepared_data = detection_module.prepare_parkings_data(data_to_prepare)
    assert isinstance(prepared_data, dict)
    assert len(prepared_data) == 1
    detection_module.runRemoteSource()
test_detection_module()