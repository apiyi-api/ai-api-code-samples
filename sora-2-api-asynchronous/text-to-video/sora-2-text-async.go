package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

// 配置参数
const (
	BaseURL      = "https://api.apiyi.com/v1/videos"
	APIKey       = "sk-"
	Prompt       = "一只橘色的小猫在阳光明媚的花园里追逐蝴蝶"
	Model        = "sora-2"
	Size         = "1280x720"
	Seconds      = "15"
	PollInterval = 30 * time.Second // 每 30 秒查询一次
	MaxWaitTime  = 10 * time.Minute // 最长等待 10 分钟
)

// VideoResponse 视频响应结构
type VideoResponse struct {
	ID          string `json:"id"`
	Status      string `json:"status"`
	Progress    int    `json:"progress"`
	URL         string `json:"url"`
	CreatedAt   int64  `json:"created_at"`
	CompletedAt int64  `json:"completed_at"`
}

// 第一步：提交文字生成视频请求
func step1SubmitRequest() (string, error) {
	fmt.Println("============================================================")
	fmt.Println("第一步：提交文字生成视频请求")
	fmt.Println("============================================================")

	// 创建 multipart form（使用 multipart/form-data 格式）
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// 添加表单字段
	writer.WriteField("prompt", Prompt)
	writer.WriteField("model", Model)
	writer.WriteField("size", Size)
	writer.WriteField("seconds", Seconds)

	writer.Close()

	fmt.Println("📤 发送请求...")
	fmt.Printf("   - 提示词: %s\n", Prompt)
	fmt.Printf("   - 模型: %s\n", Model)
	fmt.Printf("   - 尺寸: %s\n", Size)
	fmt.Printf("   - 时长: %s秒\n", Seconds)

	// 发送请求
	req, err := http.NewRequest("POST", BaseURL, body)
	if err != nil {
		return "", err
	}

	req.Header.Set("Authorization", APIKey)
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode == 200 {
		var result VideoResponse
		if err := json.Unmarshal(respBody, &result); err != nil {
			return "", err
		}

		fmt.Println("✅ 请求提交成功!")
		fmt.Printf("   - 视频ID: %s\n", result.ID)
		fmt.Printf("   - 状态: %s\n", result.Status)
		fmt.Printf("   - 创建时间: %s\n", time.Unix(result.CreatedAt, 0).Format("2006-01-02 15:04:05"))
		fmt.Println("   ⏱️  预计生成时间: 3-5 分钟")

		return result.ID, nil
	}

	return "", fmt.Errorf("❌ 请求失败: %d\n响应: %s", resp.StatusCode, string(respBody))
}

// 第二步：轮询查询视频状态
func step2PollStatus(videoID string) error {
	fmt.Println("\n============================================================")
	fmt.Println("第二步：查询视频生成状态")
	fmt.Println("============================================================")
	fmt.Printf("💡 提示：视频生成通常需要 3-5 分钟，每 %v 秒自动查询一次\n", int(PollInterval.Seconds()))

	startTime := time.Now()
	client := &http.Client{}

	for {
		elapsed := time.Since(startTime)

		// 检查超时
		if elapsed > MaxWaitTime {
			return fmt.Errorf("⏱️ 超时：已等待 %v，停止查询", MaxWaitTime)
		}

		fmt.Printf("\n🔍 查询状态... (已等待 %d 秒)\n", int(elapsed.Seconds()))

		// 查询状态
		statusURL := fmt.Sprintf("%s/%s", BaseURL, videoID)
		req, _ := http.NewRequest("GET", statusURL, nil)
		req.Header.Set("Authorization", APIKey)

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("❌ 请求失败: %v\n", err)
			time.Sleep(PollInterval)
			continue
		}

		respBody, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == 200 {
			var result VideoResponse
			if err := json.Unmarshal(respBody, &result); err != nil {
				fmt.Printf("❌ 解析响应失败: %v\n", err)
				time.Sleep(PollInterval)
				continue
			}

			fmt.Printf("   - 状态: %s\n", result.Status)
			fmt.Printf("   - 进度: %d%%\n", result.Progress)

			switch result.Status {
			case "completed":
				fmt.Println("✅ 视频生成完成!")
				fmt.Printf("   - 视频URL: %s\n", result.URL)
				fmt.Printf("   - 完成时间: %s\n", time.Unix(result.CompletedAt, 0).Format("2006-01-02 15:04:05"))
				return nil
			case "failed":
				return fmt.Errorf("❌ 视频生成失败")
			default:
				fmt.Printf("⏳ 视频生成中，等待 %d 秒后继续查询...\n", int(PollInterval.Seconds()))
				time.Sleep(PollInterval)
			}
		} else {
			fmt.Printf("❌ 状态查询失败: %d\n", resp.StatusCode)
			time.Sleep(PollInterval)
		}
	}
}

// 第三步：下载视频
func step3DownloadVideo(videoID string) error {
	fmt.Println("\n============================================================")
	fmt.Println("第三步：下载视频")
	fmt.Println("============================================================")

	// 提取 ID 后缀作为文件名
	outputFile := fmt.Sprintf("sora_text_video_%s.mp4", videoID[len(videoID)-8:])

	fmt.Println("📥 开始下载视频...")

	contentURL := fmt.Sprintf("%s/%s/content", BaseURL, videoID)
	req, _ := http.NewRequest("GET", contentURL, nil)
	req.Header.Set("Authorization", APIKey)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("❌ 下载请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("❌ 下载失败: %d\n响应: %s", resp.StatusCode, string(body))
	}

	// 保存文件
	out, err := os.Create(outputFile)
	if err != nil {
		return fmt.Errorf("❌ 创建文件失败: %v", err)
	}
	defer out.Close()

	size, err := io.Copy(out, resp.Body)
	if err != nil {
		return fmt.Errorf("❌ 保存文件失败: %v", err)
	}

	absPath, _ := filepath.Abs(outputFile)
	fmt.Println("✅ 视频下载成功!")
	fmt.Printf("   - 保存路径: %s\n", absPath)
	fmt.Printf("   - 文件大小: %d 字节\n", size)

	return nil
}

func main() {
	fmt.Println("\n🎬 开始 Sora-2 文字生成视频完整流程")
	fmt.Printf("⏰ 开始时间: %s\n\n", time.Now().Format("2006-01-02 15:04:05"))

	// 第一步：提交请求
	videoID, err := step1SubmitRequest()
	if err != nil {
		fmt.Printf("\n❌ 流程终止：%v\n", err)
		return
	}

	// 第二步：轮询状态
	if err := step2PollStatus(videoID); err != nil {
		fmt.Printf("\n❌ 流程终止：%v\n", err)
		return
	}

	// 第三步：下载视频
	if err := step3DownloadVideo(videoID); err != nil {
		fmt.Printf("\n❌ 流程终止：%v\n", err)
		return
	}

	fmt.Println("\n============================================================")
	fmt.Println("🎉 完整流程执行成功!")
	fmt.Println("============================================================")
	fmt.Printf("⏰ 结束时间: %s\n", time.Now().Format("2006-01-02 15:04:05"))
}
