#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Capsule地图工具的本地开发启动脚本。生产环境请使用 Gunicorn。"""

import os
import threading
import time
import webbrowser


def open_browser(url):
    """在本地开发启动后打开浏览器。"""
    time.sleep(1)
    webbrowser.open(url)


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    open_browser_enabled = os.environ.get('OPEN_BROWSER', 'true').lower() == 'true'
    url = f'http://{host}:{port}'

    if open_browser_enabled and not debug:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    from backend.app import app
    app.run(debug=debug, host=host, port=port)
