from monitorcontrol import get_monitors

for monitor in get_monitors():
    with monitor:
        try:
            print(monitor.get_vcp_capabilities())
        except:
            pass