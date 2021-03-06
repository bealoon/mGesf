import re

from PyQt5.QtWidgets import QWidget, QVBoxLayout

import config as config
from utils.GUI_main_window import init_container, init_combo_box, init_inputBox, init_checkBox, init_button
from utils.GUI_operation_tab import init_slider_bar_box


class XeThruX4ControlPane(QWidget):
    def __init__(self):
        super().__init__()

        # default range
        self.range_min = 0
        self.range_max = 0.4

        # for checking only one freq box
        self._toggle = None
        self.state = ['idle']  # see the docstring of self.update_state for details

        self.background = QVBoxLayout(self)
        self.setLayout(self.background)

        self.main_page = init_container(parent=self.background, vertical=True,
                                        style="background-color:" + config.container_color + ";")
        #       - device (combo box)
        self.device = init_combo_box(parent=self.main_page,
                                     label="Device",
                                     item_list=["X4M300", "X4M200", "X4M03"])
        self.device.activated[str].connect(self.device_onChanged)
        #       - port (input box)
        self.XeThruX4_port_block, self.XeThruX4_port_textbox = init_inputBox(parent=self.main_page,
                                                                               label="Port (device_name): ",
                                                                               label_bold=True,
                                                                               default_input="Default: COM8")

        self.freq_block = init_container(parent=self.main_page,
                                                  label="Frequency Band",
                                                  vertical=False)
        #       - frequency band (check box)
        self.low_freq_checkbox = init_checkBox(parent=self.freq_block,
                                               label="Low (7.290 GHz)",
                                               function=self.low_freq_action)
        self.high_freq_checkbox = init_checkBox(parent=self.freq_block,
                                                label="High (8.748 GHz)",
                                                function=self.high_freq_action)

        #       - range (input boxes)
        self.range_container = init_container(parent=self.main_page,
                                              label="Range (m) [0.5 ~ 3]",
                                              label_bold=True,
                                              vertical=False)

        self.min_range_block, self.min_range_textbox = init_inputBox(parent=self.range_container,
                                                                               label="Min:",
                                                                               label_bold=False,
                                                                               default_input="0")
        self.min_range_textbox.textChanged.connect(self.check_range)
        self.max_range_block, self.max_range_textbox = init_inputBox(parent=self.range_container,
                                                                               label="Max:",
                                                                               label_bold=False,
                                                                               default_input="0.4")
        self.max_range_textbox.textChanged.connect(self.check_range)

        #       - fps ( bar)
        self.fps_block, self.fps_slider_view = init_slider_bar_box(self.main_page,
                                                                   label="FPS",
                                                                   vertical=True,
                                                                   label_bold=True,
                                                                   min_value=10,
                                                                   max_value=25)
        self.fps_slider_view.setValue(23)

        #       - check box
        self.baseband_block = init_container(parent=self.main_page,
                                             label="Baseband",
                                             vertical=True)
        self.baseband_checkbox = init_checkBox(parent=self.baseband_block,
                                               function=self.baseband_checkbox_function)
        #       - two buttons

        self.buttons_block = init_container(self.main_page, vertical=False)
        self.start_stop__btn = init_button(parent=self.buttons_block,
                                           label="Start/stop sensor",
                                           function=self.start_stop_btn_action)
        self.reset_btn = init_button(parent=self.buttons_block,
                                     label="Reset to default",
                                     function=self.reset_btn_action)
        self.show()

    def check_range(self):

        self.range_min =  re.findall("\d+\.\d+", self.min_range_textbox.text())
        self.range_max = re.findall("\d+\.\d+", self.max_range_textbox.text())

        if self.range_min >= self.range_max:
            print("Range_min >= range_max.")


    def low_freq_action(self):
        if self.low_freq_checkbox.isChecked():
            self.update_state("freq_low")
            self._toggle = True
            self.high_freq_checkbox.setChecked(not self._toggle)
        else:
            self.update_state('not_freq_low')
            self._toggle = not self._toggle
        return

    def high_freq_action(self):
        if self.high_freq_checkbox.isChecked():
            self.update_state("freq_high")
            self._toggle = True
            self.low_freq_checkbox.setChecked(not self._toggle)
        else:
            self.update_state('not_freq_high')
            self._toggle = not self._toggle
        return

    def update_state(self, act):
        """
        update the current state based on action
        The working states, as oppose to 'idle' include that of 'pending', 'testing', 'countingDown', 'writing'
        @param act:
        """

        # check the checkbox logic
        if act in ['follow', 'not_follow', 'locate', 'not_locate']:
            self.check_locate_follow_logic(act)
        # test/record logic
        print("update function not implemented")

    def check_locate_follow_logic(self, act):
        """
        can only choose one
        :return:
        """
        if act == 'freq_low':
            # if locate is chosen, remove it
            if 'freq_high' in self.state:
                self.state.remove('freq_high')
            self.state.append(act)

        elif act == 'not_freq_low':
            if 'freq_low' in self.state:
                self.state.remove('freq_low')

        elif act == 'freq_high':
            if 'freq_low' in self.state:
                self.state.remove('freq_low')
            self.state.append(act)

        elif act == 'freq_high':
            if 'freq_high' in self.state:
                self.state.remove('freq_high')

    def baseband_checkbox_function(self):
        print('Baseband checked. Function not implemented...')

    def start_stop_btn_action(self):
        print('start/stop button clicked. Function not implemented...')
        # start testing
        self.low_freq_checkbox.setDisabled(True)
        self.high_freq_checkbox.setDisabled(True)

        # check range value
        if self.range_min >= self.range_max:
            print("Range_min >= range_max. Can't start.")
            return
        else:
           print('recording')

    def reset_btn_action(self):
        # start testing
        self.low_freq_checkbox.setChecked(False)
        self.high_freq_checkbox.setChecked(False)
        self.low_freq_checkbox.setDisabled(False)
        self.high_freq_checkbox.setDisabled(False)

        self.state.clear()
        print('reset button clicked. Function not implemented...')

    def device_onChanged(self):
        print("conbobox selection changed. Function not implemented..")