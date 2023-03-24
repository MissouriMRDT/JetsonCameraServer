import jetson_utils

#Get video device
video_device = jetson_utils.videoSource(f"/dev/video0", ['-input-width=480', '-input-height=360'])
video_device.Open()

#Set output IP/Port
output_dev = jetson_utils.videoOutput(f"rtp://192.168.1.69:5000")

#Function to send new frames to client
def updateStream():
    image = video_device.Capture(timeout=1000)
    output_dev.Render(image)

while True:
    updateStream()
