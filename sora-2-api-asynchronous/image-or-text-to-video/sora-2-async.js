/**
 * Sora-2 视频生成完整异步流程 - JavaScript/Node.js 版本
 * 智能双模式：自动识别文字生成视频 / 图片生成视频
 *
 * 依赖安装: npm install axios form-data
 * 运行: node sora-2-async.js
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

// ============================================
// 配置参数
// ============================================
const CONFIG = {
    baseURL: 'https://api.apiyi.com/v1/videos',
    apiKey: 'sk-',

    // ==================== 模式配置 ====================
    // 设置 imagePath 来切换生成模式：
    // - imagePath: null (或留空)    → 文字生成视频
    // - imagePath: '/path/to/image' → 图片生成视频
    // =================================================

    imagePath: null,  // 文字生成视频模式
    // imagePath: '/path/to/your/image.png',  // 取消注释并设置路径，切换为图片生成视频模式

    prompt: '一只橘色的小猫在阳光明媚的花园里追逐蝴蝶',
    model: 'sora-2',
    size: '1280x720',
    seconds: '15',
    pollInterval: 30000,  // 30 秒
    maxWaitTime: 600000,  // 10 分钟
};

/**
 * 根据文件扩展名推断 MIME 类型
 */
function getMimeType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    };
    return mimeTypes[ext] || 'image/png';
}

/**
 * 格式化时间戳
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/**
 * 第一步：提交视频生成请求（自动识别文字或图片模式）
 */
async function step1SubmitRequest() {
    console.log('============================================================');
    console.log('第一步：提交视频生成请求');
    console.log('============================================================');

    // 检查是否为图片生成模式
    const isImageMode = CONFIG.imagePath && fs.existsSync(CONFIG.imagePath);

    if (CONFIG.imagePath && !isImageMode) {
        console.log(`⚠️  警告：图片路径已设置但文件不存在: ${CONFIG.imagePath}`);
        console.log(`    将使用文字生成视频模式`);
    }

    // 构建 FormData
    const formData = new FormData();
    formData.append('prompt', CONFIG.prompt);
    formData.append('model', CONFIG.model);
    formData.append('size', CONFIG.size);
    formData.append('seconds', CONFIG.seconds);

    try {
        if (isImageMode) {
            // 图片生成视频模式
            console.log('📷 模式：图片生成视频');
            console.log('📤 发送请求...');
            console.log(`   - 提示词: ${CONFIG.prompt}`);
            console.log(`   - 图片: ${CONFIG.imagePath}`);
            console.log(`   - 模型: ${CONFIG.model}`);
            console.log(`   - 尺寸: ${CONFIG.size}`);
            console.log(`   - 时长: ${CONFIG.seconds}秒`);

            formData.append('input_reference', fs.createReadStream(CONFIG.imagePath), {
                filename: path.basename(CONFIG.imagePath),
                contentType: getMimeType(CONFIG.imagePath),
            });
        } else {
            // 文字生成视频模式
            console.log('📝 模式：文字生成视频');
            console.log('📤 发送请求...');
            console.log(`   - 提示词: ${CONFIG.prompt}`);
            console.log(`   - 模型: ${CONFIG.model}`);
            console.log(`   - 尺寸: ${CONFIG.size}`);
            console.log(`   - 时长: ${CONFIG.seconds}秒`);
        }

        const response = await axios.post(CONFIG.baseURL, formData, {
            headers: {
                ...formData.getHeaders(),
                'Authorization': CONFIG.apiKey,
            },
        });

        const result = response.data;
        console.log('✅ 请求提交成功!');
        console.log(`   - 视频ID: ${result.id}`);
        console.log(`   - 状态: ${result.status}`);
        console.log(`   - 创建时间: ${formatTimestamp(result.created_at)}`);
        console.log(`   ⏱️  预计生成时间: 3-5 分钟`);

        return { videoId: result.id, isImageMode };
    } catch (error) {
        if (error.response) {
            throw new Error(`❌ 请求失败: ${error.response.status}\n响应: ${JSON.stringify(error.response.data)}`);
        }
        throw new Error(`❌ 请求失败: ${error.message}`);
    }
}

/**
 * 第二步：轮询查询视频状态
 */
async function step2PollStatus(videoId) {
    console.log('\n============================================================');
    console.log('第二步：查询视频生成状态');
    console.log('============================================================');
    console.log(`💡 提示：视频生成通常需要 3-5 分钟，每 ${CONFIG.pollInterval / 1000} 秒自动查询一次`);

    const startTime = Date.now();

    while (true) {
        const elapsed = Date.now() - startTime;

        // 检查超时
        if (elapsed > CONFIG.maxWaitTime) {
            throw new Error(`⏱️ 超时：已等待 ${CONFIG.maxWaitTime / 1000} 秒，停止查询`);
        }

        console.log(`\n🔍 查询状态... (已等待 ${Math.floor(elapsed / 1000)} 秒)`);

        try {
            const response = await axios.get(`${CONFIG.baseURL}/${videoId}`, {
                headers: {
                    'Authorization': CONFIG.apiKey,
                },
            });

            const result = response.data;
            console.log(`   - 状态: ${result.status}`);
            console.log(`   - 进度: ${result.progress || 0}%`);

            switch (result.status) {
                case 'completed':
                    console.log('✅ 视频生成完成!');
                    console.log(`   - 视频URL: ${result.url}`);
                    console.log(`   - 完成时间: ${formatTimestamp(result.completed_at)}`);
                    return;
                case 'failed':
                    throw new Error('❌ 视频生成失败');
                case 'submitted':
                case 'in_progress':
                    console.log(`⏳ 视频生成中，等待 ${CONFIG.pollInterval / 1000} 秒后继续查询...`);
                    await sleep(CONFIG.pollInterval);
                    break;
                default:
                    console.log(`⚠️ 未知状态: ${result.status}`);
                    await sleep(CONFIG.pollInterval);
            }
        } catch (error) {
            if (error.response) {
                console.log(`❌ 状态查询失败: ${error.response.status}`);
            } else if (error.message.includes('视频生成失败')) {
                throw error;
            } else {
                console.log(`❌ 查询发生异常: ${error.message}`);
            }
            await sleep(CONFIG.pollInterval);
        }
    }
}

/**
 * 第三步：下载视频
 */
async function step3DownloadVideo(videoId, isImageMode) {
    console.log('\n============================================================');
    console.log('第三步：下载视频');
    console.log('============================================================');

    // 根据模式生成文件名
    const modePrefix = isImageMode ? 'image' : 'text';
    const outputFile = `sora_${modePrefix}_video_${videoId.slice(-8)}.mp4`;

    console.log('📥 开始下载视频...');

    try {
        const response = await axios.get(`${CONFIG.baseURL}/${videoId}/content`, {
            headers: {
                'Authorization': CONFIG.apiKey,
            },
            responseType: 'stream',
        });

        const writer = fs.createWriteStream(outputFile);
        let downloadedBytes = 0;
        const totalBytes = parseInt(response.headers['content-length'] || '0');

        response.data.on('data', (chunk) => {
            downloadedBytes += chunk.length;
            if (totalBytes > 0) {
                const percent = ((downloadedBytes / totalBytes) * 100).toFixed(1);
                process.stdout.write(`\r   下载进度: ${percent}% (${downloadedBytes}/${totalBytes} 字节)`);
            }
        });

        response.data.pipe(writer);

        return new Promise((resolve, reject) => {
            writer.on('finish', () => {
                const stats = fs.statSync(outputFile);
                console.log('\n✅ 视频下载成功!');
                console.log(`   - 保存路径: ${path.resolve(outputFile)}`);
                console.log(`   - 文件大小: ${formatFileSize(stats.size)}`);
                resolve();
            });
            writer.on('error', reject);
        });
    } catch (error) {
        if (error.response) {
            throw new Error(`❌ 下载失败: ${error.response.status}`);
        }
        throw new Error(`❌ 下载失败: ${error.message}`);
    }
}

/**
 * 辅助函数：延迟
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 主流程
 */
async function main() {
    const startTime = new Date();

    console.log('\n🎬 开始 Sora-2 视频生成完整流程');
    console.log(`⏰ 开始时间: ${startTime.toLocaleString('zh-CN')}\n`);

    try {
        // 第一步：提交请求
        const { videoId, isImageMode } = await step1SubmitRequest();

        // 第二步：轮询状态
        await step2PollStatus(videoId);

        // 第三步：下载视频
        await step3DownloadVideo(videoId, isImageMode);

        console.log('\n============================================================');
        console.log('🎉 完整流程执行成功!');
        console.log('============================================================');
        console.log(`⏰ 结束时间: ${new Date().toLocaleString('zh-CN')}`);
    } catch (error) {
        console.error(`\n❌ 流程终止：${error.message}`);
        process.exit(1);
    }
}

// 运行主流程
if (require.main === module) {
    main();
}

module.exports = { main };
