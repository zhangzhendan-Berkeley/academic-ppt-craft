# 从反馈到下一版

1. **收集问题**：Issue写背景、实际结果、期望、版本和匿名化示例。Discussions适合讨论未定型想法。
2. **判定范围**：通用教学问题、模板参数、个人偏好、特定课知识、单页修正分别处理。
3. **修改规则与例子**：找到唯一有效文档，替换冲突旧条；补边界和有用反例。
4. **实际验证**：检查受影响的课件内容、图形与播放器；检查资源授权、附件哈希和相对链接。
5. **审阅与发布**：PR记录问题与结果，维护者合并后更新版本、发布完整Release。Release是固定版本，main为后续工作，不混淆。

## 本地打包

在仓库根目录运行：

```text
python skills/academic-ppt-craft/scripts/package_skill.py skills/academic-ppt-craft --output dist/academic-ppt-craft_v1.4.0.zip
```

脚本不依赖第三方库，检查已登记附件、相对链接和SHA256，并生成PACKAGE_MANIFEST.json。替换附件时先检查新文件与授权，再更新附件登记，不能为了过检查盲目更新哈希。

模板结构检查需python-pptx与lxml：

```text
python skills/academic-ppt-craft/scripts/inspect_template.py skills/academic-ppt-craft/assets/ppt-template.pptx --output skills/academic-ppt-craft/assets/template-profile.json
```

脚本只读取直接声明的格式；原生渲染、媒体播放和教学审核仍由实际制作流程完成。

## 版本策略

1.3.0是首次公共版，继承此前私有课件实践的修订号。修错用补丁；增加兼容规范、资源和方法用次版本；破坏旧使用方式才提升主版本。公开版与个人版分开发布：公共经验可同步，个人路径、课程主题和秘密素材不能同步。

外部分享优先发送仓库主页与Release链接，避免只转发一份过时ZIP。更新前备份自己的配置，核对变更再合并，不能用公共新版本覆盖教师的个人偏好。
