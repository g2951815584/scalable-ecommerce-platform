import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import { adminApi } from "./api";
import { applyAdminLogin, useAdminAuthStore } from "./session";

const { Title, Paragraph, Text } = Typography;

interface UserRow {
  user_id: string;
  email: string | null;
  phone: string | null;
  nickname: string;
  status: string;
  roles: string[];
  is_email_verified: boolean;
  is_phone_verified: boolean;
  registered_at: string | null;
  last_login_at: string | null;
}

interface RoleRow {
  role_id: string;
  code: string;
  name: string;
  description: string | null;
  is_enabled: boolean;
}

interface ProductRow {
  id: string;
  title: string;
  brand: string | null;
  min_price_cents: number | null;
  max_price_cents: number | null;
  status?: string;
  sales_count: number;
  rating_avg: number;
}

function yuan(cents: number | null | undefined): string {
  if (cents === null || cents === undefined) return "—";
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY" }).format(cents / 100);
}

function errMsg(error: unknown): string {
  const candidate = error as { message?: string };
  return candidate?.message ?? "请求失败，请稍后重试";
}

const STATUS_COLOR: Record<string, string> = {
  ACTIVE: "green",
  DISABLED: "red",
  LOCKED: "orange",
  DELETED: "default",
};

/* Login */

export function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSubmitting(true);
    try {
      const data = await adminApi.post<{
        access_token: string;
        refresh_token: string;
        user: { user_id: string; nickname: string; roles: string[] };
      }>("/auth/login", {
        account: form.get("account"),
        password: form.get("password"),
        client_type: "ADMIN_CONSOLE",
      });
      applyAdminLogin(data);
      navigate(params.get("redirect") || "/", { replace: true });
    } catch (error) {
      message.error(errMsg(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <Card className="login-card" bordered={false}>
        <Text type="secondary" className="kicker">E-SHOP / OPERATIONS</Text>
        <Title level={3}>运营管理后台</Title>
        <Paragraph type="secondary">使用已获授权的运营账户登录。</Paragraph>
        <form onSubmit={submit}>
          <Form.Item label="账号">
            <Input name="account" required placeholder="邮箱或手机号" />
          </Form.Item>
          <Form.Item label="密码">
            <Input.Password name="password" required placeholder="请输入密码" />
          </Form.Item>
          <Button block type="primary" htmlType="submit" loading={submitting}>登录</Button>
        </form>
      </Card>
    </main>
  );
}

/* Dashboard */

export function DashboardPage() {
  const roles = useAdminAuthStore((state) => state.roles);
  const nickname = useAdminAuthStore((state) => state.nickname);
  return (
    <div>
      <Title level={3}>数据概览</Title>
      <Paragraph type="secondary">
        欢迎，{nickname || "运营人员"}。当前角色：{roles.join(", ") || "—"}。以下功能域已接入真实后端接口，可直接使用。
      </Paragraph>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="用户与账号" value={0} suffix="个功能" /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="商品管理" value={0} suffix="个功能" /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="库存管理" value={0} suffix="个功能" /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="发货管理" value={0} suffix="个功能" /></Card></Col>
      </Row>
      <Card title="快捷入口" className="content-card">
        <Space wrap>
          <Link to="/products"><Button>商品列表</Button></Link>
          <Link to="/products/categories"><Button>分类管理</Button></Link>
          <Link to="/inventory"><Button>库存管理</Button></Link>
          <Link to="/orders/shipping"><Button>发货管理</Button></Link>
          <Link to="/system/users"><Button>用户与账号</Button></Link>
          <Link to="/system/roles"><Button>角色权限</Button></Link>
          <Link to="/notifications"><Button>通知记录</Button></Link>
        </Space>
      </Card>
    </div>
  );
}

/* Placeholder for not-yet-implemented backend surfaces */

export function AdminPlaceholderPage({ page }: { page: string }) {
  return (
    <div>
      <Title level={3}>{page}</Title>
      <Card>
        <Paragraph type="secondary">
          此功能域的后端接口尚在实现中（例如后台订单列表、退款审核工作台、交易流水、对账），前端路由与权限已就绪。
        </Paragraph>
      </Card>
    </div>
  );
}
/* User management */

export function UserManagementPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(false);
  const [roles, setRoles] = useState<RoleRow[]>([]);

  async function load(nextPage = 1, search = keyword) {
    setLoading(true);
    try {
      const data = await adminApi.get<{ items: UserRow[]; pagination: { total: number } }>("/users", {
        params: { page: nextPage, page_size: 20, keyword: search || undefined },
      });
      setUsers(data.items);
      setTotal(data.pagination.total);
      setPage(nextPage);
    } catch (error) {
      message.error(errMsg(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    adminApi.get<{ items: RoleRow[] }>("/roles").then((data) => setRoles(data.items)).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function toggleStatus(user: UserRow, status: string) {
    try {
      await adminApi.put(`/users/${user.user_id}/status`, { status, reason: "后台操作" });
      message.success("已更新账号状态");
      load(page);
    } catch (error) {
      message.error(errMsg(error));
    }
  }

  function openAssignRoles(user: UserRow) {
    let selected: string[] = [...user.roles];
    const selectedRoles = roles.map((role) => role.code);
    Modal.confirm({
      title: `为用户 ${user.nickname} 分配角色`,
      content: (
        <Select
          mode="multiple"
          style={{ width: "100%" }}
          defaultValue={selected}
          onChange={(value) => { selected = value; }}
          options={selectedRoles.map((code) => ({ label: code, value: code }))}
        />
      ),
      onOk: async () => {
        try {
          await adminApi.put(`/users/${user.user_id}/roles`, { role_codes: selected.filter(Boolean) });
          message.success("已更新角色");
          load(page);
        } catch (error) {
          message.error(errMsg(error));
        }
      },
    });
  }

  const columns = [
    { title: "用户 ID", dataIndex: "user_id", key: "user_id", width: 160, render: (v: string) => <Text code>{v}</Text> },
    { title: "账号", dataIndex: "email", key: "email", render: (v: string | null, row: UserRow) => v || row.phone || "—" },
    { title: "昵称", dataIndex: "nickname", key: "nickname" },
    { title: "角色", dataIndex: "roles", key: "roles", render: (v: string[]) => v.map((r) => <Tag key={r}>{r}</Tag>) },
    { title: "状态", dataIndex: "status", key: "status", render: (v: string) => <Tag color={STATUS_COLOR[v]}>{v}</Tag> },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, row: UserRow) => (
        <Space>
          <Button size="small" onClick={() => openAssignRoles(row)}>分配角色</Button>
          <Button size="small" danger={row.status !== "DISABLED"} onClick={() => toggleStatus(row, row.status === "DISABLED" ? "ACTIVE" : "DISABLED")}>
            {row.status === "DISABLED" ? "启用" : "禁用"}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>用户与账号</Title>
      <Form layout="inline" onFinish={() => load(1)} className="search-form">
        <Form.Item>
          <Input placeholder="按邮箱/手机号搜索" value={keyword} onChange={(e) => setKeyword(e.target.value)} allowClear />
        </Form.Item>
        <Form.Item><Button type="primary" htmlType="submit">搜索</Button></Form.Item>
      </Form>
      <Table
        rowKey="user_id"
        loading={loading}
        columns={columns}
        dataSource={users}
        pagination={{ current: page, total, pageSize: 20, onChange: (nextPage) => load(nextPage) }}
      />
    </div>
  );
}

/* Roles */

export function RoleListPage() {
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    adminApi.get<{ items: RoleRow[] }>("/roles")
      .then((data) => setRoles(data.items))
      .catch((error) => message.error(errMsg(error)))
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { title: "角色", dataIndex: "code", key: "code", render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "描述", dataIndex: "description", key: "description" },
  ];

  return (
    <div>
      <Title level={3}>角色权限</Title>
      <Table rowKey="role_id" loading={loading} columns={columns} dataSource={roles} pagination={false} />
    </div>
  );
}
/* Products */

interface CategoryNode {
  id: string;
  name: string;
  slug: string;
  depth: number;
  children: CategoryNode[];
}

export function ProductManagementPage() {
  const [products, setProducts] = useState<ProductRow[]>([]);
  const [categories, setCategories] = useState<CategoryNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm] = Form.useForm();

  async function load() {
    setLoading(true);
    try {
      const [list, tree] = await Promise.all([
        adminApi.get<{ items: ProductRow[] }>("/products", { params: { page: 1, page_size: 100 } }),
        adminApi.get<{ items: CategoryNode[] }>("/categories/tree"),
      ]);
      setProducts(list.items);
      setCategories(tree.items);
    } catch (error) {
      message.error(errMsg(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const categoryOptions = categories
    .flatMap((c) => [c, ...(c.children ?? [])])
    .map((c) => ({ label: c.name, value: c.id }));

  async function createProduct(values: { category_id: string; title: string; sku_code: string; price_cents: number; spec_text: string; initial_stock: number }) {
    try {
      await adminApi.post("/admin/products", {
        category_id: values.category_id,
        title: values.title,
        skus: [{ sku_code: values.sku_code, price_cents: values.price_cents, spec_text: values.spec_text || "默认规格", initial_stock: values.initial_stock ?? 0 }],
      });
      message.success("商品已创建（草稿状态，可通过上架发布）");
      setCreateOpen(false);
      createForm.resetFields();
      load();
    } catch (error) {
      message.error(errMsg(error));
    }
  }

  async function togglePublish(product: ProductRow, publish: boolean) {
    try {
      await adminApi.post(`/admin/products/${product.id}/${publish ? "publish" : "unpublish"}`);
      message.success(publish ? "已上架" : "已下架");
      load();
    } catch (error) {
      message.error(errMsg(error));
    }
  }

  const columns = [
    { title: "ID", dataIndex: "id", key: "id", width: 150, render: (v: string) => <Text code>{v}</Text> },
    { title: "商品", dataIndex: "title", key: "title" },
    { title: "品牌", dataIndex: "brand", key: "brand", render: (v: string | null) => v || "—" },
    { title: "价格", key: "price", render: (_: unknown, row: ProductRow) => yuan(row.min_price_cents) },
    { title: "销量", dataIndex: "sales_count", key: "sales_count" },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, row: ProductRow) => (
        <Space>
          <Button size="small" type="primary" onClick={() => togglePublish(row, true)}>上架</Button>
          <Button size="small" onClick={() => togglePublish(row, false)}>下架</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="admin-actions">
        <Title level={3}>商品列表</Title>
        <Button type="primary" onClick={() => setCreateOpen(true)}>新建商品</Button>
      </div>
      <Table rowKey="id" loading={loading} columns={columns} dataSource={products} pagination={false} />

      <Modal title="新建商品" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => createForm.submit()} okText="创建">
        <Form form={createForm} layout="vertical" onFinish={createProduct}>
          <Form.Item name="title" label="商品标题" rules={[{ required: true }]}>
            <Input placeholder="例如：降噪无线耳机 Pro" />
          </Form.Item>
          <Form.Item name="category_id" label="所属分类" rules={[{ required: true }]}>
            <Select options={categoryOptions} placeholder="选择分类" />
          </Form.Item>
          <Form.Item name="sku_code" label="SKU 编码" rules={[{ required: true }]}>
            <Input placeholder="例如：SKU-0001" />
          </Form.Item>
          <Form.Item name="spec_text" label="规格">
            <Input placeholder="例如：颜色:黑色" />
          </Form.Item>
          <Form.Item name="price_cents" label="价格（分）" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: "100%" }} placeholder="例如：29900" />
          </Form.Item>
          <Form.Item name="initial_stock" label="初始库存">
            <InputNumber min={0} style={{ width: "100%" }} placeholder="0" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
/* Categories */

export function CategoryPage() {
  const [categories, setCategories] = useState<CategoryNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm] = Form.useForm();

  async function load() {
    setLoading(true);
    try {
      const tree = await adminApi.get<{ items: CategoryNode[] }>("/categories/tree");
      setCategories(tree.items);
    } catch (error) {
      message.error(errMsg(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createCategory(values: { name: string; slug: string; parent_id?: string }) {
    try {
      await adminApi.post("/admin/categories", {
        name: values.name,
        slug: values.slug,
        parent_id: values.parent_id || undefined,
        sort_order: 0,
      });
      message.success("分类已创建");
      setCreateOpen(false);
      createForm.resetFields();
      load();
    } catch (error) {
      message.error(errMsg(error));
    }
  }

  const columns = [
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "slug", dataIndex: "slug", key: "slug", render: (v: string) => <Text code>{v}</Text> },
    { title: "层级", dataIndex: "depth", key: "depth", width: 80 },
  ];

  return (
    <div>
      <div className="admin-actions">
        <Title level={3}>分类管理</Title>
        <Button type="primary" onClick={() => setCreateOpen(true)}>新建分类</Button>
      </div>
      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={categories}
        pagination={false}
        expandable={{ childrenColumnName: "children" }}
      />
      <Modal title="新建分类" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => createForm.submit()} okText="创建">
        <Form form={createForm} layout="vertical" onFinish={createCategory}>
          <Form.Item name="name" label="分类名称" rules={[{ required: true }]}>
            <Input placeholder="例如：数码 3C" />
          </Form.Item>
          <Form.Item name="slug" label="slug" rules={[{ required: true }]}>
            <Input placeholder="例如：digital" />
          </Form.Item>
          <Form.Item name="parent_id" label="父分类（可选）">
            <Select options={categories.map((c) => ({ label: c.name, value: c.id }))} allowClear placeholder="留空为一级分类" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

/* Inventory */

export function InventoryPage() {
  const [form] = Form.useForm();

  async function adjust(values: { sku_id: string; adjust_type: string; quantity: number; reason: string }) {
    try {
      const result = await adminApi.put<{ available: number; stock: number }>(`/admin/inventory/${values.sku_id}`, {
        adjust_type: values.adjust_type,
        quantity: values.quantity,
        reason: values.reason,
      });
      message.success(`调整完成，当前可售 ${result.available} 件`);
      form.resetFields();
    } catch (error) {
      message.error(errMsg(error));
    }
  }

  return (
    <div>
      <Title level={3}>库存管理</Title>
      <Card style={{ maxWidth: 480 }}>
        <Form form={form} layout="vertical" onFinish={adjust}>
          <Form.Item name="sku_id" label="SKU ID" rules={[{ required: true }]}>
            <Input placeholder="输入 SKU ID（可在商品详情或商品列表中获得）" />
          </Form.Item>
          <Form.Item name="adjust_type" label="调整方式" rules={[{ required: true }]} initialValue="SET">
            <Select
              options={[
                { label: "设为目标库存（SET）", value: "SET" },
                { label: "增加（INCREASE）", value: "INCREASE" },
                { label: "减少（DECREASE）", value: "DECREASE" },
              ]}
            />
          </Form.Item>
          <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="reason" label="调整原因" rules={[{ required: true }]}>
            <Input placeholder="例如：春季补货入库" />
          </Form.Item>
          <Button type="primary" htmlType="submit">提交调整</Button>
        </Form>
      </Card>
    </div>
  );
}

/* Shipping */

export function ShippingPage() {
  const [form] = Form.useForm();

  async function ship(values: { order_no: string; carrier: string; tracking_no: string }) {
    try {
      const result = await adminApi.post<{ status: string }>(`/admin/orders/${values.order_no}/ship`, {
        carrier: values.carrier || "SF",
        tracking_no: values.tracking_no,
      });
      message.success(`订单 ${values.order_no} 已发货（${result.status}）`);
      form.resetFields();
    } catch (error) {
      message.error(errMsg(error));
    }
  }

  return (
    <div>
      <Title level={3}>发货管理</Title>
      <Paragraph type="secondary">后台订单列表接口尚未实现，请直接输入订单号进行发货。</Paragraph>
      <Card style={{ maxWidth: 480 }}>
        <Form form={form} layout="vertical" onFinish={ship}>
          <Form.Item name="order_no" label="订单号" rules={[{ required: true }]}>
            <Input placeholder="例如：SO20260910000001" />
          </Form.Item>
          <Form.Item name="carrier" label="承运商" initialValue="SF">
            <Select
              options={[
                { label: "顺丰速运（SF）", value: "SF" },
                { label: "圆通速递（YTO）", value: "YTO" },
                { label: "中通快递（ZTO）", value: "ZTO" },
                { label: "京东物流（JD）", value: "JD" },
                { label: "中国邮政（EMS）", value: "EMS" },
              ]}
            />
          </Form.Item>
          <Form.Item name="tracking_no" label="物流单号" rules={[{ required: true }]}>
            <Input placeholder="例如：SF1234567890" />
          </Form.Item>
          <Button type="primary" htmlType="submit">确认发货</Button>
        </Form>
      </Card>
    </div>
  );
}
/* Notification records */

interface NotificationRow {
  record_no: string;
  event_type: string | null;
  template_code: string;
  channel: string;
  provider: string | null;
  recipient_masked: string;
  subject: string | null;
  status: string;
  created_at: string;
}

export function NotificationRecordsPage() {
  const [records, setRecords] = useState<NotificationRow[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await adminApi.get<{ items: NotificationRow[] }>("/admin/notification-records", {
        params: { page: 1, page_size: 50 },
      });
      setRecords(data.items);
    } catch (error) {
      message.error(errMsg(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns = [
    { title: "通知单号", dataIndex: "record_no", key: "record_no", render: (v: string) => <Text code>{v}</Text> },
    { title: "事件", dataIndex: "event_type", key: "event_type", render: (v: string | null) => v || "—" },
    { title: "模板", dataIndex: "template_code", key: "template_code" },
    { title: "渠道", dataIndex: "channel", key: "channel", render: (v: string) => <Tag>{v}</Tag> },
    { title: "收件人", dataIndex: "recipient_masked", key: "recipient_masked" },
    { title: "状态", dataIndex: "status", key: "status", render: (v: string) => <Tag color={v === "SENT" || v === "DELIVERED" ? "green" : v === "FAILED" ? "red" : "default"}>{v}</Tag> },
    { title: "时间", dataIndex: "created_at", key: "created_at", render: (v: string) => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <Title level={3}>通知发送记录</Title>
      <Table rowKey="record_no" loading={loading} columns={columns} dataSource={records} pagination={false} />
    </div>
  );
}

/* Not found */

export function NotFoundPage() {
  return (
    <div style={{ textAlign: "center", paddingTop: 80 }}>
      <Title level={2}>页面不存在</Title>
      <Link to="/"><Button type="primary">回到概览</Button></Link>
    </div>
  );
}