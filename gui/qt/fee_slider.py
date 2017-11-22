
from electrum.i18n import _
from electrum.simple_config import STATIC, ETA, MEMPOOL

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QSlider, QToolTip

import threading


class FeeSlider(QSlider):

    def __init__(self, window, config, callback):
        QSlider.__init__(self, Qt.Horizontal)
        self.config = config
        self.window = window
        self.callback = callback
        self.fee_type = STATIC
        self.lock = threading.RLock()
        self.update()
        self.valueChanged.connect(self.moved)
        self._active = True

    def moved(self, pos):
        with self.lock:
            if self.fee_type == STATIC:
                fee_rate = self.config.static_fee(pos)
            elif self.fee_type == ETA:
                fee_rate = self.config.eta_to_fee(pos)
            elif self.fee_type == MEMPOOL:
                fee_rate = self.config.depth_to_fee(pos)
            tooltip = self.get_tooltip(pos, fee_rate)
            QToolTip.showText(QCursor.pos(), tooltip, self)
            self.setToolTip(tooltip)
            self.callback(self.fee_type, pos, fee_rate)

    def get_tooltip(self, pos, fee_rate):
        rate_str = self.window.format_fee_rate(fee_rate) if fee_rate else _('unknown')
        if self.fee_type == MEMPOOL:
            tooltip = 'Mempool based\n' + self.config.depth_tooltip(pos)
        elif self.fee_type == ETA:
            tooltip = 'Time based\n'+ self.config.eta_tooltip(pos)
        elif self.fee_type == STATIC:
            tooltip = 'Fixed rate:\n' + rate_str
            #if self.config.has_fee_estimates():
            #    eta = self.config.fee_to_eta(fee_rate)
            #    depth = self.config.fee_to_depth(fee_rate)
            #    tooltip += '\n' + self.config.fee_tooltip(eta)
        return tooltip

    def update(self):
        from electrum.simple_config import FEE_ETA_TARGETS, FEE_DEPTH_TARGETS
        with self.lock:
            self.fee_type = self.config.fee_type()
            if self.fee_type == STATIC:
                fee_rate = self.config.fee_per_kb()
                pos = self.config.static_fee_index(fee_rate)
                self.setRange(0, 9)
                self.setValue(pos)
            elif self.fee_type == ETA:
                pos = self.config.get('fee_level', 2)
                fee_rate = self.config.eta_to_fee(pos)
                self.setRange(0, len(FEE_ETA_TARGETS)-1)
                self.setValue(pos)
            else:
                pos = self.config.get('fee_level', 2)
                fee_rate = self.config.depth_to_fee(pos)
                self.setRange(0, len(FEE_DEPTH_TARGETS)-1)
                self.setValue(pos)

            tooltip = self.get_tooltip(pos, fee_rate)
            self.setToolTip(tooltip)

    def activate(self):
        self._active = True
        self.setStyleSheet('')

    def deactivate(self):
        self._active = False
        # TODO it would be nice to find a platform-independent solution
        # that makes the slider look as if it was disabled
        self.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #B1B1B1);
                margin: 2px 0;
            }

            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 12px;
                margin: -2px 0;
                border-radius: 3px;
            }
            """
        )

    def is_active(self):
        return self._active
