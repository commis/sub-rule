from flask import jsonify


class ApiUtils:

    @staticmethod
    def invalid_request_400():
        return jsonify({
            'error': '无效输入',
            "code": 400,
            'message': '请求体不能为空'
        }), 400

    @staticmethod
    def invalid_parameter_400(message):
        return jsonify({
            'error': '无效输入',
            "code": 400,
            'message': message
        }), 400

    @staticmethod
    def invalid_response_500(e):
        return jsonify({
            'error': '处理请求时出错',
            "code": 500,
            'message': str(e)
        }), 500

    @staticmethod
    def sync_request_accepted_202(task_id):
        return jsonify({
            "task_id": task_id,
            "status": "accepted",
            "message": "检测任务已启动"
        }), 202

    @staticmethod
    def not_found_404(message):
        return jsonify({
            "status": "error",
            "code": 404,
            "message": message
        }), 404
