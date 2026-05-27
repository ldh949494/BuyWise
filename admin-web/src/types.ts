export type Product = {
  id: number;
  name: string;
  category?: string | null;
  brand?: string | null;
  sku?: string | null;
  price?: number | null;
  original_price?: number | null;
  platform?: string | null;
  product_url?: string | null;
  image_url?: string | null;
  image_urls: string[];
  rating?: number | null;
  sales?: number | null;
  description?: string | null;
  specs?: Record<string, unknown> | unknown[] | null;
  tags: string[];
  suitable_scene: string[];
  stock?: number | null;
  stock_status?: string | null;
  review_summary?: string | null;
  feedback_metrics: Record<string, unknown>;
  created_at?: string | null;
};

export type ProductListResponse = {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminProductWriteResponse = {
  product: Product;
  index_sync_status: string;
  index_sync_note: string;
};

export type ProductPayload = Omit<Product, "id" | "created_at">;

export type OpsSummary = {
  readiness: {
    status: string;
    service: string;
    checks: Record<string, Record<string, unknown>>;
  };
  index_health: Record<string, unknown>;
  catalog: Record<string, unknown>;
  token_guidance: TokenGuidance[];
  operations: OperationStatus[];
  recent_orders: OrderAudit[];
  pending_feedback: FeedbackAudit[];
  recent_reviews: ReviewAudit[];
};

export type TokenGuidance = {
  subject: string;
  scopes: string[];
};

export type OperationStatus = {
  name: string;
  status: string;
  command: string;
};

export type OrderAudit = {
  id: number;
  user_ref: string;
  payment_status: string;
  fulfillment_status: string;
  external_platform?: string | null;
  external_order_ref?: string | null;
  created_at: string;
};

export type FeedbackAudit = {
  order_id: number;
  order_item_id: number;
  user_ref: string;
  product_id: number;
  product_name: string;
  feedback_due_at?: string | null;
};

export type ReviewAudit = {
  id: number;
  product_id?: number | null;
  order_item_id?: number | null;
  user_ref?: string | null;
  rating?: number | null;
  purchase_evidence?: string | null;
  status?: string | null;
  created_at?: string | null;
};
