#!/usr/bin/env python

import io
import os
import sys
import time
import traceback
from logging import Handler
from logging import Logger as PythonLogger
from logging import LogRecord
from typing import Optional

import pandas as pd
from commlib.msg import DataClass, DataField, PubSubMessage
from commlib.transports.mqtt import ConnectionParameters as MQTTConnectionParameters
from commlib.transports.mqtt import Publisher as MQTTPublisher

from .application_warning import ApplicationWarning

TESTING_TOOLS = ["nose", "unittest", "pytest"]

#  --- Copied from logging module ---
if hasattr(sys, '_getframe'):
    def currentframe():
        return sys._getframe(3)
else:   # pragma: no cover
    def currentframe():
        """Return the frame object for the caller's stack frame."""
        try:
            raise Exception
        except Exception:
            return sys.exc_info()[2].tb_frame.f_back
#  --- Copied from logging module ---


@DataClass
class LogMessage(PubSubMessage):
    timestamp: float = DataField(default=0.0)
    msg: str = DataField(default='')
    level_no: int = DataField(default=0)
    level_name: str = DataField(default='')
    logger_name: str = DataField(default='')


class MQTTHandler(Handler):
    MQTT_URI = 'hbot/$UID/log'

    def __init__(self,
                 mqtt_params: MQTTConnectionParameters = None,
                 mqtt_topic: str = ''):
        super().__init__()
        if mqtt_params is None:
            mqtt_params = MQTTConnectionParameters()
        if mqtt_topic in ('', None):
            mqtt_topic = self.MQTT_URI.replace('$UID', str(os.getenv('HBOT_UID')))
        self.mqtt_pub = MQTTPublisher(
            conn_params=mqtt_params,
            topic=mqtt_topic,
            msg_type=LogMessage,
            logger=PythonLogger('mqtt'),
            debug=True
        )

    def emit(self, record: LogRecord):
        msg_str = self.format(record)
        msg = LogMessage(
            timestamp=time.time(),
            msg=msg_str,
            level_no=record.levelno,
            level_name=record.levelname,
            logger_name=record.name

        )
        self.mqtt_pub.publish(msg)


class HummingbotLogger(PythonLogger):
    def __init__(self, name: str):
        super().__init__(name)
        if os.getenv('HBOT_MQTT_LOGGING') in ('1', 'True', 'true', 'Yes',
                                              'Nai', 'Si', 'Da', 'sudo'):
            self.addHandler(MQTTHandler())

    @staticmethod
    def logger_name_for_class(model_class: Type):
        return f"{model_class.__module__}.{model_class.__qualname__}"

    @staticmethod
    def is_testing_mode() -> bool:
        return any(tools in arg
                   for tools in TESTING_TOOLS
                   for arg in sys.argv)

    def notify(self, msg: str):
        from . import INFO
        self.log(INFO, msg)
        if not HummingbotLogger.is_testing_mode():
            from hummingbot.client.hummingbot_application import HummingbotApplication
            hummingbot_app: HummingbotApplication = HummingbotApplication.main_application()
            hummingbot_app.notify(f"({pd.Timestamp.fromtimestamp(int(time.time()))}) {msg}")

    def network(self, log_msg: str, app_warning_msg: Optional[str] = None, *args, **kwargs):
        from hummingbot.client.hummingbot_application import HummingbotApplication

        from . import NETWORK

        self.log(NETWORK, log_msg, *args, **kwargs)
        if app_warning_msg is not None and not HummingbotLogger.is_testing_mode():
            app_warning: ApplicationWarning = ApplicationWarning(
                time.time(),
                self.name,
                self.findCaller(),
                app_warning_msg
            )
            self.warning(app_warning.warning_msg)
            hummingbot_app: HummingbotApplication = HummingbotApplication.main_application()
            hummingbot_app.add_application_warning(app_warning)

    #  --- Copied from logging module ---
    def findCaller(self, stack_info=False, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        orig_f = f
        while f and stacklevel > 1:
            f = f.f_back
            stacklevel -= 1
        if not f:
            f = orig_f
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        return rv
    #  --- Copied from logging module ---


_srcfile = os.path.normcase(HummingbotLogger.network.__code__.co_filename)
