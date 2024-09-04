import re

import requests
from dateutil import parser
from flask import Flask, request, abort, jsonify
from flask_cors import cross_origin

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/content_info', methods=['POST'])
@cross_origin()  # 只对这个路由启用 CORS
def job_content_info():
    if request.method != 'POST':
        abort(405)

    url = request.form.get('url')
    lang = request.form.get('lang')

    if not url:
        return jsonify({'status': 'error', 'message': '差事链接不能为空'})

    # 根据 URL 获取 Content ID
    content_id = get_content_id_from_url(url)
    if not content_id:
        return jsonify({'status': 'error', 'message': '差事链接格式不正确'})

    result = get_content_info(content_id, lang)
    if result['status']:
        json_url = get_content_json_url(content_id, lang)
        return jsonify({'status': 'success', 'img': result['img'], 'data': result['info'], 'json_url': json_url})

    return jsonify({'status': 'error', 'message': '获取信息失败，请检查链接是否正确'})


def get_content_id_from_url(url):
    # 首先尝试匹配整个URL
    pattern_full_url = r'https?://socialclub\.rockstargames\.com/job/gtav/([a-zA-Z0-9_-]+)'
    match = re.fullmatch(pattern_full_url, url)

    if match:
        # 如果是完整的URL，则返回匹配的字符串
        return match.group(1)

    # 如果不是完整的URL，尝试直接匹配字符串
    pattern_code_only = r'^[a-zA-Z0-9_-]+$'
    match_code = re.fullmatch(pattern_code_only, url)

    if match_code:
        # 如果是单独的字符串，则返回该字符串
        return url

    # 如果都不匹配，返回错误信息
    return None


def get_content_info_lang(lang):
    if lang == 'en':
        return 'en-US'

    if lang == 'zh-cn':
        return 'zh-CN'

    return 'en-US'


def format_iso_time(time_str):
    try:
        # 解析时间字符串
        dt = parser.isoparse(time_str)
        # 格式化为所需的格式
        formatted_time = dt.strftime("%Y年%m月%d日 %H时%M分%S秒")
        return formatted_time
    except ValueError as e:
        print(f"时间格式错误: {e}")
        return time_str


def get_content_info(content_id, lang='en'):
    result = {'status': False}

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
        return result

    try:
        res = response.json()
    except Exception as e:
        return result

    if not res['status']:
        return result

    content = res['content']

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
    return {
        'status': True,
        'img': content['imgSrc'],
        'info': data
    }


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

    return ''


if __name__ == '__main__':
    app.run()
