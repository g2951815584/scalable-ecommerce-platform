import type { ComponentType, LazyExoticComponent } from "react";
import { lazy } from "react";
import type { Role } from "@ecommerce/frontend-shared";
import {
  AppstoreOutlined,
  AuditOutlined,
  BarChartOutlined,
  BellOutlined,
  ContainerOutlined,
  DashboardOutlined,
  DollarOutlined,
  InboxOutlined,
  SettingOutlined,
  ShopOutlined,
  TeamOutlined,
} from "@ant-design/icons";

export type AdminRoute = {
  key: string;
  path: string;
  title: string;
  roles: readonly Role[];
  icon?: React.ReactNode;
  menu?: boolean;
  element: LazyExoticComponent<ComponentType>;
};

const lazyPage = (name: keyof typeof import("./pages")) =>
  lazy(() => import("./pages").then((module) => ({ default: module[name] as ComponentType })));

const lazyPlaceholder = (pageName: string) =>
  lazy(() =>
    import("./pages").then((module) => ({
      default: (() => <module.AdminPlaceholderPage page={pageName} />) as ComponentType,
    })),
  );

export const adminRoutes: AdminRoute[] = [
  { key: "dashboard", path: "/", title: "数据概览", roles: ["ADMIN", "PRODUCT_OPS", "ORDER_OPS", "FINANCE"], icon: <DashboardOutlined />, menu: true, element: lazy(() => import("./pages").then((m) => ({ default: m.DashboardPage }))) },
  { key: "categories", path: "/products/categories", title: "分类管理", roles: ["PRODUCT_OPS", "ADMIN"], icon: <AppstoreOutlined />, menu: true, element: lazyPage("CategoryPage") },
  { key: "products", path: "/products", title: "商品列表", roles: ["PRODUCT_OPS", "ADMIN"], icon: <ShopOutlined />, menu: true, element: lazyPage("ProductManagementPage") },
  { key: "product-new", path: "/products/new", title: "新建商品", roles: ["PRODUCT_OPS", "ADMIN"], element: lazyPage("ProductManagementPage") },
  { key: "product-edit", path: "/products/:id/edit", title: "编辑商品", roles: ["PRODUCT_OPS", "ADMIN"], element: lazyPage("ProductManagementPage") },
  { key: "inventory", path: "/inventory", title: "库存管理", roles: ["PRODUCT_OPS", "ADMIN"], icon: <InboxOutlined />, menu: true, element: lazyPage("InventoryPage") },
  { key: "orders", path: "/orders", title: "订单列表", roles: ["ORDER_OPS", "WAREHOUSE", "CS", "FINANCE", "ADMIN"], icon: <ContainerOutlined />, menu: true, element: lazyPlaceholder("订单列表") },
  { key: "order-detail", path: "/orders/:orderNo", title: "订单详情", roles: ["ORDER_OPS", "CS", "ADMIN"], element: lazyPlaceholder("订单详情") },
  { key: "shipping", path: "/orders/shipping", title: "发货管理", roles: ["WAREHOUSE", "ADMIN"], icon: <AuditOutlined />, menu: true, element: lazyPage("ShippingPage") },
  { key: "refunds", path: "/refunds", title: "退款审核", roles: ["ORDER_OPS", "CS", "ADMIN"], icon: <AuditOutlined />, menu: true, element: lazyPlaceholder("退款审核") },
  { key: "transactions", path: "/finance/transactions", title: "交易流水", roles: ["FINANCE", "ADMIN"], icon: <DollarOutlined />, menu: true, element: lazyPlaceholder("交易流水") },
  { key: "reconciliation", path: "/finance/reconciliation", title: "对账管理", roles: ["FINANCE", "ADMIN"], icon: <BarChartOutlined />, menu: true, element: lazyPlaceholder("对账管理") },
  { key: "users", path: "/system/users", title: "用户与账号", roles: ["ADMIN"], icon: <TeamOutlined />, menu: true, element: lazyPage("UserManagementPage") },
  { key: "roles", path: "/system/roles", title: "角色权限", roles: ["ADMIN"], icon: <SettingOutlined />, menu: true, element: lazyPage("RoleListPage") },
  { key: "notifications", path: "/notifications", title: "通知记录", roles: ["ADMIN"], icon: <BellOutlined />, menu: true, element: lazyPage("NotificationRecordsPage") },
];
