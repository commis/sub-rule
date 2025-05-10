from flask import request, jsonify, send_file, Blueprint

from . import converter

bp = Blueprint('m3u', __name__, url_prefix='/m3u')
swagger_tags = [
    {
        "name": "M3U转换器",
        "description": "M3U 和 TXT 相互转换的相关接口"
    }
]


@bp.route('/convert', methods=['POST'])
def convert_m3u():
    """
    转换 M3U 文件
    ---
    tags:
      - M3U转换器
    parameters:
      - in: formData
        name: m3u_file
        type: file
        required: true
        description: M3U 文件
      - in: query
        name: format
        type: string
        enum: ['json', 'csv', 'plain']
        default: 'json'
        description: 输出格式
    responses:
      200:
        description: 转换结果
    """
    file = request.files['m3u_file']
    output_format = request.args.get('format', 'json')

    result = converter.convert(file, output_format)

    if output_format == 'json':
        return jsonify(result)
    elif output_format == 'csv':
        # 示例：返回 CSV 文件
        return send_file(
            result,
            mimetype='text/csv',
            as_attachment=True,
            download_name='converted.csv'
        )
    else:
        return result, 200, {'Content-Type': 'text/plain'}
