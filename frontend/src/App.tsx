
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Megaphone,
  BrainCircuit,
  TrendingUp,
  Truck,
  CircleDollarSign,
  Languages,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Boxes,
  ClipboardList,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import './App.css'

type DashboardData = {
  profit: number
  sales: number
  adSpend: number
  deliveryCosts: number
  currency: string
}

type Product = {
  id: number
  name: string
  sku: string
  purchase_price: string
  selling_price: string
  packaging_cost: string
  stock_quantity: number
  created_at: string
}

type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'shipped'
  | 'delivered'
  | 'refused'
  | 'returned'

type Order = {
  id: number
  order_number: string
  customer_name: string
  customer_phone: string
  product: number
  product_name: string
  quantity: number
  unit_price: string
  delivery_cost: string
  status: OrderStatus
  notes: string
  total_amount: string
  created_at: string
}

type Page = 'dashboard' | 'products' | 'orders'

const API_URL = 'http://127.0.0.1:8000/api'

const salesData = [
  { day: '01', sales: 18000 },
  { day: '05', sales: 26000 },
  { day: '09', sales: 22000 },
  { day: '13', sales: 39000 },
  { day: '17', sales: 31000 },
  { day: '21', sales: 48000 },
  { day: '25', sales: 42000 },
  { day: '30', sales: 62000 },
]

function App() {
  const { t, i18n } = useTranslation()

  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [dashboardError, setDashboardError] = useState<string | null>(null)
  const [dashboardLoading, setDashboardLoading] = useState(true)

  const [products, setProducts] = useState<Product[]>([])
  const [productsLoading, setProductsLoading] = useState(false)
  const [productsError, setProductsError] = useState<string | null>(null)

  const [orders, setOrders] = useState<Order[]>([])
  const [ordersLoading, setOrdersLoading] = useState(false)
  const [ordersError, setOrdersError] = useState<string | null>(null)

  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [refreshKey, setRefreshKey] = useState(0)

  const language = i18n.resolvedLanguage === 'fr' ? 'fr' : 'ar'
  const isArabic = language === 'ar'

  useEffect(() => {
    document.documentElement.lang = language
    document.documentElement.dir = isArabic ? 'rtl' : 'ltr'
  }, [language, isArabic])

  // Charger le dashboard depuis Django
  useEffect(() => {
    const controller = new AbortController()

    async function fetchDashboard() {
      try {
        setDashboardLoading(true)

        const response = await fetch(`${API_URL}/dashboard/`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Dashboard API error')
        }

        const data: DashboardData = await response.json()
        setDashboard(data)
        setDashboardError(null)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return

        setDashboardError(
          isArabic
            ? 'تعذر الاتصال بالخادم. يرجى التأكد من تشغيل Django.'
            : 'Impossible de contacter Django. Vérifiez que le serveur est démarré.'
        )
      } finally {
        if (!controller.signal.aborted) {
          setDashboardLoading(false)
        }
      }
    }

    void fetchDashboard()

    return () => controller.abort()
  }, [isArabic, refreshKey])

  // Charger les produits depuis Django
  useEffect(() => {
    if (currentPage !== 'products') return

    const controller = new AbortController()

    async function fetchProducts() {
      try {
        setProductsLoading(true)
        setProductsError(null)

        const response = await fetch(`${API_URL}/products/`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Products API error')
        }

        const data = await response.json()
        setProducts(Array.isArray(data) ? data : data.results ?? [])
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return

        setProductsError(
          isArabic
            ? 'تعذر تحميل المنتجات. تحقق من اتصال الخادم.'
            : 'Impossible de charger les produits. Vérifiez le serveur Django.'
        )
      } finally {
        if (!controller.signal.aborted) {
          setProductsLoading(false)
        }
      }
    }

    void fetchProducts()

    return () => controller.abort()
  }, [currentPage, isArabic, refreshKey])

  // Charger les commandes depuis Django
  useEffect(() => {
    if (currentPage !== 'orders') return

    const controller = new AbortController()

    async function fetchOrders() {
      try {
        setOrdersLoading(true)
        setOrdersError(null)

        const response = await fetch(`${API_URL}/orders/`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Orders API error')
        }

        const data = await response.json()
        setOrders(Array.isArray(data) ? data : data.results ?? [])
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return

        setOrdersError(
          isArabic
            ? 'تعذر تحميل الطلبات. تحقق من اتصال الخادم.'
            : 'Impossible de charger les commandes. Vérifiez le serveur Django.'
        )
      } finally {
        if (!controller.signal.aborted) {
          setOrdersLoading(false)
        }
      }
    }

    void fetchOrders()

    return () => controller.abort()
  }, [currentPage, isArabic, refreshKey])

  const changeLanguage = (nextLanguage: 'ar' | 'fr') => {
    void i18n.changeLanguage(nextLanguage)
  }

  const money = (value: number) =>
    new Intl.NumberFormat(isArabic ? 'ar-DZ' : 'fr-DZ', {
      style: 'currency',
      currency: dashboard?.currency || 'DZD',
      maximumFractionDigits: 0,
    }).format(value)

  const productMoney = (value: string | number) =>
    new Intl.NumberFormat(isArabic ? 'ar-DZ' : 'fr-DZ', {
      style: 'currency',
      currency: 'DZD',
      maximumFractionDigits: 2,
    }).format(Number(value) || 0)

  const formatDate = (value: string) => {
    if (!value) return '—'

    const date = new Date(value)

    if (Number.isNaN(date.getTime())) return '—'

    return new Intl.DateTimeFormat(isArabic ? 'ar-DZ' : 'fr-DZ', {
      dateStyle: 'medium',
    }).format(date)
  }

  const getStatusLabel = (status: OrderStatus | string) => {
    const labels: Record<string, { fr: string; ar: string }> = {
      pending: { fr: 'En attente', ar: 'قيد الانتظار' },
      confirmed: { fr: 'Confirmée', ar: 'مؤكدة' },
      shipped: { fr: 'Expédiée', ar: 'تم الشحن' },
      delivered: { fr: 'Livrée', ar: 'تم التسليم' },
      refused: { fr: 'Refusée', ar: 'مرفوضة' },
      returned: { fr: 'Retournée', ar: 'مرتجعة' },
    }

    return labels[status]?.[language] ?? status
  }

  const getStatusColor = (status: OrderStatus | string) => {
    const colors: Record<string, { background: string; color: string }> = {
      pending: { background: '#fff7e6', color: '#b7791f' },
      confirmed: { background: '#e8f1ff', color: '#245bc5' },
      shipped: { background: '#f0eaff', color: '#7042b8' },
      delivered: { background: '#e6f7ed', color: '#18794e' },
      refused: { background: '#ffebeb', color: '#c53030' },
      returned: { background: '#f3f4f6', color: '#4b5563' },
    }

    return colors[status] ?? colors.pending
  }

  const menu = [
    {
      label: t('dashboard'),
      icon: LayoutDashboard,
      page: 'dashboard' as const,
    },
    {
      label: t('products'),
      icon: Package,
      page: 'products' as const,
    },
    {
      label: t('orders'),
      icon: ShoppingCart,
      page: 'orders' as const,
    },
    {
      label: t('advertising'),
      icon: Megaphone,
      page: null,
    },
  ]

  const totalCosts = dashboard
    ? dashboard.adSpend + dashboard.deliveryCosts
    : 0

  return (
    <div className="app-shell" dir={isArabic ? 'rtl' : 'ltr'}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <TrendingUp size={23} />
          </div>
          <div className="brand-copy">
            <strong>AI Copilot</strong>
            <span>E-COMMERCE INTELLIGENCE</span>
          </div>
        </div>

        <div className="menu-caption">
          {isArabic ? 'القائمة الرئيسية' : 'MENU PRINCIPAL'}
        </div>

        <nav className="navigation">
          {menu.map(({ label, icon: Icon, page }) => (
            <button
              className={`nav-item ${page !== null && currentPage === page ? 'active' : ''
                }`}
              key={label}
              type="button"
              disabled={page === null}
              onClick={() => {
                if (page !== null) setCurrentPage(page)
              }}
              title={
                page === null
                  ? isArabic
                    ? 'قريبًا'
                    : 'Bientôt disponible'
                  : label
              }
            >
              <Icon size={19} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="ai-card">
            <BrainCircuit size={23} />
            <strong>
              {isArabic ? 'مستشارك الذكي' : 'Votre conseiller IA'}
            </strong>
            <p>
              {isArabic
                ? 'اكتشف فرصًا جديدة لتحسين أرباحك.'
                : 'Découvrez comment améliorer vos bénéfices.'}
            </p>
            <span>{isArabic ? 'قريبًا' : 'BIENTÔT'}</span>
          </div>

          <div className="profile">
            <div className="avatar">EC</div>
            <div>
              <strong>{isArabic ? 'متجري' : 'Ma boutique'}</strong>
              <span>{isArabic ? 'حساب تجريبي' : 'Compte démo'}</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>{t('appName')}</span>
            <span className="breadcrumb-separator">/</span>
            <strong>
              {currentPage === 'dashboard'
                ? t('dashboard')
                : currentPage === 'products'
                  ? t('products')
                  : t('orders')}
            </strong>
          </div>

          <div className="topbar-actions">
            <span className="demo-badge">
              <span className="status-dot" />
              {isArabic ? 'وضع تجريبي' : 'Mode démo'}
            </span>

            <div className="language-switch" aria-label={t('language')}>
              <Languages size={17} />

              <button
                className={language === 'ar' ? 'selected' : ''}
                onClick={() => changeLanguage('ar')}
                type="button"
                aria-pressed={language === 'ar'}
              >
                العربية
              </button>

              <span className="language-divider">|</span>

              <button
                className={language === 'fr' ? 'selected' : ''}
                onClick={() => changeLanguage('fr')}
                type="button"
                aria-pressed={language === 'fr'}
              >
                FR
              </button>
            </div>
          </div>
        </header>

        {/* PAGE PRODUITS */}
        {currentPage === 'products' && (
          <section className="products-page">
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  {isArabic ? 'إدارة المخزون' : 'GESTION DU CATALOGUE'}
                </div>
                <h1>{t('products')}</h1>
                <p>
                  {isArabic
                    ? 'تابع منتجاتك وأسعارها والكميات المتوفرة.'
                    : 'Consultez vos produits, leurs prix et les quantités en stock.'}
                </p>
              </div>

              <button
                type="button"
                className="period-select"
                onClick={() => setRefreshKey((value) => value + 1)}
              >
                <RefreshCw size={16} />
                {isArabic ? 'تحديث القائمة' : 'Actualiser'}
              </button>
            </div>

            <div className="demo-notice">
              <span className="notice-icon">i</span>
              <span>
                {isArabic
                  ? 'هذه المنتجات تأتي مباشرة من قاعدة بياناتك.'
                  : 'Ces produits proviennent directement de ta base de données Django.'}
              </span>
            </div>

            {productsLoading && (
              <div className="panel" style={{ padding: 24 }}>
                {isArabic ? 'جارٍ تحميل المنتجات...' : 'Chargement des produits...'}
              </div>
            )}

            {productsError && (
              <div className="panel" style={{ padding: 24 }}>
                <p role="alert">{productsError}</p>
                <button
                  type="button"
                  className="period-select"
                  onClick={() => setRefreshKey((value) => value + 1)}
                >
                  <RefreshCw size={16} />
                  {isArabic ? 'إعادة المحاولة' : 'Réessayer'}
                </button>
              </div>
            )}

            {!productsLoading && !productsError && products.length === 0 && (
              <div className="panel" style={{ padding: 32, textAlign: 'center' }}>
                <Boxes size={38} />
                <h2>
                  {isArabic ? 'لا توجد منتجات بعد' : 'Aucun produit pour le moment'}
                </h2>
                <p>
                  {isArabic
                    ? 'أضف منتجًا من لوحة إدارة Django لعرضه هنا.'
                    : 'Ajoute un produit depuis l’administration Django pour le voir ici.'}
                </p>
                <a
                  href="http://127.0.0.1:8000/admin/"
                  target="_blank"
                  rel="noreferrer"
                >
                  {isArabic ? 'فتح لوحة الإدارة' : 'Ouvrir Django Admin'}
                </a>
              </div>
            )}

            {!productsLoading && !productsError && products.length > 0 && (
              <div className="panel" style={{ padding: 20 }}>
                <div className="panel-heading">
                  <div>
                    <h2>
                      {isArabic ? 'قائمة المنتجات' : 'Liste des produits'}
                    </h2>
                    <p>
                      {products.length} {isArabic ? 'منتج(ات)' : 'produit(s)'}
                    </p>
                  </div>
                  <Package size={24} />
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table
                    style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      textAlign: isArabic ? 'right' : 'left',
                    }}
                  >
                    <thead>
                      <tr>
                        {[
                          'ID',
                          isArabic ? 'المنتج' : 'Produit',
                          isArabic ? 'المرجع' : 'Référence',
                          isArabic ? 'سعر الشراء' : "Prix d'achat",
                          isArabic ? 'سعر البيع' : 'Prix de vente',
                          isArabic ? 'التغليف' : 'Emballage',
                          isArabic ? 'المخزون' : 'Stock',
                        ].map((heading) => (
                          <th
                            key={heading}
                            style={{
                              padding: 12,
                              borderBottom: '1px solid #e5e7eb',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {heading}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {products.map((product) => (
                        <tr key={product.id}>
                          <td style={{ padding: 12 }}>{product.id}</td>
                          <td style={{ padding: 12, fontWeight: 600 }}>
                            {product.name}
                          </td>
                          <td style={{ padding: 12 }}>{product.sku || '—'}</td>
                          <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                            {productMoney(product.purchase_price)}
                          </td>
                          <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                            {productMoney(product.selling_price)}
                          </td>
                          <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                            {productMoney(product.packaging_cost)}
                          </td>
                          <td style={{ padding: 12 }}>{product.stock_quantity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>
        )}

        {/* PAGE COMMANDES */}
        {currentPage === 'orders' && (
          <section className="products-page">
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  {isArabic ? 'إدارة المبيعات' : 'GESTION DES VENTES'}
                </div>
                <h1>{t('orders')}</h1>
                <p>
                  {isArabic
                    ? 'تابع طلبات العملاء والمبالغ وحالة كل طلب.'
                    : 'Consultez les commandes clients, les montants et leurs statuts.'}
                </p>
              </div>

              <button
                type="button"
                className="period-select"
                onClick={() => setRefreshKey((value) => value + 1)}
              >
                <RefreshCw size={16} />
                {isArabic ? 'تحديث الطلبات' : 'Actualiser'}
              </button>
            </div>

            <div className="demo-notice">
              <span className="notice-icon">i</span>
              <span>
                {isArabic
                  ? 'الطلبات معروضة مباشرة من قاعدة بيانات Django.'
                  : 'Les commandes affichées proviennent directement de ta base de données Django.'}
              </span>
            </div>

            {ordersLoading && (
              <div className="panel" style={{ padding: 24 }}>
                {isArabic ? 'جارٍ تحميل الطلبات...' : 'Chargement des commandes...'}
              </div>
            )}

            {ordersError && (
              <div className="panel" style={{ padding: 24 }}>
                <p role="alert">{ordersError}</p>
                <button
                  type="button"
                  className="period-select"
                  onClick={() => setRefreshKey((value) => value + 1)}
                >
                  <RefreshCw size={16} />
                  {isArabic ? 'إعادة المحاولة' : 'Réessayer'}
                </button>
              </div>
            )}

            {!ordersLoading && !ordersError && orders.length === 0 && (
              <div className="panel" style={{ padding: 32, textAlign: 'center' }}>
                <ClipboardList size={40} />
                <h2>
                  {isArabic ? 'لا توجد طلبات بعد' : 'Aucune commande pour le moment'}
                </h2>
                <p>
                  {isArabic
                    ? 'أضف طلبًا من لوحة إدارة Django لعرضه هنا.'
                    : 'Ajoute une commande depuis Django Admin pour la voir ici.'}
                </p>
                <a
                  href="http://127.0.0.1:8000/admin/"
                  target="_blank"
                  rel="noreferrer"
                >
                  {isArabic ? 'فتح لوحة الإدارة' : 'Ouvrir Django Admin'}
                </a>
              </div>
            )}

            {!ordersLoading && !ordersError && orders.length > 0 && (
              <>
                <div className="metrics-grid">
                  <article className="metric-card">
                    <div className="metric-top">
                      <span className="metric-label">
                        {isArabic ? 'إجمالي الطلبات' : 'Total commandes'}
                      </span>
                      <span className="metric-icon sales-icon">
                        <ShoppingCart size={21} />
                      </span>
                    </div>
                    <div className="metric-value">{orders.length}</div>
                    <div className="metric-foot">
                      {isArabic ? 'جميع الحالات' : 'Tous les statuts'}
                    </div>
                  </article>

                  <article className="metric-card">
                    <div className="metric-top">
                      <span className="metric-label">
                        {isArabic ? 'طلبات قيد الانتظار' : 'En attente'}
                      </span>
                      <span className="metric-icon ads-icon">
                        <ClipboardList size={21} />
                      </span>
                    </div>
                    <div className="metric-value">
                      {orders.filter((order) => order.status === 'pending').length}
                    </div>
                    <div className="metric-foot">
                      {isArabic ? 'تحتاج إلى المتابعة' : 'À traiter'}
                    </div>
                  </article>

                  <article className="metric-card">
                    <div className="metric-top">
                      <span className="metric-label">
                        {isArabic ? 'طلبات تم تسليمها' : 'Commandes livrées'}
                      </span>
                      <span className="metric-icon profit-icon">
                        <Truck size={21} />
                      </span>
                    </div>
                    <div className="metric-value">
                      {orders.filter((order) => order.status === 'delivered').length}
                    </div>
                    <div className="metric-foot">
                      {isArabic ? 'تم التسليم بنجاح' : 'Livraisons réussies'}
                    </div>
                  </article>
                </div>

                <div className="panel" style={{ padding: 20 }}>
                  <div className="panel-heading">
                    <div>
                      <h2>
                        {isArabic ? 'قائمة الطلبات' : 'Liste des commandes'}
                      </h2>
                      <p>
                        {orders.length}{' '}
                        {isArabic ? 'طلب(ات)' : 'commande(s)'}
                      </p>
                    </div>
                    <ShoppingCart size={24} />
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table
                      style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        textAlign: isArabic ? 'right' : 'left',
                      }}
                    >
                      <thead>
                        <tr>
                          {[
                            isArabic ? 'رقم الطلب' : 'N° commande',
                            isArabic ? 'العميل' : 'Client',
                            isArabic ? 'المنتج' : 'Produit',
                            isArabic ? 'الكمية' : 'Quantité',
                            isArabic ? 'سعر الوحدة' : 'Prix unitaire',
                            isArabic ? 'المبلغ الإجمالي' : 'Montant total',
                            isArabic ? 'التوصيل' : 'Livraison',
                            isArabic ? 'الحالة' : 'Statut',
                            isArabic ? 'التاريخ' : 'Date',
                          ].map((heading) => (
                            <th
                              key={heading}
                              style={{
                                padding: 12,
                                borderBottom: '1px solid #e5e7eb',
                                whiteSpace: 'nowrap',
                                fontSize: 13,
                              }}
                            >
                              {heading}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody>
                        {orders.map((order) => {
                          const statusStyle = getStatusColor(order.status)

                          return (
                            <tr key={order.id}>
                              <td
                                style={{
                                  padding: 12,
                                  fontWeight: 600,
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {order.order_number}
                              </td>

                              <td style={{ padding: 12, minWidth: 150 }}>
                                <div style={{ fontWeight: 600 }}>
                                  {order.customer_name}
                                </div>
                                {order.customer_phone && (
                                  <div
                                    style={{
                                      fontSize: 12,
                                      color: '#8992a5',
                                      marginTop: 4,
                                    }}
                                  >
                                    {order.customer_phone}
                                  </div>
                                )}
                              </td>

                              <td style={{ padding: 12, minWidth: 130 }}>
                                {order.product_name || `#${order.product}`}
                              </td>

                              <td style={{ padding: 12, textAlign: 'center' }}>
                                {order.quantity}
                              </td>

                              <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                                {productMoney(order.unit_price)}
                              </td>

                              <td
                                style={{
                                  padding: 12,
                                  whiteSpace: 'nowrap',
                                  fontWeight: 600,
                                }}
                              >
                                {productMoney(order.total_amount)}
                              </td>

                              <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                                {productMoney(order.delivery_cost)}
                              </td>

                              <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                                <span
                                  style={{
                                    display: 'inline-block',
                                    padding: '5px 10px',
                                    borderRadius: 20,
                                    fontSize: 12,
                                    fontWeight: 600,
                                    background: statusStyle.background,
                                    color: statusStyle.color,
                                  }}
                                >
                                  {getStatusLabel(order.status)}
                                </span>
                              </td>

                              <td style={{ padding: 12, whiteSpace: 'nowrap' }}>
                                {formatDate(order.created_at)}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </section>
        )}

        {/* PAGE DASHBOARD */}
        {currentPage === 'dashboard' && (
          <>
            {dashboardLoading && (
              <section style={{ padding: 24 }}>
                <p>
                  {isArabic ? 'جارٍ تحميل البيانات...' : 'Chargement des données...'}
                </p>
              </section>
            )}

            {dashboardError && (
              <section className="panel" style={{ padding: 24 }}>
                <p role="alert">{dashboardError}</p>
                <button
                  type="button"
                  className="period-select"
                  onClick={() => setRefreshKey((value) => value + 1)}
                >
                  <RefreshCw size={16} />
                  {isArabic ? 'إعادة المحاولة' : 'Réessayer'}
                </button>
              </section>
            )}

            {!dashboardLoading && dashboard && (
              <>
                <section className="page-heading">
                  <div>
                    <div className="eyebrow">
                      {isArabic
                        ? 'نظرة عامة على نشاطك'
                        : 'VUE GÉNÉRALE DE VOTRE ACTIVITÉ'}
                    </div>
                    <h1>{t('dashboard')}</h1>
                    <p>
                      {isArabic
                        ? 'تابع أداء متجرك وافهم أين تذهب أموالك.'
                        : 'Suivez les performances de votre boutique et comprenez vos coûts.'}
                    </p>
                  </div>

                  <div className="period-select">
                    <span className="period-dot" />
                    {isArabic ? 'هذا الشهر' : 'Ce mois-ci'}
                  </div>
                </section>

                <div className="demo-notice">
                  <span className="notice-icon">i</span>
                  <span>{t('demoNotice')}</span>
                </div>

                <section className="metrics-grid">
                  <article className="metric-card profit-card">
                    <div className="metric-top">
                      <span className="metric-label">{t('profit')}</span>
                      <span className="metric-icon profit-icon">
                        <CircleDollarSign size={21} />
                      </span>
                    </div>
                    <div className="metric-value">{money(dashboard.profit)}</div>
                    <div className="metric-foot">
                      <span className="trend positive">
                        <ArrowUpRight size={15} /> 12.8%
                      </span>
                      <span>
                        {isArabic ? 'مقارنة بالشهر الماضي' : 'vs mois précédent'}
                      </span>
                    </div>
                  </article>

                  <article className="metric-card">
                    <div className="metric-top">
                      <span className="metric-label">{t('sales')}</span>
                      <span className="metric-icon sales-icon">
                        <TrendingUp size={21} />
                      </span>
                    </div>
                    <div className="metric-value">{money(dashboard.sales)}</div>
                    <div className="metric-foot">
                      <span className="trend positive">
                        <ArrowUpRight size={15} /> 8.2%
                      </span>
                      <span>
                        {isArabic ? 'مقارنة بالشهر الماضي' : 'vs mois précédent'}
                      </span>
                    </div>
                  </article>

                  <article className="metric-card">
                    <div className="metric-top">
                      <span className="metric-label">{t('adSpend')}</span>
                      <span className="metric-icon ads-icon">
                        <Megaphone size={21} />
                      </span>
                    </div>
                    <div className="metric-value">{money(dashboard.adSpend)}</div>
                    <div className="metric-foot">
                      <span className="trend negative">
                        <ArrowDownRight size={15} /> 3.4%
                      </span>
                      <span>
                        {isArabic ? 'مقارنة بالشهر الماضي' : 'vs mois précédent'}
                      </span>
                    </div>
                  </article>

                  <article className="metric-card">
                    <div className="metric-top">
                      <span className="metric-label">{t('deliveryCosts')}</span>
                      <span className="metric-icon delivery-icon">
                        <Truck size={21} />
                      </span>
                    </div>
                    <div className="metric-value">
                      {money(dashboard.deliveryCosts)}
                    </div>
                    <div className="metric-foot">
                      <span className="trend neutral">—</span>
                      <span>
                        {isArabic
                          ? 'إجمالي تكاليف التوصيل'
                          : 'Total des livraisons'}
                      </span>
                    </div>
                  </article>
                </section>

                <section className="dashboard-grid">
                  <article className="panel chart-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>
                          {isArabic ? 'تطور المبيعات' : 'Évolution des ventes'}
                        </h2>
                        <p>
                          {isArabic ? 'المبيعات خلال الشهر' : 'Ventes au cours du mois'}
                        </p>
                      </div>
                      <span className="chart-legend">
                        <span className="legend-dot" />
                        {t('sales')}
                      </span>
                    </div>

                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                          data={salesData}
                          margin={{ top: 12, right: 8, left: 4, bottom: 0 }}
                        >
                          <defs>
                            <linearGradient
                              id="salesGradient"
                              x1="0"
                              y1="0"
                              x2="0"
                              y2="1"
                            >
                              <stop
                                offset="0%"
                                stopColor="#4976ed"
                                stopOpacity={0.22}
                              />
                              <stop
                                offset="95%"
                                stopColor="#4976ed"
                                stopOpacity={0}
                              />
                            </linearGradient>
                          </defs>

                          <CartesianGrid stroke="#edf0f5" vertical={false} />
                          <XAxis
                            dataKey="day"
                            tickLine={false}
                            axisLine={false}
                            tick={{ fill: '#8992a5', fontSize: 11 }}
                            tickMargin={12}
                          />
                          <YAxis
                            orientation={isArabic ? 'right' : 'left'}
                            tickLine={false}
                            axisLine={false}
                            tick={{ fill: '#8992a5', fontSize: 11 }}
                            tickFormatter={(value: number) => `${value / 1000}k`}
                            width={42}
                          />
                          <Tooltip
                            formatter={(value) => [money(Number(value)), t('sales')]}
                            labelFormatter={(label) =>
                              isArabic ? `اليوم ${label}` : `Jour ${label}`
                            }
                          />
                          <Area
                            type="monotone"
                            dataKey="sales"
                            stroke="#4976ed"
                            strokeWidth={2.5}
                            fill="url(#salesGradient)"
                            activeDot={{ r: 5, strokeWidth: 0 }}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </article>

                  <article className="panel breakdown-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>
                          {isArabic ? 'ملخص المصاريف' : 'Résumé des dépenses'}
                        </h2>
                        <p>
                          {isArabic ? 'التكاليف المسجلة' : 'Coûts enregistrés'}
                        </p>
                      </div>
                      <span className="breakdown-total">{money(totalCosts)}</span>
                    </div>

                    <div className="expense-row">
                      <span className="expense-icon ads-icon">
                        <Megaphone size={17} />
                      </span>
                      <div className="expense-info">
                        <div className="expense-label">{t('adSpend')}</div>
                        <div className="expense-track">
                          <span
                            className="bar ads-bar"
                            style={{
                              width: `${totalCosts
                                  ? (dashboard.adSpend / totalCosts) * 100
                                  : 0
                                }%`,
                            }}
                          />
                        </div>
                      </div>
                      <strong>{money(dashboard.adSpend)}</strong>
                    </div>

                    <div className="expense-row">
                      <span className="expense-icon delivery-icon">
                        <Truck size={17} />
                      </span>
                      <div className="expense-info">
                        <div className="expense-label">{t('deliveryCosts')}</div>
                        <div className="expense-track">
                          <span
                            className="bar delivery-bar"
                            style={{
                              width: `${totalCosts
                                  ? (dashboard.deliveryCosts / totalCosts) * 100
                                  : 0
                                }%`,
                            }}
                          />
                        </div>
                      </div>
                      <strong>{money(dashboard.deliveryCosts)}</strong>
                    </div>

                    <div className="cost-note">
                      <CircleDollarSign size={19} />
                      <p>
                        {isArabic
                          ? 'أضف تكلفة شراء المنتجات والتغليف والطلبات المرفوضة للحصول على ربح أدق.'
                          : 'Ajoutez les coûts d’achat, d’emballage et des commandes refusées pour estimer votre bénéfice plus précisément.'}
                      </p>
                    </div>
                  </article>
                </section>

                <footer className="page-footer">
                  <span>AI E-commerce Copilot</span>
                  <span>
                    {isArabic
                      ? 'مصمم للتجارة الإلكترونية الجزائرية'
                      : 'Pensé pour le e-commerce algérien'}
                  </span>
                </footer>
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
