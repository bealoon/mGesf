import serial
import time
import numpy as np
import pymoduleconnector
import matplotlib.pyplot as plt
try:
    from pymoduleconnector.moduleconnectorwrapper import *
except ImportError:
    print('...')


class xeThruX4SensorInterface:

    def __init__(self):

        # sys_info
        self.device_name = None
        self.min_range = None
        self.max_range = None
        self.center_frequency = None
        self.FPS = None
        self.baseband = False
        self.xep = None
        # sampling rate
        self.fs = 23.328e9
        # data buffer
        self.frame_history = []
        self.clutter_removal_frame_history = []
        self.clutter = None

    def reset(self, device_name):
        try:
            mc = pymoduleconnector.ModuleConnector(device_name)
            xep = mc.get_xep()
            xep.module_reset()
            print("device find")
            mc.close()
            time.sleep(3)

            self.frame_history.clear()
            self.clutter = None

        except:
            print("Cannot find x4 device, please check connection or reconnect your device")
            raise

    def config_x4_sensor(self, device_name, min_range=-0.1, max_range=0.4, center_frequency=3, FPS=10, baseband=False):
        try:
            self.reset(device_name)
        except:
            return

        self.mc = pymoduleconnector.ModuleConnector(device_name)

        app = self.mc.get_x4m300()
        # Stop running application and set module in manual mode.
        try:
            app.set_sensor_mode(XTID_SM_STOP, 0)  # Make sure no profile is running.
        except RuntimeError:
            # Profile not running, OK
            pass

        try:
            app.set_sensor_mode(XTID_SM_MANUAL, 0)  # Manual mode.
        except RuntimeError:
            # Maybe running XEP firmware only?
            pass

        try:
            self.xep = self.mc.get_xep()
            # set center frequency
            self.xep.x4driver_set_tx_center_frequency(center_frequency)

            # print(xep.x4driver_get_tx_center_frequency())

            self.xep.x4driver_set_dac_min(850)
            self.xep.x4driver_set_dac_max(1200)
            # Set integration
            self.xep.x4driver_set_iterations(64)
            self.xep.x4driver_set_pulses_per_step(20)
            # baseband?
            self.xep.x4driver_set_downconversion(int(baseband))
            # Start streaming of data
            self.xep.x4driver_set_frame_area(min_range, max_range)
            self.xep.x4driver_set_fps(FPS)
        except:
            print("error while config")
            return

        self.device_name = device_name
        self.FPS = FPS
        self.center_frequency = center_frequency
        self.min_range = min_range
        self.max_range = max_range
        # boolean
        self.baseband = baseband




    def stop_sensor(self):
        if self.xep is not None:
            try:
                self.reset(self.device_name)
            except:
                print("please check the connection")
        else:
            print("no connection history, please check usb")




    def display_xep_sys_info(self):
        if self.xep is not None:
            print("FirmWareID =", self.xep.get_system_info(2))
            print("Version =", self.xep.get_system_info(3))
            print("Build =", self.xep.get_system_info(4))
            print("SerialNumber =", self.xep.get_system_info(6))
            print("VersionList =", self.xep.get_system_info(7))
            frame_area = self.xep.x4driver_get_frame_area()
            print('x4driver_get_frame_area returned: [', frame_area.start, ', ', frame_area.end, ']')

    def clear_xep_buffer(self):
        if self.xep is not None:
            while self.xep.peek_message_data_float():
                self.xep.read_message_data_float()

        else:
            print("device not found")

    def read_frame(self):
        if self.xep.peek_message_data_float():
            d = self.xep.read_message_data_float()
            frame = np.array(d.data)
            if self.baseband:
                n = len(frame)
                frame = frame[:n // 2] + 1j * frame[n // 2:]

            self.frame_history.append(frame)

            return frame

        else:
            return None

    def read_clutter_removal_frame(self, rf_frame, signal_clutter_ratio):
        if self.clutter is None:
            self.clutter = rf_frame
            return rf_frame-self.clutter
        else:
            self.clutter = signal_clutter_ratio * self.clutter + (1-signal_clutter_ratio)*rf_frame
            clutter_removal_rf_frame = rf_frame - self.clutter
            self.clutter_removal_frame_history.append(clutter_removal_rf_frame)
            return clutter_removal_rf_frame
