# Nginx配置说明

## 问题分析

Excel文件在通过Nginx转发时出现截断现象，通常是由于Nginx的缓冲区设置不当造成的。当Nginx的代理缓冲区太小时，它可能会截断大文件或流式响应。

## 解决方案

我已经创建了一个优化的Nginx配置文件 (`nginx.conf`)，其中包含了以下关键设置：

1. 增加了 `client_max_body_size 100M` 来支持大文件上传
2. 设置了适当的代理缓冲区大小：
   - `proxy_buffer_size 128k`
   - `proxy_buffers 4 256k`
   - `proxy_busy_buffers_size 256k`
3. 对于API端点，特别是流式响应，禁用了代理缓冲：
   - `proxy_buffering off`
   - `proxy_cache off`
4. 配置了适当的超时设置

## 部署方式

### 方法1：直接部署到系统

1. 安装Nginx：
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. 复制配置文件：
   ```bash
   sudo cp /data/ai_wizard/nginx.conf /etc/nginx/nginx.conf
   ```

3. 测试配置文件语法：
   ```bash
   sudo nginx -t
   ```

4. 重启Nginx：
   ```bash
   sudo systemctl restart nginx
   ```

### 方法2：使用Docker部署

1. 构建Docker镜像：
   ```bash
   docker build -t nginx-ai-wizard -f nginx/Dockerfile .
   ```

2. 运行容器：
   ```bash
   docker run -d -p 80:80 --name nginx-ai-wizard nginx-ai-wizard
   ```

## 验证解决方案

配置完成后，重新测试Excel文件的上传和分析功能，应该不会再出现截断现象。