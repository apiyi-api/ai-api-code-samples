import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import org.json.JSONObject;

/**
 * Sora-2 视频生成完整异步流程 - Java 版本
 *
 * 依赖: org.json (添加到 pom.xml 或下载 json-20240303.jar)
 * Maven:
 * <dependency>
 *     <groupId>org.json</groupId>
 *     <artifactId>json</artifactId>
 *     <version>20240303</version>
 * </dependency>
 *
 * 编译: javac -cp json-20240303.jar Sora2CompleteAsync.java
 * 运行: java -cp .:json-20240303.jar Sora2CompleteAsync
 */
public class Sora2CompleteAsync {

    // 配置参数
    private static final String BASE_URL = "https://api.apiyi.com/v1/videos";
    private static final String API_KEY = "sk-";
    private static final String PROMPT = "参考配图，使得动物们活跃起来，在场地里绕场一周的追逐";
    private static final String IMAGE_PATH = "/Users/chenkang/Downloads/dog-and-cat.png";
    private static final String MODEL = "sora-2";
    private static final String SIZE = "1280x720";
    private static final String SECONDS = "10";

    // 轮询配置
    private static final int POLL_INTERVAL = 30000; // 30 秒
    private static final int MAX_WAIT_TIME = 600000; // 10 分钟

    private static final String BOUNDARY = "----WebKitFormBoundary" + System.currentTimeMillis();

    /**
     * 第一步：提交视频生成请求
     */
    private static String step1SubmitRequest() throws Exception {
        System.out.println("============================================================");
        System.out.println("第一步：提交视频生成请求");
        System.out.println("============================================================");

        File imageFile = new File(IMAGE_PATH);
        if (!imageFile.exists()) {
            throw new FileNotFoundException("❌ 错误：图片文件不存在: " + IMAGE_PATH);
        }

        System.out.println("📤 发送请求...");
        System.out.println("   - 提示词: " + PROMPT);
        System.out.println("   - 图片: " + IMAGE_PATH);
        System.out.println("   - 尺寸: " + SIZE);
        System.out.println("   - 时长: " + SECONDS + "秒");

        URL url = new URL(BASE_URL);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setRequestProperty("Authorization", API_KEY);
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);

        try (OutputStream out = conn.getOutputStream();
             PrintWriter writer = new PrintWriter(new OutputStreamWriter(out, "UTF-8"), true)) {

            // 添加表单字段
            addFormField(writer, "prompt", PROMPT);
            addFormField(writer, "model", MODEL);
            addFormField(writer, "size", SIZE);
            addFormField(writer, "seconds", SECONDS);

            // 添加文件
            addFilePart(writer, out, "input_reference", imageFile);

            // 结束边界
            writer.append("--").append(BOUNDARY).append("--").append("\r\n");
        }

        int responseCode = conn.getResponseCode();
        String responseBody = readResponse(conn);

        if (responseCode == 200) {
            JSONObject result = new JSONObject(responseBody);
            String videoId = result.getString("id");
            String status = result.getString("status");
            long createdAt = result.getLong("created_at");

            System.out.println("✅ 请求提交成功!");
            System.out.println("   - 视频ID: " + videoId);
            System.out.println("   - 状态: " + status);
            System.out.println("   - 创建时间: " + formatTimestamp(createdAt));
            System.out.println("   ⏱️  预计生成时间: 3-5 分钟");

            return videoId;
        } else {
            throw new IOException("❌ 请求失败: " + responseCode + "\n响应: " + responseBody);
        }
    }

    /**
     * 第二步：轮询查询视频状态
     */
    private static void step2PollStatus(String videoId) throws Exception {
        System.out.println("\n============================================================");
        System.out.println("第二步：查询视频生成状态");
        System.out.println("============================================================");
        System.out.println("💡 提示：视频生成通常需要 3-5 分钟，每 30 秒自动查询一次");

        long startTime = System.currentTimeMillis();

        while (true) {
            long elapsed = System.currentTimeMillis() - startTime;

            // 检查超时
            if (elapsed > MAX_WAIT_TIME) {
                throw new Exception("⏱️ 超时：已等待 " + (MAX_WAIT_TIME / 1000) + " 秒，停止查询");
            }

            System.out.println("\n🔍 查询状态... (已等待 " + (elapsed / 1000) + " 秒)");

            URL url = new URL(BASE_URL + "/" + videoId);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Authorization", API_KEY);

            int responseCode = conn.getResponseCode();
            String responseBody = readResponse(conn);

            if (responseCode == 200) {
                JSONObject result = new JSONObject(responseBody);
                String status = result.getString("status");
                int progress = result.optInt("progress", 0);

                System.out.println("   - 状态: " + status);
                System.out.println("   - 进度: " + progress + "%");

                switch (status) {
                    case "completed":
                        System.out.println("✅ 视频生成完成!");
                        System.out.println("   - 视频URL: " + result.optString("url"));
                        System.out.println("   - 完成时间: " + formatTimestamp(result.optLong("completed_at")));
                        return;
                    case "failed":
                        throw new Exception("❌ 视频生成失败");
                    default:
                        System.out.println("⏳ 视频生成中，等待 " + (POLL_INTERVAL / 1000) + " 秒后继续查询...");
                        Thread.sleep(POLL_INTERVAL);
                }
            } else {
                System.out.println("❌ 状态查询失败: " + responseCode);
                Thread.sleep(POLL_INTERVAL);
            }
        }
    }

    /**
     * 第三步：下载视频
     */
    private static void step3DownloadVideo(String videoId) throws Exception {
        System.out.println("\n============================================================");
        System.out.println("第三步：下载视频");
        System.out.println("============================================================");

        String outputFile = "sora_video_" + videoId.substring(Math.max(0, videoId.length() - 8)) + ".mp4";

        System.out.println("📥 开始下载视频...");

        URL url = new URL(BASE_URL + "/" + videoId + "/content");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", API_KEY);

        int responseCode = conn.getResponseCode();

        if (responseCode == 200) {
            try (InputStream in = conn.getInputStream();
                 FileOutputStream out = new FileOutputStream(outputFile)) {

                byte[] buffer = new byte[8192];
                int bytesRead;
                long totalBytes = 0;

                while ((bytesRead = in.read(buffer)) != -1) {
                    out.write(buffer, 0, bytesRead);
                    totalBytes += bytesRead;
                }

                System.out.println("✅ 视频下载成功!");
                System.out.println("   - 保存路径: " + new File(outputFile).getAbsolutePath());
                System.out.println("   - 文件大小: " + totalBytes + " 字节");
            }
        } else {
            throw new IOException("❌ 下载失败: " + responseCode);
        }
    }

    /**
     * 主流程
     */
    public static void main(String[] args) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        System.out.println("\n🎬 开始 Sora-2 视频生成完整流程");
        System.out.println("⏰ 开始时间: " + LocalDateTime.now().format(formatter));
        System.out.println();

        try {
            // 第一步：提交请求
            String videoId = step1SubmitRequest();

            // 第二步：轮询状态
            step2PollStatus(videoId);

            // 第三步：下载视频
            step3DownloadVideo(videoId);

            System.out.println("\n============================================================");
            System.out.println("🎉 完整流程执行成功!");
            System.out.println("============================================================");
            System.out.println("⏰ 结束时间: " + LocalDateTime.now().format(formatter));

        } catch (Exception e) {
            System.err.println("\n❌ 流程终止：" + e.getMessage());
            e.printStackTrace();
        }
    }

    // ========== 工具方法 ==========

    private static void addFormField(PrintWriter writer, String name, String value) {
        writer.append("--").append(BOUNDARY).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(name).append("\"").append("\r\n");
        writer.append("\r\n");
        writer.append(value).append("\r\n");
    }

    private static void addFilePart(PrintWriter writer, OutputStream out, String fieldName, File file) throws IOException {
        String fileName = file.getName();
        writer.append("--").append(BOUNDARY).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(fieldName)
              .append("\"; filename=\"").append(fileName).append("\"").append("\r\n");
        writer.append("Content-Type: ").append(Files.probeContentType(file.toPath())).append("\r\n");
        writer.append("\r\n");
        writer.flush();

        try (FileInputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = in.read(buffer)) != -1) {
                out.write(buffer, 0, bytesRead);
            }
            out.flush();
        }

        writer.append("\r\n");
        writer.flush();
    }

    private static String readResponse(HttpURLConnection conn) throws IOException {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(
                    conn.getResponseCode() < 400 ? conn.getInputStream() : conn.getErrorStream()))) {
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            return response.toString();
        }
    }

    private static String formatTimestamp(long timestamp) {
        if (timestamp == 0) return "N/A";
        LocalDateTime dateTime = LocalDateTime.ofInstant(
            Instant.ofEpochSecond(timestamp), ZoneId.systemDefault());
        return dateTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }
}
