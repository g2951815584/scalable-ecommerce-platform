// Wire contracts mirroring the currently-implemented backend endpoints.
// Kept local to the storefront so page code stays type-safe against the real API.

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
}

export interface UserProfile {
  user_id: string;
  email: string | null;
  phone: string | null;
  nickname: string;
  status: string;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  can_place_order: boolean;
  roles: string[];
  avatar_url: string | null;
  gender: string;
  birthday: string | null;
  bio: string | null;
  locale: string;
  registered_at: string | null;
  last_login_at: string | null;
  has_password: boolean;
}

export interface LoginResult extends AuthTokens {
  user: UserProfile;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  depth: number;
  icon_url: string | null;
  product_count: number;
  children: Category[];
}

export interface CategoryTree {
  items: Category[];
  total: number;
  max_depth: number;
}

export interface OffsetPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ProductSummary {
  id: string;
  title: string;
  subtitle: string | null;
  brand: string | null;
  main_image_url: string | null;
  category_id: string;
  min_price_cents: number | null;
  max_price_cents: number | null;
  currency: string;
  sales_count: number;
  rating_avg: number;
  review_count: number;
  published_at: string | null;
}

export interface ProductList {
  items: ProductSummary[];
  pagination: OffsetPagination;
}

export interface Sku {
  id: string;
  sku_code: string;
  spec_text: string;
  price_cents: number;
  original_price_cents: number | null;
  currency: string;
  image_url: string | null;
  status: string;
  available: number;
  is_sellable: boolean;
}

export interface ProductDetail {
  id: string;
  title: string;
  subtitle: string | null;
  brand: string | null;
  category_id: string;
  status: string;
  description: string | null;
  main_image_url: string | null;
  price: {
    min_price_cents: number | null;
    max_price_cents: number | null;
    currency: string;
  };
  skus: Sku[];
  rating_avg: number;
  review_count: number;
  sales_count: number;
  published_at: string | null;
}

export interface CartItem {
  item_id: string;
  sku_id: number;
  quantity: number;
  is_selected: boolean;
  title: string;
  spec: string;
  image: string;
  price: number;
  added_at: number;
}

export interface CartSummary {
  item_count: number;
  total_quantity: number;
  selected_item_count: number;
  selected_quantity: number;
  selected_amount_cents: number;
}

export interface Cart {
  items: CartItem[];
  summary: CartSummary;
}

export interface Address {
  address_id: string;
  user_id: string;
  receiver_name: string;
  receiver_phone: string;
  province: string;
  city: string;
  district: string;
  detail_address: string;
  postal_code: string | null;
  region_code: string | null;
  is_default: boolean;
  version: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface AddressList {
  items: Address[];
  total: number;
  max_addresses: number;
}

export interface OrderItem {
  item_no: number;
  spu_id: string;
  sku_id: string;
  spu_title: string;
  sku_spec_text: string;
  unit_price_cents: number;
  quantity: number;
  item_amount_cents: number;
}

export interface OrderAmount {
  goods_amount_cents: number;
  shipping_fee_cents: number;
  discount_amount_cents: number;
  adjust_amount_cents: number;
  payable_amount_cents: number;
  paid_amount_cents: number;
  refunded_amount_cents: number;
}

export interface OrderDetail {
  order_no: string;
  status: string;
  status_text: string;
  currency: string;
  created_at: string;
  expires_at: string;
  paid_at: string | null;
  amount: OrderAmount;
  items: OrderItem[];
}

export interface OrderSummary {
  order_no: string;
  status: string;
  status_text: string;
  payable_amount_cents: number;
  currency: string;
  item_kind_count: number;
  total_quantity: number;
  created_at: string;
  expires_at: string;
}

export interface OrderList {
  items: OrderSummary[];
  pagination: OffsetPagination;
}

export interface Payment {
  payment_no: string;
  order_no: string;
  user_id: string;
  channel: string;
  status: string;
  amount_cents: number;
  currency: string;
  refunded_amount_cents: number;
  refundable_amount_cents: number;
  third_party_payment_id: string | null;
  paid_at: string | null;
}