import re
from datetime import datetime

import requests
from flask import Flask, request, abort, jsonify
from flask_cors import cross_origin

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/content_info', methods=['POST'])
@cross_origin()  # 只对这个路由启用CORS
def job_content_info():
    if request.method != 'POST':
        abort(405)

    url = request.form.get('url')
    lang = request.form.get('lang')

    if not url:
        return jsonify({'status': 'error', 'message': '差事链接不能为空'})

    # 验证URL格式
    pattern = r'https://socialclub\.rockstargames\.com/job/gtav/([a-zA-Z0-9_]+)'
    match = re.match(pattern, url)
    if not match:
        return jsonify({'status': 'error', 'message': '差事链接格式不正确'})

    # 截取最后一段字符
    content_id = match.group(1)

    success, img, info = get_content_info(content_id, lang)
    if success:
        json_url = get_content_json_url(content_id, lang)
        if not json_url:
            json_url = ''

        return jsonify({'status': 'success', 'img': img, 'data': info, 'json_url': json_url})

    return jsonify({'status': 'error', 'message': '获取信息失败'})


def get_content_info_lang(lang):
    if lang == 'en':
        return 'en-US'

    if lang == 'zh-cn':
        return 'zh-CN'

    return 'en-US'


def format_iso_time(time_str):
    try:
        # 解析时间字符串
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        # 格式化为所需的格式
        formatted_time = dt.strftime("%Y年%m月%d日 %H时%M分%S秒")
        return formatted_time
    except ValueError as e:
        print(f"时间格式错误: {e}")
        return time_str


def get_content_info(content_id, lang='en'):
    response = requests.get(
        f'https://scapi.rockstargames.com/ugc/mission/details?title=gtav&contentId={content_id}',
        headers={
            'x-requested-with': 'XMLHttpRequest',
            'x-lang': get_content_info_lang(lang),
            'x-cache-ver': '0',
            'x-amc': 'true',
        },
        verify=False
    )

    if response.status_code != 200:
        return False

    content = response.json()['content']

    data = {
        "contentName": content['name'],
        "contentDesc": content['desc'],
        "contentType": content['type'],
        "userTags": content['userTags'],
        "createdDate": format_iso_time(content['createdDate']),
        "likeCount": content['likeCount'],
        "dislikeCount": content['dislikeCount'],
        "playedCount": content['playedCount']
    }
    return True, content['imgSrc'], data


def get_content_json_url(content_id, lang='en'):
    prefixes = []

    for i in range(3):
        for j in range(3):
            prefixes.append(f'{i}_{j}')

    for prefix in prefixes:
        url = f'https://prod.cloud.rockstargames.com/ugc/gta5mission/{content_id}/{prefix}_{lang}.json'
        response = requests.get(url, verify=False)

        if response.status_code == 200:
            return url


if __name__ == '__main__':
    app.run()
