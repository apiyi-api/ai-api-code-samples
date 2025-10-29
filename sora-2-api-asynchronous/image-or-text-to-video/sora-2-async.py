import requests
import time
import os
from datetime import datetime

# API 配置
BASE_URL = "https://api.apiyi.com/v1/videos"
API_KEY = "sk-"

# ==================== 模式配置 ====================
# 设置 IMAGE_PATH 来切换生成模式：
# - IMAGE_PATH = None (或留空)    → 文字生成视频
# - IMAGE_PATH = '/path/to/image' → 图片生成视频
# =================================================

#IMAGE_PATH = None  # 取消注释，即文字生成视频模式，注释即图片生成视频模式；本文件默认是图片生成视频模式
IMAGE_PATH = r'./dog-and-cat.png'  # 取消注释并设置路径，切换为图片生成视频模式

# 请求参数配置
PROMPT = '参考配图，使得动物们活跃起来，在场地里绕场一周的追逐，画面要生动有趣，背景音乐类似：让我们欢快地跳起来'
MODEL = 'sora-2'
SIZE = '1280x720'  # 或 '720x1280'
SECONDS = '15'     # 支持 '10' 或 '15'

# 轮询配置
POLL_INTERVAL = 30  # 每 30 秒查询一次状态
MAX_WAIT_TIME = 600  # 最长等待 10 分钟


def get_mime_type(file_path):
    """根据文件扩展名推断 MIME 类型"""
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }
    return mime_types.get(ext, 'image/png')


def step1_submit_video_request():
    """第一步：提交视频生成请求（自动识别文字或图片模式）"""
    print("=" * 60)
    print("第一步：提交视频生成请求")
    print("=" * 60)

    # 检查是否为图片生成模式
    is_image_mode = IMAGE_PATH and os.path.exists(IMAGE_PATH)

    if IMAGE_PATH and not is_image_mode:
        print(f"⚠️  警告：图片路径已设置但文件不存在: {IMAGE_PATH}")
        print(f"    将使用文字生成视频模式")

    # 基础参数（使用 multipart/form-data 格式）
    files = {
        'prompt': (None, PROMPT),
        'model': (None, MODEL),
        'size': (None, SIZE),
        'seconds': (None, SECONDS)
    }

    headers = {
        'Accept': 'application/json',
        'Authorization': API_KEY,
        'Host': 'api.apiyi.com',
        'Connection': 'keep-alive'
    }

    try:
        if is_image_mode:
            # 图片生成视频模式
            print("📷 模式：图片生成视频")
            print(f"📤 发送请求...")
            print(f"   - 提示词: {PROMPT}")
            print(f"   - 图片: {IMAGE_PATH}")
            print(f"   - 模型: {MODEL}")
            print(f"   - 尺寸: {SIZE}")
            print(f"   - 时长: {SECONDS}秒")

            with open(IMAGE_PATH, 'rb') as f:
                files['input_reference'] = (
                    os.path.basename(IMAGE_PATH),
                    f,
                    get_mime_type(IMAGE_PATH)
                )
                response = requests.post(
                    BASE_URL,
                    headers=headers,
                    files=files
                )
        else:
            # 文字生成视频模式
            print("📝 模式：文字生成视频")
            print(f"📤 发送请求...")
            print(f"   - 提示词: {PROMPT}")
            print(f"   - 模型: {MODEL}")
            print(f"   - 尺寸: {SIZE}")
            print(f"   - 时长: {SECONDS}秒")

            response = requests.post(
                BASE_URL,
                headers=headers,
                files=files
            )

        if response.status_code == 200:
            result = response.json()
            video_id = result.get('id')
            print(f"✅ 请求提交成功!")
            print(f"   - 视频ID: {video_id}")
            print(f"   - 状态: {result.get('status')}")
            print(f"   - 创建时间: {datetime.fromtimestamp(result.get('created_at'))}")
            print(f"   ⏱️  预计生成时间: 3-5 分钟")
            return video_id, is_image_mode
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None, None

    except Exception as e:
        print(f"❌ 请求发生异常: {str(e)}")
        return None, None


def step2_poll_video_status(video_id):
    """第二步：轮询查询视频生成状态"""
    print("\n" + "=" * 60)
    print("第二步：查询视频生成状态")
    print("=" * 60)
    print(f"💡 提示：视频生成通常需要 3-5 分钟，每 {POLL_INTERVAL} 秒自动查询一次")

    headers = {
        'Authorization': API_KEY
    }

    status_url = f"{BASE_URL}/{video_id}"
    start_time = time.time()

    while True:
        elapsed_time = time.time() - start_time

        # 检查是否超时
        if elapsed_time > MAX_WAIT_TIME:
            print(f"⏱️ 超时：已等待 {MAX_WAIT_TIME} 秒，停止查询")
            return False

        try:
            print(f"\n🔍 查询状态... (已等待 {int(elapsed_time)} 秒)")
            response = requests.get(status_url, headers=headers)

            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                progress = result.get('progress', 0)

                print(f"   - 状态: {status}")
                print(f"   - 进度: {progress}%")

                if status == 'completed':
                    print(f"✅ 视频生成完成!")
                    print(f"   - 视频URL: {result.get('url')}")
                    print(f"   - 完成时间: {datetime.fromtimestamp(result.get('completed_at'))}")
                    return True
                elif status == 'failed':
                    print(f"❌ 视频生成失败")
                    return False
                elif status in ['submitted', 'in_progress']:
                    print(f"⏳ 视频生成中，等待 {POLL_INTERVAL} 秒后继续查询...")
                    time.sleep(POLL_INTERVAL)
                else:
                    print(f"⚠️ 未知状态: {status}")
                    time.sleep(POLL_INTERVAL)
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                print(f"   响应: {response.text}")
                time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"❌ 查询发生异常: {str(e)}")
            time.sleep(POLL_INTERVAL)


def step3_download_video(video_id, is_image_mode, output_path=None):
    """第三步：下载生成的视频"""
    print("\n" + "=" * 60)
    print("第三步：下载视频")
    print("=" * 60)

    # 根据模式生成默认文件名
    if output_path is None:
        mode_prefix = "image" if is_image_mode else "text"
        output_path = f"sora_{mode_prefix}_video_{video_id.split('_')[-1]}.mp4"

    headers = {
        'Authorization': API_KEY
    }

    content_url = f"{BASE_URL}/{video_id}/content"

    try:
        print(f"📥 开始下载视频...")
        response = requests.get(content_url, headers=headers, stream=True)

        if response.status_code == 200:
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))

            with open(output_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = (downloaded / total_size) * 100
                            print(f"\r   下载进度: {percent:.1f}% ({downloaded}/{total_size} 字节)", end='')

            print(f"\n✅ 视频下载成功!")
            print(f"   - 保存路径: {os.path.abspath(output_path)}")
            print(f"   - 文件大小: {os.path.getsize(output_path)} 字节")
            return True
        else:
            print(f"❌ 下载失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 下载发生异常: {str(e)}")
        return False


def main():
    """完整的异步流程"""
    print("\n🎬 开始 Sora-2 视频生成完整流程")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 第一步：提交请求
    video_id, is_image_mode = step1_submit_video_request()
    if not video_id:
        print("\n❌ 流程终止：视频请求提交失败")
        return

    # 第二步：轮询状态
    success = step2_poll_video_status(video_id)
    if not success:
        print("\n❌ 流程终止：视频生成未完成")
        return

    # 第三步：下载视频
    success = step3_download_video(video_id, is_image_mode)

    if success:
        print("\n" + "=" * 60)
        print("🎉 完整流程执行成功!")
        print("=" * 60)
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n❌ 流程终止：视频下载失败")


if __name__ == "__main__":
    main()
