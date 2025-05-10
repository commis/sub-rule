import importlib
import os
import traceback

from flasgger import Swagger
from flask import Blueprint, redirect
from flask_cors import CORS


class RouteScanner:
    def __init__(self, app, app_package):
        self.app = app
        self.app_package = app_package
        self.blueprints = []
        self.tags = {}
        self.definitions = {}

        CORS(app, resources={r"/*": {"origins": "*"}})

        @app.route('/')
        def index():
            return redirect('/swagger/')

    def scan_directory(self, base_dir):
        """递归扫描目录，查找所有routes.py文件并注册路由"""
        for root, dirs, files in os.walk(base_dir):
            if 'routes.py' in files:
                relative_path = os.path.relpath(root, base_dir)
                if relative_path == '.':
                    module_path = 'routes'
                else:
                    module_path = relative_path.replace(os.sep, '.') + '.routes'

                full_module_path = f"{self.app_package}.{module_path}"

                # 导入模块并查找蓝图
                try:
                    module = importlib.import_module(full_module_path)

                    # 查找蓝图
                    blueprint = None
                    if hasattr(module, 'bp') and isinstance(module.bp, Blueprint):
                        blueprint = module.bp
                    elif hasattr(module, 'create_blueprint'):
                        blueprint = module.create_blueprint()

                    if blueprint:
                        self.blueprints.append(blueprint)
                        self.__collect_swagger_tags(module, blueprint.name)

                except Exception as e:
                    print(f"导入模块 {full_module_path} 时出错: {e}")
                    print(traceback.format_exc())

    def __collect_swagger_tags(self, module, blueprint_name):
        """收集模块中的Swagger标签信息"""
        # 假设模块中有一个swagger_tags属性
        if hasattr(module, 'swagger_tags'):
            for tag in module.swagger_tags:
                if not tag.get("description"):
                    tag["description"] = "No description provided"
                self.tags[tag['name']] = tag
        else:
            print(f"模块 {blueprint_name} 没有定义swagger_tags")

        # 收集模型定义
        if hasattr(module, 'swagger_definitions'):
            self.definitions.update(module.swagger_definitions)

    def register_blueprints(self):
        """注册所有找到的蓝图到应用"""
        for blueprint in self.blueprints:
            self.app.register_blueprint(blueprint)

    def configure_swagger(self):
        swagger_template = {
            "swagger": "2.0",
            "info": {
                "title": "模块化 Web 服务器 API",
                "description": "自动生成的API文档",
                "version": "1.0.0"
            },
            "basePath": "/",  # 重要：设置API的基础路径
            "schemes": ["http"],
            "tags": list(self.tags.values()),
            "definitions": self.definitions
        }
        swagger_config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": 'apispec_1',
                    "route": '/apispec_1.json',
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/swagger/"
        }
        return Swagger(self.app, template=swagger_template, config=swagger_config)
