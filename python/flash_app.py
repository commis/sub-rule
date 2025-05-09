from flasgger import Swagger
from flask import Flask, redirect

from api import api_bp
from m3u_checker import channel_bp
from m3u_converter import m3u_bp

app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(channel_bp, url_prefix='/channel')
app.register_blueprint(m3u_bp, url_prefix='/m3u')

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "模块化 Web 服务器 API",
        "description": "包含任务管理、M3U 转换和频道检查等功能的模块化 API",
        "version": "1.0.0",
        "termsOfService": None
    },
}
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",
}
swagger = Swagger(app, template=swagger_template, config=swagger_config)


# auto_register_blueprint_routes(app, swagger)


@app.route('/')
def index():
    return redirect('/swagger/')


if __name__ == '__main__':
    app.run(threaded=True, debug=True)
