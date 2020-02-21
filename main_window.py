from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QRunnable, QThreadPool, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget, \
    QGridLayout, QMainWindow, QLabel
import pyqtgraph as pg

from utils.iwr6843_utils.mmWave_interface import MmWaveSensorInterface
from utils.simulation import sim_heatmap, sim_detected_points
from utils.img_utils import array_to_colormap_qim

import numpy as np
# class WorkerSignals(QObject):
#     finished = pyqtSignal()
#     error = pyqtSignal(tuple)
#     result = pyqtSignal(object)
#     progress = pyqtSignal(int)


class Worker(QObject):
    result_signal = pyqtSignal(dict)
    tick_signal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        self.tick_signal.connect(self.process_on_tick)
        self._mmw_interface = None

    @pg.QtCore.pyqtSlot()
    def process_on_tick(self):
        if self._mmw_interface:
            pts_array = self._mmw_interface.process_frame()
            # TODO, we are not simulating this
            spec_array = sim_heatmap((100, 100))
            spec_qim = array_to_colormap_qim(spec_array)
            if pts_array is not None:
                self.result_signal.emit({'spec': spec_qim,
                                         'pts': pts_array})
        else:
            pts_array = sim_detected_points()
            spec_array = sim_heatmap((100, 100))
            spec_qim = array_to_colormap_qim(spec_array)

            self.result_signal.emit({'spec': spec_qim,
                                     'pts': pts_array})

    def enable_mmw(self, mmw_interface):
        self._mmw_interface = mmw_interface
        self._mmw_interface.start_sensor()


class MainWindow(QMainWindow):
    def __init__(self, mmw_interface: MmWaveSensorInterface, refresh_interval, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.resize(1920, 1080)
        pg.setConfigOption('background', 'w')

        w = QWidget()
        # create main layout
        self.lay = QGridLayout(self)
        # add spectrogram graphic view
        self.spec_pixmap_item = QGraphicsPixmapItem()
        self.init_spec_view()
        # add detected points plots
        self.scatterXY = self.init_pts_view(pos=(0, 3))
        self.scatterZD = self.init_pts_view(pos=(0, 4))

        # add the interrupt button
        self.interruptBtn = QtWidgets.QPushButton(text='Interrupt')
        self.interruptBtn.clicked.connect(self.interruptBtnAction)
        self.lay.addWidget(self.interruptBtn, *(0, 1))

        # add dialogue label
        self.dialogueLabel = QLabel()
        self.dialogueLabel.setText("Running")
        self.lay.addWidget(self.dialogueLabel, *(0, 0))

        # set the main layout
        w.setLayout(self.lay)
        self.setCentralWidget(w)
        self.show()

        # create threading
        # create a QThread and start the thread that handles
        worker_thread = pg.QtCore.QThread(self)
        worker_thread.start()

        self.timer = QTimer()
        self.timer.setInterval(refresh_interval)
        self.timer.timeout.connect(self.ticks)

        self.worker = Worker()
        self.worker.moveToThread(worker_thread)
        self.worker.result_signal.connect(self.update_image)

        # prepare the sensor interface
        if mmw_interface:
            print('App: using IWR6843AoP; starting sensor')
            self.worker.enable_mmw(mmw_interface)
            print('App: done!')
        else:
            print('App: not using IWR6843AoP')

        self.timer.start()

    def init_spec_view(self):
        spc_gv = QGraphicsView()
        self.lay.addWidget(spc_gv, *(0, 2))
        scene = QGraphicsScene(self)
        spc_gv.setScene(scene)
        scene.addItem(self.spec_pixmap_item)

    def init_pts_view(self, pos):
        pts_plt = pg.PlotWidget()
        pts_plt.setXRange(0., 1.)
        pts_plt.setYRange(0., 1.)
        self.lay.addWidget(pts_plt, *pos)
        scatter = pg.ScatterPlotItem(pen=None, symbol='o')
        pts_plt.addItem(scatter)
        return scatter
        # pts_gv = QGraphicsView()
        # self.lay.addWidget(pts_gv, *(0, 3))
        # scene = QGraphicsScene(self)
        # pts_gv.setScene(scene)
        # scene.addItem(self.pts_pixmap_item)

    def interruptBtnAction(self):
        self.timer.stop()
        self.dialogueLabel.setText('Stopped. Close the application to return to the console.')

    def update_image(self, data_dict):
        # update spectrogram
        # spec_qpixmap = QPixmap(data_dict['spec'])
        # self.spec_pixmap_item.setPixmap(spec_qpixmap)
        # update the scatter
        self.scatterXY.setData(data_dict['pts'][:, 0], data_dict['pts'][:, 1])
        self.scatterZD.setData(data_dict['pts'][:, 2], data_dict['pts'][:, 3])

    @pg.QtCore.pyqtSlot()
    def ticks(self):
        """
        ticks every 'refresh' milliseconds
        """
        self.worker.tick_signal.emit()  # signals the worker to run process_on_tick
        # worker = Worker()
        # worker.signals.result.connect(self.update_image)
        # self.threadpool.start(worker)
