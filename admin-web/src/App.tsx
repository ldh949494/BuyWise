import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  clearToken,
  createProduct,
  deleteProduct,
  getProduct,
  getToken,
  listProducts,
  login,
  updateProduct,
  uploadImage
} from "./api";
import type { Product, ProductPayload } from "./types";

type FormState = {
  name: string;
  category: string;
  brand: string;
  sku: string;
  price: string;
  original_price: string;
  stock: string;
  stock_status: string;
  platform: string;
  product_url: string;
  image_url: string;
  image_urls: string;
  rating: string;
  sales: string;
  description: string;
  review_summary: string;
  tags: string;
  suitable_scene: string;
  specs: string;
  feedback_metrics: string;
};

const emptyForm: FormState = {
  name: "",
  category: "",
  brand: "",
  sku: "",
  price: "",
  original_price: "",
  stock: "",
  stock_status: "",
  platform: "",
  product_url: "",
  image_url: "",
  image_urls: "",
  rating: "",
  sales: "",
  description: "",
  review_summary: "",
  tags: "",
  suitable_scene: "",
  specs: "{}",
  feedback_metrics: "{}"
};

export default function App() {
  const [tokenVersion, setTokenVersion] = useState(0);
  const isAuthed = Boolean(getToken());

  function signOut() {
    clearToken();
    setTokenVersion((value) => value + 1);
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage onLogin={() => setTokenVersion(tokenVersion + 1)} />} />
      <Route
        path="/*"
        element={
          isAuthed ? (
            <Shell onSignOut={signOut} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  );
}

function Shell({ onSignOut }: { onSignOut: () => void }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          BuyWise Admin
        </Link>
        <nav>
          <Link to="/">商品</Link>
          <button type="button" className="ghost-button" onClick={onSignOut}>
            退出
          </button>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<ProductListPage />} />
          <Route path="/products/new" element={<ProductFormPage mode="create" />} />
          <Route path="/products/:productId" element={<ProductFormPage mode="edit" />} />
        </Routes>
      </main>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: () => void }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await login(username, password);
      onLogin();
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="login-layout">
      <form className="login-panel" onSubmit={submit}>
        <h1>BuyWise Admin</h1>
        <label>
          用户名
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
        </label>
        <label>
          密码
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            autoComplete="current-password"
          />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button type="submit" disabled={isLoading}>
          {isLoading ? "登录中" : "登录"}
        </button>
      </form>
    </main>
  );
}

function ProductListPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: "20"
    });
    if (keyword) params.set("keyword", keyword);
    if (category) params.set("category", category);

    setIsLoading(true);
    listProducts(params)
      .then((payload) => {
        setProducts(payload.items);
        setTotal(payload.total);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"))
      .finally(() => setIsLoading(false));
  }, [page, keyword, category]);

  const pageCount = Math.max(1, Math.ceil(total / 20));

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h1>商品管理</h1>
          <p>{total} 个商品</p>
        </div>
        <Link className="primary-link" to="/products/new">
          新建商品
        </Link>
      </div>

      <div className="toolbar">
        <input placeholder="搜索名称、描述、品牌" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
        <input placeholder="类目" value={category} onChange={(event) => setCategory(event.target.value)} />
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>商品</th>
              <th>类目</th>
              <th>价格</th>
              <th>库存</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7}>加载中</td>
              </tr>
            ) : (
              products.map((product) => (
                <tr key={product.id}>
                  <td>{product.id}</td>
                  <td>
                    <div className="product-cell">
                      {product.image_url ? <img src={product.image_url} alt="" /> : <span className="image-placeholder" />}
                      <div>
                        <strong>{product.name}</strong>
                        <span>{product.brand || product.sku || "-"}</span>
                      </div>
                    </div>
                  </td>
                  <td>{product.category || "-"}</td>
                  <td>{formatMoney(product.price)}</td>
                  <td>{product.stock ?? "-"}</td>
                  <td>
                    <span className={`status-badge ${product.stock_status || "unknown"}`}>
                      {product.stock_status || "unknown"}
                    </span>
                  </td>
                  <td>
                    <Link to={`/products/${product.id}`}>编辑</Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>
          上一页
        </button>
        <span>
          {page} / {pageCount}
        </span>
        <button type="button" disabled={page >= pageCount} onClick={() => setPage(page + 1)}>
          下一页
        </button>
      </div>
    </section>
  );
}

function ProductFormPage({ mode }: { mode: "create" | "edit" }) {
  const navigate = useNavigate();
  const { productId } = useParams();
  const id = Number(productId);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(mode === "edit");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (mode !== "edit" || !id) return;
    setIsLoading(true);
    getProduct(id)
      .then((product) => {
        setForm(productToForm(product));
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"))
      .finally(() => setIsLoading(false));
  }, [id, mode]);

  const title = mode === "create" ? "新建商品" : `编辑商品 #${id}`;
  const canDelete = mode === "edit" && form.stock_status !== "discontinued";
  const parsedPayload = useMemo(() => {
    try {
      return formToPayload(form);
    } catch {
      return null;
    }
  }, [form]);

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setError("");
    setNotice("");
    try {
      const payload = formToPayload(form);
      const response = mode === "create" ? await createProduct(payload) : await updateProduct(id, payload);
      setForm(productToForm(response.product));
      setNotice(`保存成功，索引同步状态：${response.index_sync_status}`);
      if (mode === "create") {
        navigate(`/products/${response.product.id}`, { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setIsSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm("确认下架这个商品？")) return;
    setError("");
    const response = await deleteProduct(id);
    setForm(productToForm(response.product));
    setNotice("商品已下架");
  }

  async function handleUpload(file: File, target: "main" | "gallery") {
    setError("");
    try {
      const uploaded = await uploadImage(file);
      if (target === "main") {
        updateField("image_url", uploaded.url);
      } else {
        const next = [...splitList(form.image_urls), uploaded.url];
        updateField("image_urls", next.join("\n"));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    }
  }

  if (isLoading) {
    return <section className="page-stack">加载中</section>;
  }

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h1>{title}</h1>
          <p>{parsedPayload ? "JSON 字段有效" : "JSON 字段无效"}</p>
        </div>
        <Link className="secondary-link" to="/">
          返回列表
        </Link>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {notice ? <p className="notice-text">{notice}</p> : null}

      <form className="product-form" onSubmit={submit}>
        <fieldset>
          <legend>基础信息</legend>
          <TextInput label="名称" value={form.name} onChange={(value) => updateField("name", value)} required />
          <TextInput label="类目" value={form.category} onChange={(value) => updateField("category", value)} />
          <TextInput label="品牌" value={form.brand} onChange={(value) => updateField("brand", value)} />
          <TextInput label="SKU" value={form.sku} onChange={(value) => updateField("sku", value)} />
          <TextInput label="平台" value={form.platform} onChange={(value) => updateField("platform", value)} />
          <TextInput label="商品链接" value={form.product_url} onChange={(value) => updateField("product_url", value)} />
        </fieldset>

        <fieldset>
          <legend>价格库存</legend>
          <TextInput label="价格" value={form.price} onChange={(value) => updateField("price", value)} inputMode="decimal" />
          <TextInput
            label="原价"
            value={form.original_price}
            onChange={(value) => updateField("original_price", value)}
            inputMode="decimal"
          />
          <TextInput label="库存" value={form.stock} onChange={(value) => updateField("stock", value)} inputMode="numeric" />
          <SelectInput label="库存状态" value={form.stock_status} onChange={(value) => updateField("stock_status", value)} />
          <TextInput label="评分" value={form.rating} onChange={(value) => updateField("rating", value)} inputMode="decimal" />
          <TextInput label="销量" value={form.sales} onChange={(value) => updateField("sales", value)} inputMode="numeric" />
        </fieldset>

        <fieldset>
          <legend>图片</legend>
          <TextInput label="主图 URL" value={form.image_url} onChange={(value) => updateField("image_url", value)} />
          <UploadControl label="上传为主图" onUpload={(file) => handleUpload(file, "main")} />
          <TextArea label="图库 URL" value={form.image_urls} onChange={(value) => updateField("image_urls", value)} />
          <UploadControl label="追加到图库" onUpload={(file) => handleUpload(file, "gallery")} />
        </fieldset>

        <fieldset>
          <legend>文案</legend>
          <TextArea label="描述" value={form.description} onChange={(value) => updateField("description", value)} />
          <TextArea label="评价摘要" value={form.review_summary} onChange={(value) => updateField("review_summary", value)} />
          <TextArea label="标签" value={form.tags} onChange={(value) => updateField("tags", value)} />
          <TextArea label="适用场景" value={form.suitable_scene} onChange={(value) => updateField("suitable_scene", value)} />
        </fieldset>

        <fieldset className="wide-fieldset">
          <legend>高级字段</legend>
          <TextArea label="规格 JSON" value={form.specs} onChange={(value) => updateField("specs", value)} rows={10} />
          <TextArea
            label="反馈指标 JSON"
            value={form.feedback_metrics}
            onChange={(value) => updateField("feedback_metrics", value)}
            rows={10}
          />
        </fieldset>

        <div className="form-actions">
          <button type="submit" disabled={isSaving || !parsedPayload}>
            {isSaving ? "保存中" : "保存"}
          </button>
          {canDelete ? (
            <button type="button" className="danger-button" onClick={remove}>
              下架
            </button>
          ) : null}
        </div>
      </form>
    </section>
  );
}

function TextInput({
  label,
  value,
  onChange,
  required,
  inputMode
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  inputMode?: "decimal" | "numeric";
}) {
  return (
    <label>
      {label}
      <input value={value} onChange={(event) => onChange(event.target.value)} required={required} inputMode={inputMode} />
    </label>
  );
}

function SelectInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">自动</option>
        <option value="in_stock">in_stock</option>
        <option value="low_stock">low_stock</option>
        <option value="out_of_stock">out_of_stock</option>
        <option value="discontinued">discontinued</option>
      </select>
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
  rows = 4
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
}) {
  return (
    <label>
      {label}
      <textarea value={value} rows={rows} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function UploadControl({ label, onUpload }: { label: string; onUpload: (file: File) => void }) {
  return (
    <label className="file-control">
      {label}
      <input
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onUpload(file);
          event.currentTarget.value = "";
        }}
      />
    </label>
  );
}

function productToForm(product: Product): FormState {
  return {
    name: product.name ?? "",
    category: product.category ?? "",
    brand: product.brand ?? "",
    sku: product.sku ?? "",
    price: valueToString(product.price),
    original_price: valueToString(product.original_price),
    stock: valueToString(product.stock),
    stock_status: product.stock_status ?? "",
    platform: product.platform ?? "",
    product_url: product.product_url ?? "",
    image_url: product.image_url ?? "",
    image_urls: (product.image_urls ?? []).join("\n"),
    rating: valueToString(product.rating),
    sales: valueToString(product.sales),
    description: product.description ?? "",
    review_summary: product.review_summary ?? "",
    tags: (product.tags ?? []).join("\n"),
    suitable_scene: (product.suitable_scene ?? []).join("\n"),
    specs: JSON.stringify(product.specs ?? {}, null, 2),
    feedback_metrics: JSON.stringify(product.feedback_metrics ?? {}, null, 2)
  };
}

function formToPayload(form: FormState): ProductPayload {
  return {
    name: form.name.trim(),
    category: emptyToNull(form.category),
    brand: emptyToNull(form.brand),
    sku: emptyToNull(form.sku),
    price: numberOrNull(form.price),
    original_price: numberOrNull(form.original_price),
    stock: integerOrNull(form.stock),
    stock_status: emptyToNull(form.stock_status),
    platform: emptyToNull(form.platform),
    product_url: emptyToNull(form.product_url),
    image_url: emptyToNull(form.image_url),
    image_urls: splitList(form.image_urls),
    rating: numberOrNull(form.rating),
    sales: integerOrNull(form.sales),
    description: emptyToNull(form.description),
    review_summary: emptyToNull(form.review_summary),
    tags: splitList(form.tags),
    suitable_scene: splitList(form.suitable_scene),
    specs: parseJson(form.specs),
    feedback_metrics: parseJsonObject(form.feedback_metrics)
  };
}

function splitList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseJson(value: string): Record<string, unknown> | unknown[] | null {
  const trimmed = value.trim();
  return trimmed ? (JSON.parse(trimmed) as Record<string, unknown> | unknown[]) : null;
}

function parseJsonObject(value: string): Record<string, unknown> {
  const parsed = parseJson(value);
  if (parsed === null) return {};
  if (Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("反馈指标必须是 JSON 对象");
  }
  return parsed as Record<string, unknown>;
}

function emptyToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function numberOrNull(value: string): number | null {
  const trimmed = value.trim();
  return trimmed ? Number(trimmed) : null;
}

function integerOrNull(value: string): number | null {
  const number = numberOrNull(value);
  return number === null ? null : Math.trunc(number);
}

function valueToString(value: number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

function formatMoney(value: number | null | undefined): string {
  return value === null || value === undefined ? "-" : `¥${value.toFixed(2)}`;
}
