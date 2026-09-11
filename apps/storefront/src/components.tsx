import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { api } from "./api";
import { useAuthStore } from "./session";

export function StorefrontShell() {
  const nickname = useAuthStore((state) => state.nickname);
  const accessToken = useAuthStore((state) => state.access_token);
  const clearSession = useAuthStore((state) => state.clearSession);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    if (!accessToken) return;
    api
      .get<{ total_quantity: number }>("/cart/count")
      .then((data) => setCartCount(data.total_quantity ?? 0))
      .catch(() => setCartCount(0));
  }, [accessToken]);

  return (
    <div className="storefront-shell">
      <header className="site-header">
        <Link to="/" className="brand">E-Shop<span>·</span></Link>
        <nav aria-label="主导航" className="primary-nav">
          <NavLink to="/categories/all">分类</NavLink>
          <NavLink to="/search">搜索</NavLink>
          <NavLink to="/orders">我的订单</NavLink>
        </nav>
        <div className="header-actions">
          <Link className="cart-link" to="/cart">购物车 <span className="badge">{cartCount}</span></Link>
          {accessToken ? (
            <>
              <Link className="user-chip" to="/account/profile">{nickname || "已登录"}</Link>
              <button className="text-button" onClick={() => { clearSession(); window.location.assign("/login"); }}>退出</button>
            </>
          ) : (
            <Link to="/login" className="button button-small">登录</Link>
          )}
        </div>
      </header>
      <main className="site-main"><Outlet /></main>
      <footer className="site-footer">© 2026 E-Shop · API Gateway `/api/v1`</footer>
    </div>
  );
}

export function AuthGuard() {
  const token = useAuthStore((state) => state.access_token);
  const location = useLocation();
  if (!token) {
    const redirect = `${location.pathname}${location.search}`;
    return <Navigate replace to={`/login?redirect=${encodeURIComponent(redirect)}`} />;
  }
  return <Outlet />;
}

export function PageSkeleton({ lines = 4 }: { lines?: number }) {
  return <div className="skeleton-card" aria-label="加载中">{Array.from({ length: lines }, (_, index) => <div className="skeleton-line" key={index} />)}</div>;
}

export function EmptyState({ title = "暂无数据", action, children }: { title?: string; action?: React.ReactNode; children?: React.ReactNode }) {
  return <div className="empty-state"><div className="empty-icon" aria-hidden="true"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 7.5h16M6.5 4h11A1.5 1.5 0 0 1 19 5.5v13a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 5 18.5v-13A1.5 1.5 0 0 1 6.5 4Z"/><path d="M8 11h8M8 15h5"/></svg></div><h2>{title}</h2>{action}{children}</div>;
}

export function ErrorBoundaryFallback() {
  return <section className="page-card"><p className="eyebrow">COMMON-8001</p><h1>页面出错，请刷新重试</h1><p>如果问题持续，请提供页面上的 trace_id 给客服。</p></section>;
}

export function PriceTag({ cents, currency = "CNY" }: { cents: number; currency?: string }) {
  return <span className="price-tag">{new Intl.NumberFormat("zh-CN", { style: "currency", currency }).format(cents / 100)}</span>;
}

export function CountdownTimer({ expiresAt }: { expiresAt: string }) {
  const remaining = Math.max(0, new Date(expiresAt).getTime() - Date.now());
  const minutes = Math.floor(remaining / 60_000).toString().padStart(2, "0");
  const seconds = Math.floor((remaining % 60_000) / 1_000).toString().padStart(2, "0");
  return <span className="countdown" aria-label="剩余时间">{remaining ? `${minutes}:${seconds}` : "已结束"}</span>;
}

export function PlaceholderPage({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
}) {
  return <section className="page-card page-placeholder"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p><div className="placeholder-panel"><div className="placeholder-dot" /><span>页面脚手架已就绪。</span></div>{actions}</section>;
}
