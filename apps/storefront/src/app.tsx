import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import { AuthGuard, ErrorBoundaryFallback, PageSkeleton, StorefrontShell } from "./components";

const HomePage = lazy(() => import("./pages").then((module) => ({ default: module.HomePage })));
const LoginPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.AuthPage mode="login" /> })));
const RegisterPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.AuthPage mode="register" /> })));
const ForgotPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.AuthPage mode="forgot" /> })));
const ListingPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.ListingPage /> })));
const SearchPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.ListingPage search /> })));
const ProductDetailPage = lazy(() => import("./pages").then((module) => ({ default: module.ProductDetailPage })));
const CartPage = lazy(() => import("./pages").then((module) => ({ default: module.CartPage })));
const AccountPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.AccountPage kind="profile" /> })));
const AddressesPage = lazy(() => import("./pages").then((module) => ({ default: () => <module.AccountPage kind="addresses" /> })));
const CheckoutPage = lazy(() => import("./pages").then((module) => ({ default: module.CheckoutPage })));
const PayPage = lazy(() => import("./pages").then((module) => ({ default: module.PayPage })));
const ResultPage = lazy(() => import("./pages").then((module) => ({ default: module.ResultPage })));
const OrdersPage = lazy(() => import("./pages").then((module) => ({ default: module.OrdersPage })));
const OrderDetailPage = lazy(() => import("./pages").then((module) => ({ default: module.OrderDetailPage })));
const ReviewPage = lazy(() => import("./pages").then((module) => ({ default: module.ReviewPage })));
const NotFoundPage = lazy(() => import("./pages").then((module) => ({ default: module.NotFoundPage })));

function RouteLoading() { return <PageSkeleton />; }

export function StorefrontApp() {
  return <Suspense fallback={<RouteLoading />}><Routes><Route element={<StorefrontShell />}><Route path="/" element={<HomePage />} /><Route path="/categories/:id" element={<ListingPage />} /><Route path="/search" element={<SearchPage />} /><Route path="/products/:id" element={<ProductDetailPage />} /><Route path="/register" element={<RegisterPage />} /><Route path="/login" element={<LoginPage />} /><Route path="/forgot-password" element={<ForgotPage />} /><Route element={<AuthGuard />}><Route path="/account/profile" element={<AccountPage />} /><Route path="/account/addresses" element={<AddressesPage />} /><Route path="/cart" element={<CartPage />} /><Route path="/checkout" element={<CheckoutPage />} /><Route path="/checkout/pay/:orderNo" element={<PayPage />} /><Route path="/checkout/result" element={<ResultPage />} /><Route path="/orders" element={<OrdersPage />} /><Route path="/orders/:orderNo" element={<OrderDetailPage />} /><Route path="/orders/:orderNo/review" element={<ReviewPage />} /></Route><Route path="*" element={<NotFoundPage />} /></Route></Routes></Suspense>;
}

export function AppErrorFallback() { return <ErrorBoundaryFallback />; }
