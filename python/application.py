import os

import uvicorn
from fastapi import FastAPI

from core.core_scanner import RouteScanner


class CreateApplication:
    def __init__(self):
        self.__app = FastAPI(
            title="模块化 Web 服务器 API",
            description="自动生成的API文档",
            version="1.0.0",
            debug=True)

        # 初始化路由扫描器
        app_package = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
        scanner = RouteScanner(self.__app, app_package)

        # 扫描当前目录下的所有routes.py文件
        base_dir = os.path.dirname(os.path.abspath(__file__))
        scanner.scan_directory(base_dir)
        scanner.register_routers()

    def get_app(self):
        return self.__app

    def start_server(self):
        import __main__ as main
        module_name = os.path.basename(main.__file__).replace('.py', '')
        uvicorn.run(
            f"{module_name}:app",
            port=8001
        )


print(f"working directory: {os.getcwd()}")
application_creator = CreateApplication()
app = application_creator.get_app()

if __name__ == '__main__':
    application_creator.start_server()
