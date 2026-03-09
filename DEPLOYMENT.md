# GitHub 部署指南

本指南将帮助你将项目上传到 GitHub。

## 准备工作

### 1. 安装 Git

如果还没有安装 Git：

**Windows:**
- 访问 https://git-scm.com/download/win
- 下载并安装

**Linux:**
```bash
sudo apt-get install git  # Ubuntu/Debian
sudo yum install git       # CentOS/RHEL
```

**Mac:**
```bash
brew install git
```

### 2. 配置 Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 上传到 GitHub

### 方法一：通过 GitHub 网页创建仓库

1. **登录 GitHub**
   - 访问 https://github.com
   - 登录你的账户

2. **创建新仓库**
   - 点击右上角的 "+" 图标
   - 选择 "New repository"
   - 仓库名称填写: `industrial-protocol-clients`
   - 描述填写: `工业通信协议客户端库，支持Modbus TCP、FINS、CIP、Melsec等协议`
   - 选择 "Public" 或 "Private"
   - **不要**勾选 "Initialize this repository with a README"
   - 点击 "Create repository"

3. **在本地初始化并推送**

```bash
# 进入项目目录
cd industrial-protocol-clients

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 添加五个工业协议客户端"

# 添加远程仓库（替换 yourusername 为你的 GitHub 用户名）
git remote add origin https://github.com/yourusername/industrial-protocol-clients.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 方法二：使用 GitHub Desktop（推荐新手）

1. **下载 GitHub Desktop**
   - 访问 https://desktop.github.com/
   - 下载并安装

2. **登录并创建仓库**
   - 打开 GitHub Desktop
   - 登录你的 GitHub 账户
   - File → New Repository
   - Name: `industrial-protocol-clients`
   - Local Path: 选择项目所在目录的父目录
   - 点击 "Create Repository"

3. **发布到 GitHub**
   - 点击 "Publish repository"
   - 填写描述
   - 选择 Public 或 Private
   - 点击 "Publish Repository"

## 上传你的5个Python文件

你需要将以下5个文件放入项目目录：

1. `modbus_tcp_client.py`
2. `fins_client.py`
3. `cip_client.py`
4. `melsec_client.py`
5. `opt_controller.py`

### 步骤：

```bash
# 1. 将你的5个Python文件复制到项目根目录
cp /path/to/your/modbus_tcp_client.py ./
cp /path/to/your/fins_client.py ./
cp /path/to/your/cip_client.py ./
cp /path/to/your/melsec_client.py ./
cp /path/to/your/opt_controller.py ./

# 2. 添加文件到Git
git add modbus_tcp_client.py fins_client.py cip_client.py melsec_client.py opt_controller.py

# 3. 提交
git commit -m "添加核心协议客户端文件"

# 4. 推送到GitHub
git push
```

## 后续更新

当你修改代码或添加新文件时：

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .

# 3. 提交修改
git commit -m "描述你的修改内容"

# 4. 推送到GitHub
git push
```

## 创建 Release

当你准备发布正式版本时：

1. 在 GitHub 仓库页面点击 "Releases"
2. 点击 "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `v1.0.0 - 初始发布`
5. 描述发布内容
6. 点击 "Publish release"

## 设置仓库选项

### 添加主题标签

在仓库页面点击 "About" 旁边的齿轮图标，添加标签：
- `industrial-automation`
- `modbus`
- `plc`
- `python`
- `industrial-iot`
- `scada`

### 启用 Issues 和 Discussions

在仓库的 Settings → Features 中：
- 启用 "Issues"
- 启用 "Discussions"

### 添加描述和网站

在仓库主页点击 "About" 的齿轮图标：
- Description: `工业通信协议客户端库，支持Modbus TCP、FINS、CIP、Melsec等协议`
- Website: 如果有的话
- Topics: 添加相关标签

## 完善文档

### 更新 README 中的链接

在 `README.md` 中找到并替换：
- `yourusername` → 你的 GitHub 用户名
- `your.email@example.com` → 你的邮箱

### 添加徽章

在 README 顶部已经有了一些徽章，你可以自定义：

```markdown
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/yourusername/industrial-protocol-clients)](https://github.com/yourusername/industrial-protocol-clients/stargazers)
```

## 常见问题

### Q: 如何删除已提交的敏感信息？

```bash
# 从历史记录中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch PATH-TO-YOUR-FILE" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

### Q: 如何撤销最后一次提交？

```bash
# 保留修改
git reset --soft HEAD^

# 完全撤销
git reset --hard HEAD^
```

### Q: 忘记添加 .gitignore 怎么办？

```bash
# 移除已追踪的文件
git rm -r --cached .

# 重新添加
git add .

# 提交
git commit -m "更新 .gitignore"
```

## 推广你的项目

1. **添加到 awesome 列表**
   - 搜索相关的 awesome-xxx 仓库
   - 提交 PR 添加你的项目

2. **写博客文章**
   - 介绍项目的用途和特点
   - 分享使用案例

3. **社交媒体分享**
   - Twitter、LinkedIn
   - 相关技术论坛

4. **参与社区**
   - 回答相关问题
   - 帮助其他开发者

## 维护建议

- 定期查看和回复 Issues
- 审查和合并 Pull Requests
- 保持文档更新
- 发布新版本时更新 CHANGELOG
- 考虑设置 CI/CD 自动化测试

## 获取帮助

如果遇到问题：
- GitHub Docs: https://docs.github.com/
- Git Book: https://git-scm.com/book/zh/v2
- Stack Overflow: https://stackoverflow.com/

---

祝你的项目成功！🎉
