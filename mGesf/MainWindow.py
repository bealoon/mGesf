import sys

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QTabWidget, \
    QHBoxLayout, QFormLayout, QScrollArea
import pyqtgraph as pg
import time

from mGesf.main_page_tabs.ControlTab import ControlTab
from mGesf.main_page_tabs.RadarTab import RadarTab
from mGesf.main_page_tabs.LeapTab import LeapTab
from mGesf.main_page_tabs.XeThruX4Tab import XeThruX4Tab
from mGesf.main_page_tabs.UWBTab import UWBTab
from mGesf.main_page_tabs.gesture_tab.GestureTab import GestureTab

from utils.InformationPane import InformationPane
from utils.iwr6843_utils.mmWave_interface import MmWaveSensorInterface

import mGesf.workers as workers

# tabs ======================================
import config as config

# class WorkerSignals(QObject):
#     finished = pyqtSignal()
#     error = pyqtSignal(tuple)
#     result = pyqtSignal(object)
#     progress = pyqtSignal(int)

# TODO add resume function to the stop button
from utils.std_utils import Stream


class MainWindow(QMainWindow):
    def __init__(self, mmw_interface: MmWaveSensorInterface, leap_interface,
                 uwb_interface_anchor, uwb_interface_tag,
                 refresh_interval, data_path, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi('mGesf/resource/ui/MainWindow.ui', self)
        pg.setConfigOption('background', 'w')
        self.title = 'Micro-gesture Sensor-fusion'

        main_layout = self.findChild(QHBoxLayout, 'mainLayout')

        # create the tabs: Control, Radar, Leap, UWB, and Gesture
        self.main_widget = self.findChild(QWidget, 'mainWidget')
        self.table_widget = Tabs(self.main_widget, mmw_interface, leap_interface,
                                 uwb_interface_anchor, uwb_interface_tag,
                                 refresh_interval, data_path)
        self.setCentralWidget(self.table_widget)
        # create the information black
        # self.info_scroll = self.findChild(QScrollArea, 'infoScroll')
        self.show()


class Tabs(QWidget):
    """A frame contains 4 tabs and their contents"""

    def __init__(self, parent, mmw_interface: MmWaveSensorInterface, leap_interface,
                 uwb_interface_anchor, uwb_interface_tag,
                 refresh_interval, data_path, *args, **kwargs):
        super(QWidget, self).__init__(parent)

        self.layout = QHBoxLayout(self)

        # create threading; create a QThread and start the thread that handles; worker for sensors
        self.mmw_worker_thread = pg.QtCore.QThread(self)
        self.mmw_worker_thread.start()
        self.uwb_worker_thread = pg.QtCore.QThread(self)
        self.uwb_worker_thread.start()
        self.leap_worker_thread = pg.QtCore.QThread(self)
        self.leap_worker_thread.start()

        # worker
        # mmwave worker
        self.mmw_worker = workers.MmwWorker(mmw_interface)
        self.mmw_worker.moveToThread(self.mmw_worker_thread)
        # uwb worker
        self.uwb_worker = workers.UWBWorker(uwb_interface_anchor, uwb_interface_tag)
        self.uwb_worker.moveToThread(self.uwb_worker_thread)
        # leap worker
        self.leap_worker = workers.LeapWorker(leap_interface=leap_interface)
        self.leap_worker.moveToThread(self.leap_worker_thread)

        # timer
        self.timer = QTimer()
        self.timer.setInterval(refresh_interval)
        self.timer.timeout.connect(self.ticks)
        self.timer.start()

        # Initialize tab screen

        self.tabs = QTabWidget()
        self.tab1 = ControlTab(self.mmw_worker, self.uwb_worker, self.leap_worker, refresh_interval, data_path)
        self.tab2 = RadarTab(self.mmw_worker, refresh_interval, data_path)
        self.tab3 = LeapTab(self.leap_worker, refresh_interval, data_path)
        self.tab4 = UWBTab(self.uwb_worker, refresh_interval, data_path)
        self.tab5 = XeThruX4Tab()
        self.tab6 = GestureTab(self.mmw_worker)

        self.tabs.addTab(self.tab1, config.main_window_control_tab_label)
        self.tabs.addTab(self.tab2, config.main_window_radar_tab_label)
        self.tabs.addTab(self.tab3, config.main_window_leap_tab_label)
        self.tabs.addTab(self.tab4, config.main_window_uwb_tab_label)
        self.tabs.addTab(self.tab5, "XeThruX4")
        self.tabs.addTab(self.tab6, config.main_window_gesture_tab_label)

        # Add tabs to main_widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        self.info_pane = InformationPane(parent=self.layout)
        sys.stdout = Stream(newText=self.on_print)

    def on_print(self, msg):
        self.info_pane.push(msg)

    def __del__(self):
        sys.stdout = sys.__stdout__  # return control to regular stdout

    @pg.QtCore.pyqtSlot()
    def ticks(self):
        """
        ticks every 'refresh' milliseconds
        """
        self.mmw_worker.tick_signal.emit()  # signals the worker to run process_on_tick
        self.uwb_worker.tick_signal.emit()  # signals the worker to run process_on_tick for the UWB sensor
        self.leap_worker.tick_signal.emit()
