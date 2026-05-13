import '../models/agent_recommendation.dart';
import '../models/compare_result.dart';
import '../models/product.dart';

const _imgMouse = 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?auto=format&fit=crop&w=900&q=80';
const _imgKeyboard = 'https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?auto=format&fit=crop&w=900&q=80';
const _imgHeadset = 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80';
const _imgMonitor = 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80';

final mockProducts = <Product>[
  _p('m001', 'VXE R1 Pro Max', 'VXE', 'mouse', 299, 4.8, 12500, _imgMouse,
      ['PAW3395', '49g', '8000Hz', '三模连接', '轻量化'], '49g 轻量化无线游戏鼠标，主打 FPS 低延迟和高性价比。', 95),
  _p('m002', 'Logitech G Pro X Superlight 2', 'Logitech', 'mouse', 999, 4.7, 9800, _imgMouse,
      ['HERO 2', '60g', 'LightSpeed', '职业选手'], '旗舰无线电竞鼠标，适合追求稳定手感和品牌生态的高阶玩家。', 92),
  _p('m003', 'Razer Viper V3 Pro', 'Razer', 'mouse', 899, 4.6, 8200, _imgMouse,
      ['Focus Pro 30K', '54g', '8000Hz', '电竞利器'], '雷蛇旗舰对称鼠，强调高速回报率和竞技手感。', 89),
  _p('m004', 'HyperX Pulsefire Haste 2', 'HyperX', 'mouse', 399, 4.6, 6200, _imgMouse,
      ['53g', '26000DPI', '8000Hz', 'PTFE脚贴'], '轻量化游戏鼠标，均衡覆盖 FPS 和 MOBA。', 91),
  _p('m005', 'Logitech G304', 'Logitech', 'mouse', 199, 4.7, 8600, _imgMouse,
      ['HERO', '99g', '无线', '长续航'], '经典入门无线游戏鼠标，适合预算有限的新手玩家。', 86),
  _p('m006', 'ATK F1 Extreme', 'ATK', 'mouse', 459, 4.5, 3900, _imgMouse,
      ['PAW3950', '38g', '8K', '旗舰轻量'], '超轻量高性能鼠标，面向追求极限操控的玩家。', 90),
  _p('k001', 'WOBKEY Rainy75', 'WOBKEY', 'keyboard', 699, 4.6, 8600, _imgKeyboard,
      ['75%配列', 'Gasket结构', '客制化', 'PBT键帽'], '高颜值 75% 客制化机械键盘，适合桌搭与游戏兼顾。', 93),
  _p('k002', 'AULA F75', 'AULA', 'keyboard', 249, 4.6, 9800, _imgKeyboard,
      ['75%配列', '三模', 'Gasket', '热插拔'], '高性价比 75% 三模机械键盘，适合预算有限但想要好手感的用户。', 94),
  _p('k003', 'K87 静音红轴机械键盘', 'KeyFlow', 'keyboard', 299, 4.5, 5100, _imgKeyboard,
      ['87键', '静音红轴', '低噪音', '办公游戏'], '兼顾游戏和宿舍办公的静音机械键盘。', 88),
  _p('k004', 'Lite68 办公静音键盘', 'LiteKeys', 'keyboard', 199, 4.4, 4300, _imgKeyboard,
      ['68键', '静音', '便携', '蓝牙'], '小配列静音键盘，适合宿舍、图书馆和移动办公。', 84),
  _p('k005', 'X75 三模机械键盘', 'XGear', 'keyboard', 359, 4.5, 5200, _imgKeyboard,
      ['75%', '三模', '旋钮', 'RGB'], '带旋钮的三模 75% 键盘，适合游戏和效率场景。', 89),
  _p('k006', 'Keychron K2 Pro', 'Keychron', 'keyboard', 449, 4.6, 6800, _imgKeyboard,
      ['75%', 'QMK/VIA', 'Mac友好', '三模'], '面向程序员和多系统用户的可编程机械键盘。', 87),
  _p('k007', 'Leobog Hi75', 'Leobog', 'keyboard', 349, 4.6, 6600, _imgKeyboard,
      ['铝坨坨', '75%', '热插拔', '旋钮'], '入门铝坨坨机械键盘，声音和手感有明显升级。', 86),
  _p('k008', 'IQUNIX ZX75', 'IQUNIX', 'keyboard', 899, 4.7, 2800, _imgKeyboard,
      ['高端量产', '75%', '三模', 'PBT'], '设计感强的高端量产键盘，适合注重桌面审美的玩家。', 85),
  _p('h001', 'HyperX Cloud III Wireless', 'HyperX', 'headset', 799, 4.6, 5100, _imgHeadset,
      ['无线', 'DTS', '长续航', '舒适'], '舒适耐戴的无线电竞耳机，适合长时间游戏和语音开黑。', 90),
  _p('h002', 'SteelSeries Arctis Nova 5', 'SteelSeries', 'headset', 899, 4.5, 3600, _imgHeadset,
      ['无线', '多平台', '低延迟', '轻量'], '多平台无线电竞耳机，适合 PC、主机和移动设备切换。', 88),
  _p('h003', 'Razer BlackShark V2 X', 'Razer', 'headset', 299, 4.4, 7200, _imgHeadset,
      ['有线', '轻量', '7.1', '入门电竞'], '入门有线电竞耳机，适合预算有限的 FPS 玩家。', 86),
  _p('h004', 'Logitech G Pro X 2 Lightspeed', 'Logitech', 'headset', 1299, 4.7, 3100, _imgHeadset,
      ['石墨烯单元', 'Lightspeed', '蓝牙', '旗舰'], '旗舰无线电竞耳机，强调听声辨位和多连接能力。', 87),
  _p('p001', 'Artisan Zero FX Soft 鼠标垫', 'Artisan', 'mousepad', 399, 4.8, 2600, _imgMouse,
      ['控制型', 'Soft', 'FPS', '细面'], '高端控制型鼠标垫，适合 FPS 精准急停。', 91),
  _p('d001', 'AOC AG275QZ 27英寸电竞显示器', 'AOC', 'monitor', 2499, 4.6, 4100, _imgMonitor,
      ['2K', '240Hz', 'Fast IPS', 'HDR400'], '2K 240Hz 高刷显示器，适合 FPS 和综合游戏体验。', 88),
];

Product _p(
  String id,
  String name,
  String brand,
  String category,
  double price,
  double rating,
  int sales,
  String image,
  List<String> tags,
  String desc,
  int score,
) {
  return Product(
    id: id,
    name: name,
    brand: brand,
    category: category,
    price: price,
    rating: rating,
    sales: sales,
    imageUrl: image,
    tags: tags,
    description: desc,
    specs: {
      '传感器': category == 'mouse' ? tags.first : '未标注',
      '重量': category == 'mouse' ? tags.firstWhere((e) => e.endsWith('g'), orElse: () => '约 60g') : '未标注',
      '连接': tags.contains('三模') || tags.contains('三模连接') ? '有线 / 2.4G / 蓝牙' : '有线 / 2.4G',
      '噪音': tags.any((e) => e.contains('静音')) ? '低噪音' : '常规',
      '回报率': tags.contains('8000Hz') ? '8000Hz' : '1000Hz',
    },
    pros: ['核心配置贴合电竞使用', '同价位口碑稳定', '外设玩家讨论热度高'],
    cons: ['不同手型或桌面环境仍建议试用', '部分高级功能需要驱动配置'],
    recommendedFor: ['FPS 玩家', '电竞桌搭', '外设升级用户'],
    notRecommendedFor: ['只需要基础办公', '对价格极度敏感'],
    reviewSummary: '用户普遍认可性能和手感，主要差评集中在价格、驱动或个体适配。',
    matchScore: score,
  );
}

Product findMockProduct(String id) =>
    mockProducts.firstWhere((p) => p.id == id, orElse: () => mockProducts.first);

AgentResponse mockAgentResponse() {
  final recs = mockProducts
      .where((p) => p.category == 'mouse')
      .take(4)
      .map((p) => AgentRecommendation(
            product: p,
            matchScore: p.matchScore,
            reason: '${p.tags.take(3).join('、')}，适合 FPS 游戏和低延迟无线需求。',
          ))
      .toList();
  return AgentResponse(
    intent: {
      'category': 'mouse',
      'budget': 300,
      'scenario': 'FPS游戏',
      'priorities': ['轻量化', '低延迟', '无线']
    },
    recommendations: recs,
    summary: '综合来看，最推荐 VXE R1 Pro Max；预算更低可考虑罗技 G304。',
    pitfalls: ['如果手型偏大，建议优先试握。'],
  );
}

CompareResult mockCompareResult() {
  final products = ['k003', 'k004', 'k005'].map(findMockProduct).toList();
  final table = <String, Map<String, dynamic>>{};
  for (final row in ['商品图', '价格', '品牌', '评分', '销量', '适合场景', '噪音表现', '连接方式', '优点', '缺点', '推荐指数', '购买建议']) {
    table[row] = {
      for (final p in products)
        p.id: switch (row) {
          '商品图' => p.imageUrl,
          '价格' => '￥${p.price.toStringAsFixed(0)}',
          '品牌' => p.brand,
          '评分' => p.rating,
          '销量' => p.sales,
          '适合场景' => p.recommendedFor.join(' / '),
          '噪音表现' => p.specs['噪音'],
          '连接方式' => p.specs['连接'],
          '优点' => p.pros.join(' / '),
          '缺点' => p.cons.join(' / '),
          '推荐指数' => '${p.matchScore}分',
          _ => p.description,
        }
    };
  }
  return CompareResult(
    products: products,
    table: table,
    summary: 'AI 根据噪音、连接、价格和场景匹配生成对比结论。',
    finalRecommendation: '如果优先宿舍静音，K87 静音红轴最稳；如果想要无线与桌搭完整性，X75 三模更均衡。',
  );
}
