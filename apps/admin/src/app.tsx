import { Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { ConfigProvider, Layout, Menu, Spin, Typography } from "antd";
import { LogoutOutlined } from "@ant-design/icons";
import { Link, useLocation } from "react-router-dom";
import { AdminAuthGuard, RoleGuard } from "./guards";
import { adminRoutes } from "./routes";
import { LoginPage, NotFoundPage } from "./pages";
import { useAdminAuthStore } from "./session";
import "./styles.css";

const { Header, Content, Sider } = Layout;

function AdminShell() {
  const location = useLocation();
  const roles = useAdminAuthStore((state) => state.roles);
  const nickname = useAdminAuthStore((state) => state.nickname);
  const clearSession = useAdminAuthStore((state) => state.clearSession);
  const items = adminRoutes.filter((route) => route.menu && route.roles.some((role) => roles.includes(role))).map((route) => ({ key: route.path, icon: route.icon, label: <Link to={route.path}>{route.title}</Link> }));
  return <Layout className="admin-shell"><Sider breakpoint="lg" collapsedWidth="0" theme="dark"><div className="admin-brand">E-Shop <span>Ops</span></div><Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={items} /></Sider><Layout><Header className="admin-header"><Typography.Text>运营工作台</Typography.Text><div><Typography.Text type="secondary">{nickname || "运营人员"}</Typography.Text><button className="logout" onClick={() => { clearSession(); window.location.assign("/admin/login"); }} aria-label="退出登录"><LogoutOutlined /></button></div></Header><Content className="admin-content"><Suspense fallback={<div className="loading"><Spin size="large" /></div>}><Routes>{adminRoutes.map((route) => { const Page = route.element; return <Route key={route.key} path={route.path} element={<RoleGuard roles={route.roles}><Page /></RoleGuard>} />; })}<Route path="*" element={<NotFoundPage />} /></Routes></Suspense></Content></Layout></Layout>;
}

export function AdminApp() {
  return <ConfigProvider theme={{ token: { colorPrimary: "#a16207", colorLink: "#7c4a06", borderRadius: 10, fontFamily: "Inter, system-ui, sans-serif", colorBgLayout: "#faf9f7" }, components: { Layout: { siderBg: "#211d1a", headerBg: "rgba(255,255,255,.88)" }, Button: { controlHeight: 40 } } }}><Routes><Route path="/login" element={<LoginPage />} /><Route element={<AdminAuthGuard />}><Route path="/*" element={<AdminShell />} /></Route><Route path="*" element={<Navigate replace to="/" />} /></Routes></ConfigProvider>;
}
