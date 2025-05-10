import os

from flask import Flask

from core.core_scanner import RouteScanner


class CreateApplication:
    def __init__(self):
        app = Flask(__name__)
        app_package = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

        # 初始化路由扫描器
        scanner = RouteScanner(app, app_package)

        # 扫描当前目录下的所有routes.py文件
        base_dir = os.path.dirname(os.path.abspath(__file__))
        scanner.scan_directory(base_dir)
        scanner.register_blueprints()

        self.__swagger = scanner.configure_swagger()
        self.__app = app

    def get_app(self):
        return self.__app

    def start_server(self):
        self.__app.run(port=8001, threaded=True, debug=True)


application_creator = CreateApplication()
app = application_creator.get_app()

if __name__ == '__main__':
    application_creator.start_server()
