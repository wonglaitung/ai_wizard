# 前端设计配色方案 Skill

## 功能说明

此 skill 提供基于债券管理系统设计规范的专业配色方案，帮助开发者快速应用一致、专业的颜色系统。

## 配色方案

### 主色系 Primary Colors

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 主色 | `#3B82F6` | 蓝色系，专业、可靠 |
| 主色深色 | `#1e3a8a` | 深蓝色，用于表格表头、强调元素 |
| 品牌红 | `#8B1919` | 重要标识、品牌强调 |

### 功能色 Functional Colors

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 成功 | `#108981` | 青绿色，专业成功状态 |
| 成功深色 | `#0e7a75` | 深青绿色，悬停状态 |
| 警告 | `#F59E0B` | 橙色，警告提示 |
| 警告深色 | `#d97706` | 深橙色，悬停状态 |
| 危险 | `#EF4444` | 红色，错误、删除等危险操作 |
| 危险深色 | `#dc2626` | 深红色，悬停状态 |

### 中性色 Neutral Colors

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 标题文本 | `#1f2937` | 深灰色，标题文字 |
| 正文文本 | `#6b7280` | 中灰色，正文内容 |
| 边框 | `#e5e7eb` | 浅灰色，边框线条 |

### 背景色 Background Colors

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 主背景 | `#ffffff` | 白色，主要背景 |
| 次要背景 | `#f9fafb` | 浅灰色，次要区域 |
| 悬浮背景 | `#f3f4f6` | 悬浮效果背景 |
| 表格斑马纹 | `#f0f9ff` | 浅蓝色，表格交替行 |

### 侧边栏颜色 Sidebar Colors

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 侧边栏背景 | `#1e3a8a` | 深蓝色，与主色深色一致 |
| 侧边栏边框 | `#172554` | 更深的蓝色，用于边框分隔 |
| 侧边栏悬停 | `#1e40af` | 中蓝色，菜单项悬停背景 |

## 使用方式

### CSS 变量定义

```css
:root {
  /* 主色系 */
  --primary: #3B82F6;
  --primary-dark: #1e3a8a;
  --brand-red: #8B1919;

  /* 功能色 */
  --success: #108981;
  --success-dark: #0e7a75;
  --warning: #F59E0B;
  --warning-dark: #d97706;
  --danger: #EF4444;
  --danger-dark: #dc2626;

  /* 中性色 */
  --neutral-heading: #1f2937;
  --neutral-body: #6b7280;
  --border: #e5e7eb;

  /* 背景色 */
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-hover: #f3f4f6;
  --bg-table-zebra: #f0f9ff;

  /* 侧边栏颜色 */
  --sidebar-bg: #1e3a8a;
  --sidebar-border: #172554;
  --sidebar-hover: #1e40af;
}
```

### 实际应用示例

```css
/* 按钮样式 */
.btn-primary {
  background-color: var(--primary);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
}

/* 状态标签 */
.status-success {
  background-color: var(--success);
  color: white;
}

.status-warning {
  background-color: var(--warning);
  color: white;
}

.status-danger {
  background-color: var(--danger);
  color: white;
}

/* 卡片样式 */
.card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.card:hover {
  border-color: var(--primary);
}

/* 表格样式 */
table {
  background-color: var(--bg-primary);
  border-collapse: collapse;
}

th {
  background-color: var(--primary-dark);
  color: white;
}

tbody tr:nth-child(even) {
  background-color: var(--bg-table-zebra);
}

tbody tr:hover {
  background-color: var(--bg-hover);
}
```

### JavaScript 使用示例

```javascript
// 获取配色方案
const colorScheme = {
  primary: '#3B82F6',
  primaryDark: '#1e3a8a',
  brandRed: '#8B1919',
  success: '#108981',
  successDark: '#0e7a75',
  warning: '#F59E0B',
  warningDark: '#d97706',
  danger: '#EF4444',
  dangerDark: '#dc2626',
  neutralHeading: '#1f2937',
  neutralBody: '#6b7280',
  border: '#e5e7eb',
  bgPrimary: '#ffffff',
  bgSecondary: '#f9fafb',
  bgHover: '#f3f4f6',
  bgTableZebra: '#f0f9ff',
  sidebarBg: '#1e3a8a',
  sidebarBorder: '#172554',
  sidebarHover: '#1e40af'
};

// 动态设置颜色
function setElementColor(element, colorType) {
  element.style.color = colorScheme[colorType];
}

// 动态设置背景
function setElementBackground(element, bgColorType) {
  element.style.backgroundColor = colorScheme[bgColorType];
}
```

## 设计原则

1. **色彩一致性**：统一使用蓝色系作为主色调，保持专业感
2. **功能性**：成功（青绿）、警告（橙）、危险（红）清晰区分
3. **可访问性**：确保文字与背景有足够对比度（WCAG AA 标准）
4. **品牌识别**：品牌红 (#8B1919) 用于重要品牌标识

## 视觉效果

- ✅ 更专业的蓝色系主色调
- ✅ 成功色从绿色改为青绿色，更符合金融行业风格
- ✅ 统一的中性色体系，提高整体一致性
- ✅ 新增品牌红色，可用于重要标识和强调
- ✅ 优化的背景色系统，包括表格斑马纹

## 更新日期

2026-01-21