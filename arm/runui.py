# pylint: disable=wrong-import-position
"""Main run page for armui"""
import os
import sys
import signal

# set the PATH to /arm/arm, so we can handle imports properly
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import arm.config.config as cfg  # noqa E402
import arm.ui.routes  # noqa E402
import arm.ui.settings.DriveUtils  # noqa E402
import arm.ui.utils  # noqa E402

from arm.ui import app  # noqa E402

shutdown_requested = False


def startup():
    """ARM UI Startup check on database config"""
    db_update = arm.ui.utils.arm_db_check()
    if db_update["db_current"]:
        app.logger.info("Updating Optical Drives")
        arm.ui.settings.DriveUtils.drives_update(startup=True)


def handle_shutdown(signum, frame):
    """ARM handle SIGTERM/SIGINT for graceful shutdown"""
    global shutdown_requested
    shutdown_requested = True
    app.logger.info("Received shutdown signal (%s). Shutting down ARM-UI.", signum)
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)      # systemd shutdown command
signal.signal(signal.SIGINT, handle_shutdown)       # keyboard interrupt


def get_host():
    """
    Return the address the web server should bind to.

    WEBSERVER_IP is the address advertised in notifications/display. Binding to a
    single autodetected address only exposes the UI on whichever interface happens
    to be listed first (e.g. tailscale0), hiding it from the LAN or vice versa.
    Bind to all interfaces so the UI is reachable from every network the host is on
    (LAN, Tailscale, docker port mapping). Set ARM_WEBSERVER_BIND to restrict it.
    """
    return os.environ.get('ARM_WEBSERVER_BIND', '0.0.0.0')


# Start ARM using waitress, default number of threads is "4", set ARM count to "40"
# Higher thread count to accommodate slow blocking processes when the UI is polling the ripper during ripping
if __name__ == '__main__':
    host = get_host()
    port = cfg.arm_config['WEBSERVER_PORT']
    app.logger.info("Starting ARM-UI on interface address - %s:%s", host, port)

    # Run ARM Startup
    startup()

    from waitress import serve

    try:
        serve(app, host=host, port=port, threads=40)
    except KeyboardInterrupt:
        app.logger.info("Keyboard interrupt received, shutting down ARM-UI.")
    finally:
        app.logger.info("ARM-UI shutdown complete.")
