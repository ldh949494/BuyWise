# 商品目录数据源标准

BuyWise 的商品数据源是人工维护、可校验、可导入的商品目录 CSV。Closed beta 阶段不要让商品卡片直接依赖第三方图片热链；商品图片应先进入腾讯 COS，商品表只保存可被浏览器无登录访问的 COS URL。

## 标准数据流

1. 准备真实商品目录 CSV：本地忽略文件 `.\data\beta-catalog.csv`。
2. 把商品主图和图库图片上传到腾讯 COS。
3. 在 CSV 的 `image_url` 和 `image_urls` 中填写 COS 公网 URL。
4. 校验 CSV。
5. 导入商品表。
6. 重建或更新商品向量索引。

```powershell
python -m app.scripts.validate_beta_catalog --csv .\data\beta-catalog.csv
python -m app.scripts.import_products --csv .\data\beta-catalog.csv --require-real-assets
python -m app.scripts.build_vector_index --mode rebuild
```

## CSV 表头

Closed beta 目录必须严格使用以下表头和顺序：

```csv
sku,name,category,brand,price,original_price,platform,product_url,image_url,image_urls,rating,sales,description,specs,tags,suitable_scene,stock,stock_status,review_summary
```

模板文件：`data/beta-catalog.template.csv`。

## 字段标准

| 字段 | 标准 |
| --- | --- |
| `sku` | 稳定唯一 ID。Closed beta 使用 `beta-...` slug 格式，例如 `beta-keyboard-keynova-k75`。 |
| `name` | 商品名，必填。 |
| `category` | 必须是 `机械键盘`、`蓝牙耳机`、`台灯`、`充电宝`、`双肩包` 之一。 |
| `brand` | 品牌或店铺名。每个类目至少 4 个品牌或店铺，单品牌每类最多 3 个 SKU。 |
| `price` | 当前价，必填，非负数字。 |
| `original_price` | 原价，可空，建议填写。 |
| `platform` | 商品来源平台，例如京东、天猫、淘宝、拼多多。 |
| `product_url` | 真实商品页 URL，必须无需登录可打开，不能是 `example.com`、`localhost` 或 `127.0.0.1`。 |
| `image_url` | 主图 URL，必须是无需登录可访问的真实图片 URL；推荐 COS URL。 |
| `image_urls` | JSON 数组，详情页图库；推荐包含主图和其他详情图。 |
| `rating` | 评分，数字，可空。 |
| `sales` | 销量，整数，可空。 |
| `description` | 商品描述，用于 RAG、导购和详情展示。 |
| `specs` | JSON 对象，例如 `{"layout":"75键","connection":"蓝牙/2.4G/有线"}`。 |
| `tags` | JSON 数组，4 到 8 个，必须来自 `docs/reference/beta-catalog-taxonomy.md`。 |
| `suitable_scene` | JSON 数组，2 到 5 个，必须来自 `docs/reference/beta-catalog-taxonomy.md`。 |
| `stock` | 库存整数；和 `stock_status` 至少有一个。 |
| `stock_status` | 建议使用 `in_stock`、`low_stock`、`out_of_stock`、`discontinued`。 |
| `review_summary` | 必填，用于推荐解释和商品可信度展示。 |

## 图片标准

商品卡片优先使用 `image_url`；详情页可使用 `image_urls` 做轮播。图片 URL 必须能被 Android、Web、后端视觉模型和用户浏览器稳定访问。

禁止把第三方热链作为长期数据源：

```csv
https://example.com/images/k87.jpg
https://img.alicdn.com/xxx.jpg
https://m.media-amazon.com/xxx.jpg
```

推荐使用 COS URL：

```csv
https://<bucket>.cos.<region>.myqcloud.com/product-images/beta-keyboard-keynova-k75/main.jpg
```

COS 对象必须公开可读，或通过已配置的公开 CDN/自定义域名访问。Closed beta 最小可行方案是让 `product-images/` 前缀公开读，并把图片生命周期和权限纳入 COS bucket 配置。

`image_urls` 必须是 CSV 中的 JSON 数组字符串：

```csv
"[""https://<bucket>.cos.<region>.myqcloud.com/product-images/beta-keyboard-keynova-k75/main.jpg"",""https://<bucket>.cos.<region>.myqcloud.com/product-images/beta-keyboard-keynova-k75/detail-1.jpg""]"
```

如果商品表里已经存在可下载的外部图片 URL，可先迁移到 COS：

```powershell
python -m app.scripts.migrate_product_images_to_cos
python -m app.scripts.migrate_product_images_to_cos --apply
```

如果原始 URL 是占位地址、已过期地址或防盗链地址，迁移脚本无法凭空生成图片，需要先拿到真实图片文件并通过后台上传或其他 COS 上传流程写入。

## Closed Beta 目录规模

第一版 closed beta 目录使用固定规模：

- 5 个类目。
- 每类 10 个 SKU。
- 合计 50 个商品。
- 每类覆盖低、中、高价格带。
- 每类至少 4 个品牌或店铺。
- 单品牌或单店铺每类最多 3 个 SKU。

## Taxonomy

`tags` 和 `suitable_scene` 必须从 `docs/reference/beta-catalog-taxonomy.md` 中选择，避免同义词漂移。

常用通用标签：

- `性价比`
- `轻便`
- `耐用`
- `高颜值`
- `送礼`
- `学生党`
- `办公`
- `便携`

常用场景：

- `宿舍`
- `通勤`
- `办公`
- `学习`
- `写代码`
- `阅读`
- `旅行`
- `送礼`
- `应急`
- `备考`
- `上课`
- `运动`

不要混用近义词，例如 `宿舍`、`寝室`、`学生宿舍` 统一使用 `宿舍`。价格、库存、平台名和型号不要写入 `tags`，这类信息应放在专门字段或 `specs` 中。

## 示例行

```csv
beta-keyboard-keynova-k75,KeyNova K75 静音三模机械键盘,机械键盘,KeyNova,299.00,369.00,京东,https://item.jd.com/real-product-url.html,https://<bucket>.cos.<region>.myqcloud.com/product-images/beta-keyboard-keynova-k75/main.jpg,"[""https://<bucket>.cos.<region>.myqcloud.com/product-images/beta-keyboard-keynova-k75/main.jpg""]",4.80,1820,静音轴体和三模连接，适合宿舍写代码和学习。,"{""layout"":""75键"",""connection"":""蓝牙/2.4G/有线"",""switch"":""静音线性轴""}","[""低噪音"",""无线"",""三模"",""性价比""]","[""宿舍"",""写代码"",""学习""]",24,in_stock,按键声音低，蓝牙稳定，宿舍夜间使用不容易打扰室友。
```

## 验收标准

一份可进入 closed beta 的商品目录必须满足：

- `validate_beta_catalog` 返回 `ok: true`。
- `import_products --require-real-assets` 可成功导入。
- 商品列表和详情接口返回的 `image_url` 能直接在浏览器打开。
- Android 商品卡片能稳定显示主图。
- Chroma 商品索引完成重建或 upsert，`check_vector_index` 无缺失 active 商品。
