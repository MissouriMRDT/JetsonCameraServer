import threading
import jetson_utils
from jetson_utils import gstCamera
import time

from typing import List, Dict, Tuple

class VideoDevice:
    device: int
    video_source: jetson_utils.videoSource
    output_by_endpoint: Dict[str, jetson_utils.videoOutput]

    def __init__(self, device: int):
        self.device = device
        self.output_by_endpoint = {}
        self.video_source = None
    
    def create_stream(self, endpoint: str):
        # Make sure we're not already streaming this device to this endpoint
        assert not (endpoint in self.output_by_endpoint.keys())

        if self.is_streaming():
            # try:
            #     self.video_source.Close()
            #     self.video_source = jetson.utils.videoSource(f"/dev/video{self.device}", ['-input-width=480', '-input-height=360'])
            #     self.video_source.Open()
            #     for other_endpoint in self.output_by_endpoint.keys():
            #         self.output_by_endpoint[other_endpoint] = jetson_utils.videoOutput(f"rtp://{other_ndpoint}")
            #     self.output_by_endpoint[endpoint] = jetson_utils.videoOutput(f"rtp://{endpoint}")
            # except Exception:
            #     self.video_source = None
            #     print(f"Error creating stream for device {self.device}")
            self.output_by_endpoint[endpoint] = jetson_utils.video_source(f"rtp://{endpoint}", argv=['--width=640', '--height=480', '--headless', '--bitrate=1200000'])
        else:
            try:
                self.video_source = jetson_utils.videoSource(f"/dev/video{self.device}", argv=['--width=640', '--height=480', '--headless', '--bitrate=1200000'])
                self.video_source.Open()
                self.output_by_endpoint[endpoint] = jetson_utils.videoOutput(f"rtp://{endpoint}", argv=['--width=640', '--height=480', '--headless', '--bitrate=1200000'])
            except Exception as e:
                self.video_source = None
                print(f"Error creating stream for device {self.device}")
                print(e)
                self.output_by_endpoint = {}

    def is_streaming(self) -> bool:
        is_streaming = len(self.output_by_endpoint) != 0
        if is_streaming and self.video_source is not None:
            return True
        elif not is_streaming and self.video_source is None:
            return False
        else:
            assert False, "Invalid state in is_streaming"
        

class StreamManager:
    _lock = threading.Lock

    _endpoints: List[str]
    _video_devices: List[VideoDevice]
    _device_endpoints: List[Tuple[int, int]]

    def __init__(self):
        self._video_devices = []
        for i in range(2):
            self._video_devices.append(VideoDevice(i * 4))
        self._endpoints = [
            "rtp://192.168.1.69:5000",
            "rtp://192.168.1.69:5001",
            "rtp://192.168.1.69:5002",
            "rtp://192.168.1.69:5003",
        ]
        self._lock = threading.Lock()

    def updateStreams(self):
        with self._lock:
            for index, video_dev in enumerate(self._video_devices):
                try:
                    #print(video_dev.device)
                    image = video_dev.video_source.Capture(timeout=5000)
                    for output in video_dev.output_by_endpoint.values():
                        output.Render(image)
                    # image.__delitem__()
                except Exception as e: 
                    # print("Error updating streams")
                    # TODO: Stop streaming this device
                    print(e)
                    pass


def main():
    streaming_manager = StreamManager()
    streaming_manager._video_devices[0].create_stream("192.168.1.69:5000")
    streaming_manager._video_devices[1].create_stream("192.168.1.69:5001")

    fps = 30
    loop_delta = 1./fps

    current_time = target_time = time.time()
    
    while True:
        previous_time, current_time = current_time, time.time()
        time_delta = current_time - previous_time
        streaming_manager.updateStreams()

        target_time += loop_delta
        sleep_time = target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else: 
            # print("took too long")
            pass

if __name__ == "__main__":
    main()
