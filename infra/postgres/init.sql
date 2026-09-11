-- Creates one database owned by a least-privilege account per service.
-- Executed once by the postgres container's init scripts.

CREATE USER svc_user WITH PASSWORD 'svc_user_local';
CREATE USER svc_catalog WITH PASSWORD 'svc_catalog_local';
CREATE USER svc_cart WITH PASSWORD 'svc_cart_local';
CREATE USER svc_order WITH PASSWORD 'svc_order_local';
CREATE USER svc_payment WITH PASSWORD 'svc_payment_local';
CREATE USER svc_notification WITH PASSWORD 'svc_notification_local';

CREATE DATABASE ecommerce_user OWNER svc_user;
CREATE DATABASE ecommerce_catalog OWNER svc_catalog;
CREATE DATABASE ecommerce_cart OWNER svc_cart;
CREATE DATABASE ecommerce_order OWNER svc_order;
CREATE DATABASE ecommerce_payment OWNER svc_payment;
CREATE DATABASE ecommerce_notification OWNER svc_notification;