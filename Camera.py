import threading
import jetson_utils
from jetson_utils import gstCamera
import time
from rovecomm.rovecomm import RoveComm, RoveCommPacket, get_manifest

from typing import List, Dict, Tuple

rovecomm_node: RoveComm
manifest = get_manifest()

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
            print("It is streaming")
            self.output_by_endpoint[endpoint] = jetson_utils.videoOutput(f"{endpoint}", argv=['--width=640', '--height=480', '--headless', '--bitrate=1200000'])
        else:
            try:
                self.video_source = jetson_utils.videoSource(f"/dev/video{self.device}", argv=['--width=640', '--height=480', '--headless', '--bitrate=1200000'])
                self.video_source.Open()
                self.output_by_endpoint[endpoint] = jetson_utils.videoOutput(f"{endpoint}", argv=['--width=640', '--height=480', '--headless', '--bitrate=1200000'])
            except Exception as e:
                self.video_source = None
                print(f"Error creating stream for device {self.device}")
                print(e)
                self.output_by_endpoint = {}
                return False
        return True

    def is_streaming(self) -> bool:
        is_streaming = len(self.output_by_endpoint) != 0
        if is_streaming and self.video_source is not None:
            return True
        elif not is_streaming and self.video_source is None:
            return False
        else:
            assert False, "Invalid state in is_streaming"
    
    def remove_endpoint(self, endpoint: str):
        #assert endpoint in self.output_by_endpoint.keys()
        del self.output_by_endpoint[endpoint]
        if len(self.output_by_endpoint) == 0:
            self.video_source = None

class StreamManager:
    _lock = threading.Lock

    _streams: List[int]
    _endpoints: List[str]
    _video_devices: List[VideoDevice]
    _device_endpoints: List[Tuple[int, int]]

    def __init__(self):
        self._video_devices = []
        self._streams = [-1, -1, -1, -1]
        for i in range(8):
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
                if(video_dev.is_streaming()):
                    try:
                        image = video_dev.video_source.Capture(timeout=5000)
                        for output in video_dev.output_by_endpoint.values():
                            output.Render(image)
                    except Exception as e: 
                        print("Error updating streams")
                        # TODO: Stop streaming this device
                        copy_endpoints = [elem for elem in video_dev.output_by_endpoint.keys()]
                        for endpoint in copy_endpoints:
                            video_dev.remove_endpoint(endpoint)
                        print(e)
                        pass

    def change_feeds(self, packet):
        with self._lock:
            print("hello")
            port, new_dev = packet.data
            endpoint = self._endpoints[port]
            prev_dev = self._streams[port]
            print(f"prev_dev: {prev_dev}")
            print(f"{port}:{new_dev}")

            if prev_dev == new_dev:
                print("prev_dev == new_dev")
                #Do nothing, request is already being served
                return
            elif new_dev == -1:
                print("none")
                self._video_devices[prev_dev].remove_endpoint(endpoint)
                self._streams[port] = -1
            else:
                if prev_dev == -1:
                    print("new")
                    if  (self._video_devices[new_dev].create_stream(endpoint)):
                        self._streams[port] = new_dev
                else:
                    print("change")
                    self._streams[port] = new_dev
                    print("new_dev")
                    self._video_devices[prev_dev].remove_endpoint(endpoint)
                    print("remove endpoint")
                    if (self._video_devices[new_dev].create_stream(endpoint)) == 0:
                        self._streams[port] = prev_dev
                        self._video_devices[prev_dev].create_stream(endpoint)



def main():
    streaming_manager = StreamManager()

    rovecomm_node = RoveComm()
    rovecomm_node.set_callback(manifest["Camera1"]["Commands"]["ChangeCameras"]["dataId"], streaming_manager.change_feeds)
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
