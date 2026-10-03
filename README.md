# DOIT Tech Atlas｜產業技術星圖

> 探索科技，看見產業未來。

GPT 版本的 DOIT Tech Atlas 展示站。

目前基準版本：**V11.2.1 Hotfix**

核心體驗：

**科技宇宙 → 技術銀河 → 技術星系 → 關鍵技術星星 → 科技星卡**

## 展示版重點

- 沉浸式宇宙背景、公轉、景深與 fly-through 轉場
- 滑鼠拖曳／觸控滑動快速旋轉軌道
- 長標籤最多兩行，避免破版
- Hover 聚焦目標星體
- Dr. T 一句式科技導覽
- 科技星卡以「市場分析／應用痛點／關鍵技術」為主體
- 延伸顯示應用場域、台灣機會與推薦星星
- V11.2.1 修正拖曳 Pointer Capture 攔截 click 的問題

## 專案結構

```
index.html
styles.css
app.js
data.js
galaxy-reference.jpg
vercel.json
```

這是純靜態展示站，可直接部署至 Vercel、Cloudflare Pages、Netlify 或任意靜態網站服務。

## Staging

下一步：連接 Vercel，將本 Repo 的 `main` branch 自動部署為 Staging。
