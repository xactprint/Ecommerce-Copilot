
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Package, RefreshCw } from 'lucide-react'
import type { Product } from './types'

function Products() {
    const { i18n } = useTranslation()
    const isArabic = i18n.resolvedLanguage !== 'fr'

    const [products, setProducts] = useState<Product[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const controller = new AbortController()

        async function fetchProducts() {
            try {
                setLoading(true)
                setError(null)

                const response = await fetch(
                    'http://127.0.0.1:8000/api/products/',
                    { signal: controller.signal }
                )

                if (!response.ok) {
                    throw new Error('Impossible de récupérer les produits.')
                }

                const data: Product[] = await response.json()
                setProducts(data)
            } catch (err) {
                if (err instanceof Error && err.name === 'AbortError') {
                    return
                }

                setError(
                    isArabic
                        ? 'تعذر تحميل المنتجات.'
                        : 'Impossible de charger les produits.'
                )
            } finally {
                if (!controller.signal.aborted) {
                    setLoading(false)
                }
            }
        }

        void fetchProducts()

        return () => controller.abort()
    }, [isArabic])

    const money = (value: string) =>
        new Intl.NumberFormat(isArabic ? 'ar-DZ' : 'fr-DZ', {
            style: 'currency',
            currency: 'DZD',
            maximumFractionDigits: 2,
        }).format(Number(value))

    return (
        <main style={{ padding: '24px' }}>
            <h1>
                <Package
                    size={28}
                    style={{ verticalAlign: 'middle', marginInlineEnd: 8 }}
                />
                {isArabic ? 'المنتجات' : 'Produits'}
            </h1>

            <p>
                {isArabic
                    ? 'المنتجات المسجلة في متجرك'
                    : 'Produits enregistrés dans votre boutique'}
            </p>

            {loading && (
                <p>{isArabic ? 'جارٍ التحميل...' : 'Chargement...'}</p>
            )}

            {error && (
                <div role="alert">
                    <p>{error}</p>
                    <button
                        type="button"
                        onClick={() => window.location.reload()}
                    >
                        <RefreshCw size={16} />{' '}
                        {isArabic ? 'إعادة المحاولة' : 'Réessayer'}
                    </button>
                </div>
            )}

            {!loading && !error && products.length === 0 && (
                <p>
                    {isArabic
                        ? 'لا توجد منتجات حتى الآن.'
                        : 'Aucun produit pour le moment.'}
                </p>
            )}

            {!loading && !error && products.length > 0 && (
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
                                <th style={{ padding: 12 }}>ID</th>
                                <th style={{ padding: 12 }}>
                                    {isArabic ? 'المنتج' : 'Produit'}
                                </th>
                                <th style={{ padding: 12 }}>
                                    {isArabic ? 'سعر الشراء' : "Prix d'achat"}
                                </th>
                                <th style={{ padding: 12 }}>
                                    {isArabic ? 'سعر البيع' : 'Prix de vente'}
                                </th>
                                <th style={{ padding: 12 }}>
                                    {isArabic ? 'المخزون' : 'Stock'}
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            {products.map((product) => (
                                <tr key={product.id}>
                                    <td style={{ padding: 12 }}>{product.id}</td>
                                    <td style={{ padding: 12 }}>{product.name}</td>
                                    <td style={{ padding: 12 }}>
                                        {money(product.purchase_price)}
                                    </td>
                                    <td style={{ padding: 12 }}>
                                        {money(product.selling_price)}
                                    </td>
                                    <td style={{ padding: 12 }}>
                                        {product.stock_quantity}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </main>
    )
}

export default Products
