import importlib
import os
from typing import List

from fastapi import FastAPI, APIRouter
from starlette.responses import RedirectResponse

from core.logger_factory import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RouteScanner:
    def __init__(self, app: FastAPI, app_package):
        self.app = app
        self.app_package = app_package
        self.routers: List[APIRouter] = []

        @app.get("/", include_in_schema=False)
        def docs_redirect():
            return RedirectResponse(url="/docs")

    def scan_directory(self, base_dir: str):
        """递归扫描目录，查找所有routes.py文件并注册路由"""
        for root, dirs, files in os.walk(base_dir):
            if "routes.py" in files:
                rel_path = os.path.relpath(root, base_dir)
                if rel_path == ".":
                    module_name = "routes"
                else:
                    module_name = rel_path.replace(os.path.sep, ".") + ".routes"

                full_module_name = f"{self.app_package}.{module_name}"
                try:
                    module = importlib.import_module(full_module_name)
                    # 查找模块中的所有APIRouter实例
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, APIRouter):
                            self.routers.append(attr)
                    logger.info(f"successfully import routes module: {full_module_name}")
                except Exception as e:
                    logger.error(f"failed to import routes module: {full_module_name}, error: {e}")

    def register_routers(self):
        """将收集到的APIRouter注册到FastAPI应用"""
        for router in self.routers:
            self.app.include_router(router)
