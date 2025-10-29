/**
 * Sora-2 文字生成视频完整异步流程 - JavaScript/Node.js 版本
 *
 * 依赖安装: npm install axios form-data
 * 运行: node sora-2-text-async.js
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
    prompt: '一只橘色的小猫在阳光明媚的花园里追逐蝴蝶',
    model: 'sora-2',
    size: '1280x720',
    seconds: '15',
    pollInterval: 30000,  // 30 秒
    maxWaitTime: 600000,  // 10 分钟
};

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
 * 第一步：提交文字生成视频请求
 */
async function step1SubmitRequest() {
    console.log('============================================================');
    console.log('第一步：提交文字生成视频请求');
    console.log('============================================================');

    console.log('📤 发送请求...');
    console.log(`   - 提示词: ${CONFIG.prompt}`);
    console.log(`   - 模型: ${CONFIG.model}`);
    console.log(`   - 尺寸: ${CONFIG.size}`);
    console.log(`   - 时长: ${CONFIG.seconds}秒`);

    // 构建 FormData（使用 multipart/form-data 格式）
    const formData = new FormData();
    formData.append('prompt', CONFIG.prompt);
    formData.append('model', CONFIG.model);
    formData.append('size', CONFIG.size);
    formData.append('seconds', CONFIG.seconds);

    try {
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

        return result.id;
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
async function step3DownloadVideo(videoId) {
    console.log('\n============================================================');
    console.log('第三步：下载视频');
    console.log('============================================================');

    const outputFile = `sora_text_video_${videoId.slice(-8)}.mp4`;

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

    console.log('\n🎬 开始 Sora-2 文字生成视频完整流程');
    console.log(`⏰ 开始时间: ${startTime.toLocaleString('zh-CN')}\n`);

    try {
        // 第一步：提交请求
        const videoId = await step1SubmitRequest();

        // 第二步：轮询状态
        await step2PollStatus(videoId);

        // 第三步：下载视频
        await step3DownloadVideo(videoId);

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
