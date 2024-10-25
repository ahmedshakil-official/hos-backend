def get_user_device_info_from_request(request):
    device_type = ""
    browser_type = ""
    browser_version = ""
    os_type = ""
    os_version = ""
    if request.user_agent.is_mobile:
        device_type = "Mobile"
    elif request.user_agent.is_tablet:
        device_type = "Tablet"
    elif request.user_agent.is_pc:
        device_type = "PC"
    elif request.user_agent.is_bot:
        device_type = "BOT"
    else:
        device_type = "Unknown"

    browser_type = request.user_agent.browser.family
    browser_version = request.user_agent.browser.version_string
    os_type = request.user_agent.os.family
    os_version = request.user_agent.os.version_string
    context = {
        "ip": request.user_ip,
        "device_type": device_type,
        "browser_type": browser_type,
        "browser_version": browser_version,
        "os_type": os_type,
        "os_version": os_version
    }
    return context
