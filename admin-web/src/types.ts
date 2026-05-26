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
