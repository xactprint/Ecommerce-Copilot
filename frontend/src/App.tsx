
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Megaphone,
  BrainCircuit,
  TrendingUp,
  TrendingDown,
  Truck,
  CircleDollarSign,
  Languages,
  ArrowUpRight,
  ArrowDownRight,
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
  const language = i18n.resolvedLanguage === 'fr' ? 'fr' : 'ar'
  const isArabic = language === 'ar'

  useEffect(() => {
    document.documentElement.lang = language
    document.documentElement.dir = isArabic ? 'rtl' : 'ltr'
  }, [language, isArabic])

  const changeLanguage = (nextLanguage: 'ar' | 'fr') => {
    void i18n.changeLanguage(nextLanguage)
  }

  const money = (value: number) =>
    new Intl.NumberFormat(language === 'ar' ? 'ar-DZ' : 'fr-DZ', {
      style: 'currency',
      currency: 'DZD',
      maximumFractionDigits: 0,
    }).format(value)

  const menu = [
    { label: t('dashboard'), icon: LayoutDashboard, active: true },
    { label: t('products'), icon: Package, active: false },
    { label: t('orders'), icon: ShoppingCart, active: false },
    { label: t('advertising'), icon: Megaphone, active: false },
  ]

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
          {menu.map(({ label, icon: Icon, active }) => (
            <button
              className={`nav-item ${active ? 'active' : ''}`}
              key={label}
              type="button"
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
            <span>
              {isArabic ? 'قريبًا' : 'BIENTÔT'}
            </span>
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
            <strong>{t('dashboard')}</strong>
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

        <section className="page-heading">
          <div>
            <div className="eyebrow">
              {isArabic ? 'نظرة عامة على نشاطك' : 'VUE GÉNÉRALE DE VOTRE ACTIVITÉ'}
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
            <div className="metric-value">{money(84500)}</div>
            <div className="metric-foot">
              <span className="trend positive">
                <ArrowUpRight size={15} /> 12.8%
              </span>
              <span>{isArabic ? 'مقارنة بالشهر الماضي' : 'vs mois précédent'}</span>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span className="metric-label">{t('sales')}</span>
              <span className="metric-icon sales-icon">
                <TrendingUp size={21} />
              </span>
            </div>
            <div className="metric-value">{money(245000)}</div>
            <div className="metric-foot">
              <span className="trend positive">
                <ArrowUpRight size={15} /> 8.2%
              </span>
              <span>{isArabic ? 'مقارنة بالشهر الماضي' : 'vs mois précédent'}</span>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span className="metric-label">{t('adSpend')}</span>
              <span className="metric-icon ads-icon">
                <Megaphone size={21} />
              </span>
            </div>
            <div className="metric-value">{money(42000)}</div>
            <div className="metric-foot">
              <span className="trend negative">
                <ArrowDownRight size={15} /> 3.4%
              </span>
              <span>{isArabic ? 'مقارنة بالشهر الماضي' : 'vs mois précédent'}</span>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span className="metric-label">{t('deliveryCosts')}</span>
              <span className="metric-icon delivery-icon">
                <Truck size={21} />
              </span>
            </div>
            <div className="metric-value">{money(18500)}</div>
            <div className="metric-foot">
              <span className="trend neutral">—</span>
              <span>{isArabic ? 'إجمالي تكاليف التوصيل' : 'Total des livraisons'}</span>
            </div>
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>{isArabic ? 'تطور المبيعات' : 'Évolution des ventes'}</h2>
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
                    <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4976ed" stopOpacity={0.22} />
                      <stop offset="95%" stopColor="#4976ed" stopOpacity={0} />
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
                <h2>{isArabic ? 'ملخص المصاريف' : 'Résumé des dépenses'}</h2>
                <p>
                  {isArabic ? 'التكاليف المسجلة' : 'Coûts enregistrés'}
                </p>
              </div>
              <span className="breakdown-total">{money(60500)}</span>
            </div>

            <div className="expense-row">
              <span className="expense-icon ads-icon"><Megaphone size={17} /></span>
              <div className="expense-info">
                <div className="expense-label">{t('adSpend')}</div>
                <div className="expense-track">
                  <span className="bar ads-bar" style={{ width: '69.4%' }} />
                </div>
              </div>
              <strong>{money(42000)}</strong>
            </div>

            <div className="expense-row">
              <span className="expense-icon delivery-icon"><Truck size={17} /></span>
              <div className="expense-info">
                <div className="expense-label">{t('deliveryCosts')}</div>
                <div className="expense-track">
                  <span className="bar delivery-bar" style={{ width: '30.6%' }} />
                </div>
              </div>
              <strong>{money(18500)}</strong>
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
            {isArabic ? 'مصمم للتجارة الإلكترونية الجزائرية' : 'Pensé pour le e-commerce algérien'}
          </span>
        </footer>
      </main>
    </div>
  )
}

export default App
