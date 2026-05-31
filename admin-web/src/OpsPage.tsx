import { Children, useEffect, useMemo, useState } from "react";
import { getOpsSummary } from "./api";
import type { FeedbackAudit, OpsSummary, OrderAudit, ReviewAudit } from "./types";

type LoadState = {
  data: OpsSummary | null;
  error: string;
  isLoading: boolean;
};

export function OpsPage() {
  const [state, setState] = useState<LoadState>({ data: null, error: "", isLoading: true });

  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, isLoading: true, error: "" }));
    getOpsSummary()
      .then((data) => {
        if (active) setState({ data, error: "", isLoading: false });
      })
      .catch((error) => {
        if (active) setState({ data: null, error: error instanceof Error ? error.message : "加载失败", isLoading: false });
      });
    return () => {
      active = false;
    };
  }, []);

  const checks = useMemo(() => Object.entries(state.data?.readiness.checks ?? {}), [state.data]);

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <h1>Beta 运维面板</h1>
          <p>发布可见性、索引健康、token 权限和购买反馈审计</p>
        </div>
        <button type="button" onClick={() => window.location.reload()}>
          刷新
        </button>
      </div>

      {state.error ? (
        <p className="error-text" role="alert">
          {state.error}
        </p>
      ) : null}
      {state.isLoading ? (
        <p className="notice-text" role="status">
          加载运维状态中
        </p>
      ) : null}
      {state.data ? (
        <>
          <MetricGrid summary={state.data} />
          <ReadinessPanel status={state.data.readiness.status} checks={checks} />
          <IndexPanel health={state.data.index_health} operations={state.data.operations} />
          <TokenPanel tokens={state.data.token_guidance} />
          <OrderAuditTable orders={state.data.recent_orders} />
          <FeedbackAuditTable items={state.data.pending_feedback} />
          <ReviewAuditTable reviews={state.data.recent_reviews} />
        </>
      ) : null}
    </section>
  );
}

function MetricGrid({ summary }: { summary: OpsSummary }) {
  return (
    <div className="metric-grid">
      <MetricCard label="Readiness" value={summary.readiness.status} tone={summary.readiness.status === "ready" ? "ok" : "warn"} />
      <MetricCard label="索引状态" value={String(summary.index_health.status ?? "unknown")} />
      <MetricCard label="Active 商品" value={String(summary.catalog.active_products ?? "-")} />
      <MetricCard label="待评价" value={String(summary.pending_feedback.length)} />
    </div>
  );
}

function MetricCard({ label, value, tone }: { label: string; value: string; tone?: "ok" | "warn" }) {
  return (
    <article className={`metric-card ${tone ?? ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ReadinessPanel({ status, checks }: { status: string; checks: [string, Record<string, unknown>][] }) {
  return (
    <section className="ops-card">
      <div className="section-heading">
        <h2>Readiness 状态</h2>
        <span className={`status-badge ${status === "ready" ? "in_stock" : "low_stock"}`}>{status}</span>
      </div>
      <div className="check-grid">
        {checks.map(([name, check]) => (
          <div key={name} className="check-item">
            <strong>{name}</strong>
            <span>{String(check.status ?? "unknown")}</span>
            {check.detail ? <small>{String(check.detail)}</small> : null}
          </div>
        ))}
      </div>
    </section>
  );
}

function IndexPanel({ health, operations }: { health: Record<string, unknown>; operations: OpsSummary["operations"] }) {
  return (
    <section className="ops-card">
      <div className="section-heading">
        <h2>商品索引健康</h2>
        <span className="status-badge">{String(health.status ?? "unknown")}</span>
      </div>
      <div className="key-value-grid">
        <KeyValue label="collection count" value={health.collection_count} />
        <KeyValue label="active products" value={health.active_product_count} />
        <KeyValue label="missing ids" value={formatList(health.missing_product_ids)} />
        <KeyValue label="stale ids" value={formatList(health.stale_product_ids)} />
      </div>
      <div className="operation-list">
        {operations.length ? operations.map((operation) => (
          <article key={operation.name}>
            <strong>{operation.name}</strong>
            <span>{operation.status}</span>
            <code>{operation.command}</code>
          </article>
        )) : <p className="empty-state">暂无导入或索引操作说明。</p>}
      </div>
    </section>
  );
}

function TokenPanel({ tokens }: { tokens: OpsSummary["token_guidance"] }) {
  return (
    <section className="ops-card">
      <div className="section-heading">
        <h2>Token 权限提示</h2>
        <span>不展示 token 明文</span>
      </div>
      <div className="token-grid">
        {tokens.length ? tokens.map((token) => <TokenCard key={token.subject} subject={token.subject} scopes={token.scopes} />) : <p>当前未配置 beta token。</p>}
      </div>
    </section>
  );
}

function TokenCard({ subject, scopes }: { subject: string; scopes: string[] }) {
  const hint = subject.toLowerCase().includes("smoke") ? "Smoke token：用于发布后验证订单、待评价和评价提交闭环。" : "Beta token：按用户或渠道分配，便于排查和审计。";
  return (
    <article className="token-card">
      <strong>{subject}</strong>
      <span>{hint}</span>
      <small>{scopes.join(", ") || "未声明 scopes"}</small>
    </article>
  );
}

function OrderAuditTable({ orders }: { orders: OrderAudit[] }) {
  return (
    <AuditTable title="最近订单与外部购买" empty="暂无订单" columns={["ID", "用户", "支付", "履约", "外部来源", "创建时间"]}>
      {orders.map((order) => (
        <tr key={order.id}>
          <td>{order.id}</td>
          <td>{order.user_ref}</td>
          <td>{order.payment_status}</td>
          <td>{order.fulfillment_status}</td>
          <td>{[order.external_platform, order.external_order_ref].filter(Boolean).join(" / ") || "-"}</td>
          <td>{formatDate(order.created_at)}</td>
        </tr>
      ))}
    </AuditTable>
  );
}

function FeedbackAuditTable({ items }: { items: FeedbackAudit[] }) {
  return (
    <AuditTable title="待评价提示" empty="暂无待评价" columns={["订单", "用户", "商品", "到期时间"]}>
      {items.map((item) => (
        <tr key={item.order_item_id}>
          <td>#{item.order_id} / item {item.order_item_id}</td>
          <td>{item.user_ref}</td>
          <td>{item.product_name}</td>
          <td>{formatDate(item.feedback_due_at)}</td>
        </tr>
      ))}
    </AuditTable>
  );
}

function ReviewAuditTable({ reviews }: { reviews: ReviewAudit[] }) {
  return (
    <AuditTable title="评价提交审计" empty="暂无评价" columns={["ID", "用户", "商品", "评分", "证据", "创建时间"]}>
      {reviews.map((review) => (
        <tr key={review.id}>
          <td>{review.id}</td>
          <td>{review.user_ref || "-"}</td>
          <td>{review.product_id ?? "-"}</td>
          <td>{review.rating ?? "-"}</td>
          <td>{review.purchase_evidence || review.status || "-"}</td>
          <td>{formatDate(review.created_at)}</td>
        </tr>
      ))}
    </AuditTable>
  );
}

function AuditTable({ title, empty, columns, children }: { title: string; empty: string; columns: string[]; children: React.ReactNode }) {
  const rows = Children.count(children);
  return (
    <section className="ops-card">
      <h2>{title}</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
          </thead>
          <tbody>{rows ? children : <tr><td colSpan={columns.length}>{empty}</td></tr>}</tbody>
        </table>
      </div>
    </section>
  );
}

function KeyValue({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value === undefined || value === null ? "-" : String(value)}</strong>
    </div>
  );
}

function formatList(value: unknown): string {
  return Array.isArray(value) && value.length ? value.join(", ") : "-";
}

function formatDate(value?: string | null): string {
  return value ? new Date(value).toLocaleString() : "-";
}
