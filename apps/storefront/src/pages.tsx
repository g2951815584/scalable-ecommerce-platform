import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "./api";
import { applyLogin, useAuthStore } from "./session";
import { EmptyState, PlaceholderPage, PriceTag } from "./components";
import type {
  Address,
  AddressList,
  Cart,
  Category,
  CategoryTree,
  LoginResult,
  OrderDetail,
  OrderList,
  Payment,
  ProductDetail,
  ProductList,
  ProductSummary,
  Sku,
  UserProfile,
} from "./types";

function formatYuan(cents: number | null | undefined): string {
  if (cents === null || cents === undefined) return "—";
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY" }).format(cents / 100);
}

function errorText(error: unknown): string {
  const candidate = error as { message?: string };
  if (candidate?.message) return candidate.message;
  return "请求失败，请稍后重试";
}

async function block<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    throw new Error(errorText(error));
  }
}

function ProductArt({ url, seed }: { url: string | null; seed: string }) {
  const palette = Math.abs(seed.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0)) % 4;
  if (url) return <img className="product-image" src={url} alt={seed} />;
  return <div className={`product-art art-${palette + 1}`} />;
}

function ProductCard({ product }: { product: ProductSummary }) {
  const price =
    product.min_price_cents != null &&
    product.max_price_cents != null &&
    product.min_price_cents !== product.max_price_cents
      ? `${formatYuan(product.min_price_cents)} 起`
      : formatYuan(product.min_price_cents ?? product.max_price_cents);
  return (
    <Link className="product-card" to={`/products/${product.id}`}>
      <ProductArt url={product.main_image_url} seed={product.title} />
      <p>{product.title}</p>
      <span className="muted">{product.brand || "·"}</span>
      <PriceTag cents={product.min_price_cents ?? 0} />
      <span className="rating">{product.rating_avg > 0 ? `★ ${product.rating_avg}` : price}</span>
    </Link>
  );
}

function ProductGrid({ products }: { products: ProductSummary[] }) {
  if (products.length === 0) {
    return <EmptyState title="暂无商品"><Link className="button" to="/">回到首页</Link></EmptyState>;
  }
  return (
    <div className="product-grid">
      {products.map((product) => <ProductCard key={product.id} product={product} />)}
    </div>
  );
}

/* Home */

export function HomePage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const [tree, list] = await Promise.all([
          api.get<CategoryTree>("/categories/tree"),
          api.get<ProductList>("/products", { params: { page: 1, page_size: 8 } }),
        ]);
        setCategories(tree.items);
        setProducts(list.items);
      } catch (err) {
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section className="home-page">
      <div className="hero">
        <p className="eyebrow">SPRING / 2026</p>
        <h1>把喜欢的生活，<br />放进购物车。</h1>
        <p>分类、搜索、购物车、结算到支付，买家商城端已接入真实后端接口。</p>
        <div className="hero-links">
          <Link className="button" to="/categories/all">开始逛逛</Link>
          {categories.slice(0, 3).map((category) => (
            <Link key={category.id} className="chip-link" to={`/categories/${category.id}`}>
              {category.name}
            </Link>
          ))}
        </div>
      </div>

      <div className="section-heading">
        <div>
          <p className="eyebrow">CATALOG</p>
          <h2>热销商品</h2>
        </div>
        <Link to="/search">查看全部 →</Link>
      </div>

      {loading && <div className="muted">加载中…</div>}
      {error && <div className="form-message">{error}</div>}
      {!loading && !error && <ProductGrid products={products} />}
    </section>
  );
}
/* Auth */

export function AuthPage({ mode }: { mode: "login" | "register" | "forgot" }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [account, setAccount] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const title = mode === "login" ? "欢迎回来" : mode === "register" ? "创建商城账户" : "找回密码";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    try {
      if (mode === "login") {
        const result = await block(() => api.post<LoginResult>("/auth/login", { account, password }));
        applyLogin(result);
        navigate(params.get("redirect") || "/", { replace: true });
      } else if (mode === "register") {
        await block(() => api.post("/auth/register", { account, password, nickname: account }));
        navigate("/login", { replace: true });
      } else {
        await block(() =>
          api.post("/auth/password/forgot", { account, account_type: account.includes("@") ? "EMAIL" : "PHONE" }),
        );
        setMessage("若该账号存在，重置验证码已发送，请稍后按提示重置。");
      }
    } catch (err) {
      setMessage(errorText(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-card">
        <p className="eyebrow">ACCOUNT</p>
        <h1>{title}</h1>
        <p className="muted">{mode === "forgot" ? "输入账号获取重置验证码" : "使用邮箱或手机号继续"}</p>
        <form onSubmit={submit}>
          <label>
            账号
            <input required value={account} onChange={(event) => setAccount(event.target.value)} placeholder="name@example.com" />
          </label>
          {mode !== "forgot" && (
            <label>
              密码
              <input
                required
                minLength={mode === "register" ? 8 : 6}
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "register" ? "至少 8 位，含字母与数字" : "请输入密码"}
              />
            </label>
          )}
          <button className="button" type="submit" disabled={submitting}>
            {submitting ? "提交中…" : mode === "login" ? "登录" : mode === "register" ? "注册" : "发送验证码"}
          </button>
        </form>
        {message && <p className="form-message">{message}</p>}
        <div className="auth-links">
          {mode !== "login" && <Link to="/login">已有账户？登录</Link>}
          {mode === "login" && (
            <>
              <Link to="/register">创建账户</Link>
              <Link to="/forgot-password">忘记密码</Link>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
/* Listing / Search */

export function ListingPage({ search = false }: { search?: boolean }) {
  const { id } = useParams();
  const [params] = useSearchParams();
  const keyword = params.get("q") ?? "";
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const list = await api.get<ProductList>(search ? "/products/search" : "/products", {
          params: search
            ? { keyword, page: 1, page_size: 50 }
            : { category_id: id === "all" ? undefined : id, page: 1, page_size: 50 },
        });
        setProducts(list.items);
        setTotal(list.pagination.total);
      } catch (err) {
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    })();
  }, [id, keyword, search]);

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{search ? "SEARCH" : "CATALOG"}</p>
          <h1>{search ? (keyword ? `搜索结果：${keyword}` : "搜索") : "商品分类"}</h1>
        </div>
        <span className="muted">共 {total} 件商品</span>
      </div>
      {loading && <div className="muted">加载中…</div>}
      {error && <div className="form-message">{error}</div>}
      {!loading && !error && <ProductGrid products={products} />}
    </section>
  );
}
/* Product detail */

export function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [sku, setSku] = useState<Sku | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      setSku(null);
      try {
        const detail = await api.get<ProductDetail>(`/products/${id}`);
        setProduct(detail);
        const first = detail.skus.find((item) => item.is_sellable) ?? detail.skus[0];
        setSku(first ?? null);
      } catch (err) {
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  async function addToCart(buyNow: boolean) {
    if (!sku) return;
    setNotice("");
    try {
      await api.post("/cart/items", { sku_id: sku.id, quantity });
      if (buyNow) navigate("/cart");
      else {
        setNotice("已加入购物车");
        window.setTimeout(() => setNotice(""), 2000);
      }
    } catch (err) {
      setNotice(errorText(err));
    }
  }

  if (loading) return <div className="muted">加载中…</div>;
  if (error || !product) {
    return <EmptyState title={error || "商品不存在"}><Link className="button" to="/">回到首页</Link></EmptyState>;
  }

  return (
    <section className="detail-page">
      <div className="detail-media"><ProductArt url={product.main_image_url} seed={product.title} /></div>
      <div className="detail-copy">
        <p className="eyebrow">PRODUCT / SKU MATRIX</p>
        <h1>{product.title}</h1>
        <p className="muted">{product.subtitle || product.brand || "·"}</p>
        <PriceTag cents={sku?.price_cents ?? product.price.min_price_cents ?? 0} />
        {sku && <p className="muted">库存 {sku.available} 件 · {sku.spec_text}</p>}
        <div className="option-row">
          <span>规格</span>
          {product.skus.map((item) => (
            <button
              key={item.id}
              className={`option ${sku?.id === item.id ? "selected" : ""} ${!item.is_sellable ? "sold-out" : ""}`}
              disabled={!item.is_sellable}
              onClick={() => setSku(item)}
            >
              {item.spec_text}
            </button>
          ))}
        </div>
        <div className="option-row">
          <span>数量</span>
          <button className="quantity" onClick={() => setQuantity((q) => Math.max(1, q - 1))}>−</button>
          <span>{quantity}</span>
          <button className="quantity" onClick={() => setQuantity((q) => Math.min(sku?.available ?? 99, q + 1))}>＋</button>
        </div>
        {notice && <p className="form-message">{notice}</p>}
        <div className="detail-actions">
          <button className="button secondary" disabled={!sku} onClick={() => addToCart(false)}>加入购物车</button>
          <button className="button" disabled={!sku} onClick={() => addToCart(true)}>立即购买</button>
        </div>
      </div>
    </section>
  );
}
/* Cart */

export function CartPage() {
  const navigate = useNavigate();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setCart(await api.get<Cart>("/cart"));
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function toggleSelect(itemId: string, selected: boolean) {
    try {
      await api.post("/cart/items/select", { item_ids: [itemId], selected });
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function setQty(itemId: string, quantity: number) {
    try {
      if (quantity <= 0) {
        await api.delete(`/cart/items/${itemId}`);
      } else {
        await api.put(`/cart/items/${itemId}`, { quantity });
      }
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function remove(itemId: string) {
    try {
      await api.delete(`/cart/items/${itemId}`);
      await load();
    } catch (err) {
      setError(errorText(err));
    }
  }

  if (loading) return <div className="muted">加载中…</div>;
  if (error || !cart) {
    return <EmptyState title={error || "购物车为空"}><Link className="button" to="/">去逛逛</Link></EmptyState>;
  }

  const selectedItems = cart.items.filter((item) => item.is_selected);

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">CART</p>
          <h1>购物车</h1>
        </div>
        <span className="muted">价格与库存将在结算前校验</span>
      </div>
      <div className="cart-layout">
        <div className="cart-list">
          {cart.items.length === 0 && <EmptyState title="购物车是空的" />}
          {cart.items.map((item) => (
            <article className={`cart-row ${item.is_selected ? "" : "dimmed"}`} key={item.item_id}>
              <input
                type="checkbox"
                checked={item.is_selected}
                onChange={(event) => toggleSelect(item.item_id, event.target.checked)}
              />
              <ProductArt url={item.image || null} seed={item.title} />
              <div>
                <strong>{item.title}</strong>
                <p className="muted">{item.spec || "默认规格"}</p>
                <div className="qty-row">
                  <button className="quantity" onClick={() => setQty(item.item_id, item.quantity - 1)}>−</button>
                  <span>{item.quantity}</span>
                  <button className="quantity" onClick={() => setQty(item.item_id, item.quantity + 1)}>＋</button>
                </div>
              </div>
              <div className="cart-row-right">
                <PriceTag cents={item.price * item.quantity} />
                <button className="text-button" onClick={() => remove(item.item_id)}>删除</button>
              </div>
            </article>
          ))}
        </div>
        <aside className="summary-card">
          <p className="muted">已选 {cart.summary.selected_item_count} 件商品</p>
          <div className="summary-total">
            <span>合计</span>
            <PriceTag cents={cart.summary.selected_amount_cents} />
          </div>
          <button
            className="button full"
            disabled={selectedItems.length === 0}
            onClick={() => navigate("/checkout")}
          >
            去结算
          </button>
        </aside>
      </div>
    </section>
  );
}
/* Account (profile + addresses) */

export function AccountPage({ kind }: { kind: "profile" | "addresses" }) {
  return kind === "profile" ? <ProfileManager /> : <AddressManager />;
}

function ProfileManager() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [nickname, setNickname] = useState("");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get<UserProfile>("/users/me");
        setProfile(data);
        setNickname(data.nickname ?? "");
        setBio(data.bio ?? "");
      } catch {
        /* guarded below */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    try {
      const updated = await api.patch<UserProfile>("/users/me", { nickname, bio });
      setProfile(updated);
      useAuthStore.getState().setSession({
        access_token: useAuthStore.getState().access_token ?? "",
        refresh_token: useAuthStore.getState().refresh_token ?? "",
        user_id: updated.user_id,
        nickname: updated.nickname,
        roles: useAuthStore.getState().roles,
      });
      setMessage("已保存");
    } catch (err) {
      setMessage(errorText(err));
    }
  }

  if (loading) return <div className="muted">加载中…</div>;
  if (!profile) return <EmptyState title="无法加载资料"><Link className="button" to="/">回到首页</Link></EmptyState>;

  return (
    <section className="page-card">
      <p className="eyebrow">ACCOUNT</p>
      <h1>个人资料</h1>
      <form onSubmit={save}>
        <label>昵称<input value={nickname} onChange={(event) => setNickname(event.target.value)} /></label>
        <label>简介<textarea value={bio} onChange={(event) => setBio(event.target.value)} rows={3} /></label>
        <p className="muted">账号：{profile.email || profile.phone || "—"}（{profile.is_email_verified || profile.is_phone_verified ? "已验证" : "未验证"}）</p>
        <button className="button" type="submit">保存</button>
      </form>
      {message && <p className="form-message">{message}</p>}
    </section>
  );
}

function AddressManager() {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await api.get<AddressList>("/users/me/addresses");
      setAddresses(data.items);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function addDefault() {
    setMessage("");
    try {
      await api.post("/users/me/addresses", {
        receiver_name: "收货人",
        receiver_phone: "+8613800138000",
        province: "广东省",
        city: "深圳市",
        district: "南山区",
        detail_address: "科技园南路 1 号 A 座 1801",
      });
      await load();
    } catch (err) {
      setMessage(errorText(err));
    }
  }

  async function setDefault(id: string) {
    try {
      await api.put(`/users/me/addresses/${id}/default`);
      await load();
    } catch (err) {
      setMessage(errorText(err));
    }
  }

  async function remove(id: string) {
    try {
      await api.delete(`/users/me/addresses/${id}`);
      await load();
    } catch (err) {
      setMessage(errorText(err));
    }
  }

  if (loading) return <div className="muted">加载中…</div>;

  return (
    <section className="page-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ACCOUNT</p>
          <h1>收货地址</h1>
        </div>
        <button className="button" onClick={addDefault}>新增地址（示例）</button>
      </div>
      {message && <p className="form-message">{message}</p>}
      {addresses.length === 0 && <EmptyState title="暂无收货地址" />}
      <div className="address-list">
        {addresses.map((address) => (
          <article className="address-card" key={address.address_id}>
            <div>
              <strong>{address.receiver_name}</strong>
              <span className="tag">{address.is_default ? "默认" : ""}</span>
              <p className="muted">
                {address.receiver_phone} · {address.province}{address.city}{address.district}{address.detail_address}
              </p>
            </div>
            <div className="address-actions">
              {!address.is_default && <button className="text-button" onClick={() => setDefault(address.address_id)}>设为默认</button>}
              <button className="text-button" onClick={() => remove(address.address_id)}>删除</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
/* Checkout */

export function CheckoutPage() {
  const navigate = useNavigate();
  const [cart, setCart] = useState<Cart | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [addressId, setAddressId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [cartData, addressData] = await Promise.all([
          api.get<Cart>("/cart"),
          api.get<AddressList>("/users/me/addresses"),
        ]);
        setCart(cartData);
        setAddresses(addressData.items);
        const primary = addressData.items.find((item) => item.is_default) ?? addressData.items[0];
        setAddressId(primary?.address_id ?? "");
      } catch (err) {
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function submit() {
    if (!cart || !addressId) return;
    setSubmitting(true);
    setError("");
    try {
      const items = cart.items
        .filter((item) => item.is_selected)
        .map((item) => ({
          sku_id: item.sku_id,
          quantity: item.quantity,
          unit_price_cents: item.price,
          title: item.title,
          spec_name: item.spec,
          image_url: item.image,
        }));
      const address = addresses.find((item) => item.address_id === addressId);
      if (!address) throw new Error("请选择收货地址");
      const order = await api.post<{ order_no: string }>("/orders", {
        items,
        address: {
          address_id: address.address_id,
          receiver_name: address.receiver_name,
          receiver_phone: address.receiver_phone,
          province: address.province,
          city: address.city,
          district: address.district,
          detail_address: address.detail_address,
          address_text: `${address.province}${address.city}${address.district}${address.detail_address}`,
        },
      });
      navigate(`/checkout/pay/${order.order_no}`);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="muted">加载中…</div>;
  if (error) return <EmptyState title={error}><Link className="button" to="/cart">返回购物车</Link></EmptyState>;
  if (!cart) return null;

  const selectedItems = cart.items.filter((item) => item.is_selected);

  return (
    <section className="checkout-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">CHECKOUT</p>
          <h1>确认订单</h1>
        </div>
      </div>

      <div className="checkout-layout">
        <div className="checkout-main">
          <h2>收货地址</h2>
          {addresses.length === 0 ? (
            <p className="muted">暂无收货地址，请先到账号页添加。</p>
          ) : (
            <div className="address-picker">
              {addresses.map((address) => (
                <label className={`address-option ${addressId === address.address_id ? "selected" : ""}`} key={address.address_id}>
                  <input type="radio" name="address" checked={addressId === address.address_id} onChange={() => setAddressId(address.address_id)} />
                  <span>
                    <strong>{address.receiver_name}</strong> {address.receiver_phone}
                    <br />
                    <span className="muted">{address.province}{address.city}{address.district}{address.detail_address}</span>
                  </span>
                </label>
              ))}
            </div>
          )}

          <h2>商品清单</h2>
          <div className="checkout-items">
            {selectedItems.map((item) => (
              <div className="checkout-item" key={item.item_id}>
                <span>{item.title} · {item.spec} × {item.quantity}</span>
                <PriceTag cents={item.price * item.quantity} />
              </div>
            ))}
          </div>
        </div>

        <aside className="summary-card">
          <p className="muted">商品金额</p>
          <div className="summary-total">
            <span>合计</span>
            <PriceTag cents={cart.summary.selected_amount_cents} />
          </div>
          <button className="button full" disabled={submitting || selectedItems.length === 0 || !addressId} onClick={submit}>
            {submitting ? "提交中…" : "提交订单"}
          </button>
        </aside>
      </div>
    </section>
  );
}
/* Payment */

export function PayPage() {
  const { orderNo } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [channel, setChannel] = useState<"STRIPE" | "PAYPAL">("STRIPE");
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadOrder = useCallback(async () => {
    if (!orderNo) return;
    try {
      const data = await api.get<OrderDetail>(`/orders/${orderNo}`);
      setOrder(data);
      if (data.status === "PAID" || data.status === "SHIPPED" || data.status === "RECEIVED" || data.status === "COMPLETED") {
        navigate(`/checkout/result?status=success&order_no=${data.order_no}`, { replace: true });
      }
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(false);
    }
  }, [orderNo, navigate]);

  useEffect(() => {
    loadOrder();
  }, [loadOrder]);

  async function createPayment() {
    if (!order) return;
    setError("");
    try {
      const result = await api.post<Payment>("/payments", {
        order_no: order.order_no,
        channel,
        amount_cents: order.amount.payable_amount_cents,
      });
      setPayment(result);
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function simulatePaid() {
    if (!payment) return;
    setError("");
    try {
      await api.post(`/payments/${channel.toLowerCase()}/webhook`, {
        payment_no: payment.payment_no,
        third_party_payment_id: `mock_${Date.now()}`,
      });
      await loadOrder();
    } catch (err) {
      setError(errorText(err));
    }
  }

  if (loading) return <div className="muted">加载中…</div>;
  if (error || !order) return <EmptyState title={error || "订单不存在"}><Link className="button" to="/orders">返回订单</Link></EmptyState>;

  return (
    <section className="page-card">
      <p className="eyebrow">PAYMENT</p>
      <h1>支付订单</h1>
      <p className="muted">订单号：{order.order_no}</p>
      <p className="muted">应付金额：<PriceTag cents={order.amount.payable_amount_cents} /></p>

      <div className="option-row">
        <span>渠道</span>
        {(["STRIPE", "PAYPAL"] as const).map((item) => (
          <button key={item} className={`option ${channel === item ? "selected" : ""}`} onClick={() => setChannel(item)}>
            {item === "STRIPE" ? "Stripe" : "PayPal"}
          </button>
        ))}
      </div>

      {error && <p className="form-message">{error}</p>}

      {!payment ? (
        <button className="button" onClick={createPayment}>立即支付</button>
      ) : (
        <div className="payment-panel">
          <p className="muted">支付单已创建：{payment.payment_no}（模拟渠道）</p>
          <button className="button" onClick={simulatePaid}>模拟支付成功</button>
        </div>
      )}
    </section>
  );
}

/* Payment result */

export function ResultPage() {
  const [params] = useSearchParams();
  const success = params.get("status") === "success";
  const orderNo = params.get("order_no") ?? "";
  return (
    <section className="page-card">
      <p className="eyebrow">PAYMENT RESULT</p>
      <h1>{success ? "支付成功" : "支付未完成"}</h1>
      <p className="muted">
        {success ? `订单 ${orderNo || "—"} 已收到，感谢你的购买。` : "可以重试支付或稍后在订单列表确认状态。"}
      </p>
      <div className="detail-actions">
        <Link className="button" to={success ? "/orders" : `/checkout/pay/${orderNo}`}>
          {success ? "查看订单" : "重试支付"}
        </Link>
        <Link className="button secondary" to="/">继续购物</Link>
      </div>
    </section>
  );
}
/* Orders */

const ORDER_TABS = [
  { key: "", label: "全部" },
  { key: "PENDING_PAYMENT", label: "待支付" },
  { key: "PAID", label: "待发货" },
  { key: "SHIPPED", label: "待收货" },
  { key: "RECEIVED", label: "已收货" },
  { key: "COMPLETED", label: "已完成" },
  { key: "CANCELLED", label: "已取消" },
];

export function OrdersPage() {
  const [params, setSearchParams] = useSearchParams();
  const status = params.get("status") ?? "";
  const [list, setList] = useState<OrderList["items"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const data = await api.get<OrderList>("/orders", { params: { status: status || undefined, page: 1, page_size: 50 } });
        setList(data.items);
      } catch (err) {
        setError(errorText(err));
      } finally {
        setLoading(false);
      }
    })();
  }, [status]);

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">ORDERS</p>
          <h1>我的订单</h1>
        </div>
      </div>
      <div className="order-tabs">
        {ORDER_TABS.map((tab) => (
          <button
            key={tab.key}
            className={`filter-pill ${status === tab.key ? "selected" : ""}`}
            onClick={() => setSearchParams(tab.key ? { status: tab.key } : {})}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {loading && <div className="muted">加载中…</div>}
      {error && <div className="form-message">{error}</div>}
      {!loading && !error && list.length === 0 && <EmptyState title="暂无订单"><Link className="button" to="/">去逛逛</Link></EmptyState>}
      <div className="order-list">
        {list.map((order) => (
          <Link className="order-card" key={order.order_no} to={`/orders/${order.order_no}`}>
            <div>
              <strong>{order.order_no}</strong>
              <p className="muted">{new Date(order.created_at).toLocaleString()}</p>
            </div>
            <div className="order-meta">
              <Tag status={order.status}>{order.status_text}</Tag>
              <span className="muted">{order.item_kind_count} 种 · {order.total_quantity} 件</span>
            </div>
            <PriceTag cents={order.payable_amount_cents} />
          </Link>
        ))}
      </div>
    </section>
  );
}

function Tag({ status, children }: { status: string; children: React.ReactNode }) {
  const color = status === "PENDING_PAYMENT" ? "warn" : status === "PAID" || status === "SHIPPED" ? "info" : status === "COMPLETED" ? "ok" : "muted";
  return <span className={`tag tag-${color}`}>{children}</span>;
}
/* Order detail */

export function OrderDetailPage() {
  const { orderNo } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!orderNo) return;
    try {
      setOrder(await api.get<OrderDetail>(`/orders/${orderNo}`));
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(false);
    }
  }, [orderNo]);

  useEffect(() => {
    load();
  }, [load]);

  async function cancel() {
    if (!orderNo) return;
    setNotice("");
    try {
      await api.post(`/orders/${orderNo}/cancel`, { reason: "买家取消" });
      await load();
    } catch (err) {
      setNotice(errorText(err));
    }
  }

  async function confirmReceipt() {
    if (!orderNo) return;
    setNotice("");
    try {
      await api.post(`/orders/${orderNo}/confirm`);
      await load();
    } catch (err) {
      setNotice(errorText(err));
    }
  }

  if (loading) return <div className="muted">加载中…</div>;
  if (error || !order) return <EmptyState title={error || "订单不存在"}><Link className="button" to="/orders">返回订单列表</Link></EmptyState>;

  return (
    <section className="page-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ORDER DETAIL</p>
          <h1>{order.status_text}</h1>
        </div>
        <Tag status={order.status}>{order.order_no}</Tag>
      </div>
      <p className="muted">下单时间：{new Date(order.created_at).toLocaleString()}</p>
      {order.paid_at && <p className="muted">支付时间：{new Date(order.paid_at).toLocaleString()}</p>}

      <h2>商品明细</h2>
      <div className="checkout-items">
        {order.items.map((item) => (
          <div className="checkout-item" key={item.item_no}>
            <span>{item.spu_title} · {item.sku_spec_text} × {item.quantity}</span>
            <PriceTag cents={item.item_amount_cents} />
          </div>
        ))}
      </div>

      <h2>金额</h2>
      <div className="amount-grid">
        <span>商品总额</span><PriceTag cents={order.amount.goods_amount_cents} />
        <span>运费</span><PriceTag cents={order.amount.shipping_fee_cents} />
        <span className="total">应付</span><PriceTag cents={order.amount.payable_amount_cents} />
        {order.amount.paid_amount_cents > 0 && (<><span>实付</span><PriceTag cents={order.amount.paid_amount_cents} /></>)}
      </div>

      {notice && <p className="form-message">{notice}</p>}

      <div className="detail-actions">
        {order.status === "PENDING_PAYMENT" && (
          <>
            <Link className="button" to={`/checkout/pay/${order.order_no}`}>去支付</Link>
            <button className="button secondary" onClick={cancel}>取消订单</button>
          </>
        )}
        {order.status === "SHIPPED" && (
          <button className="button" onClick={confirmReceipt}>确认收货</button>
        )}
        <button className="text-button" onClick={() => navigate("/orders")}>返回订单列表</button>
      </div>
    </section>
  );
}

/* Review */

export function ReviewPage() {
  const { orderNo } = useParams();
  return (
    <PlaceholderPage
      eyebrow="REVIEW"
      title="发表评价"
      description="评价接口（商品目录服务 reviews 路由）尚未在后端实现；下单、支付、发货、收货主链路已可用。"
      actions={<Link className="button" to={`/orders/${orderNo}`}>返回订单</Link>}
    />
  );
}

/* Not found */

export function NotFoundPage() {
  return <EmptyState title="页面不存在"><Link className="button" to="/">回到首页</Link></EmptyState>;
}