export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  phone?: string
  date_of_birth?: string
  newsletter_subscription: boolean
  created_at: string
}

export interface Address {
  id: number
  address_type: 'shipping' | 'billing'
  street_address: string
  apartment?: string
  city: string
  state: string
  postal_code: string
  country: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  name: string
  description: string
  image?: string
  is_active: boolean
  products_count: number
  created_at: string
  updated_at: string
}

export interface FilterOptions {
  categories: Category[]
  materials: string[]
  priceRange: {
    min: number
    max: number
  }
  ratings: number[]
}

export interface Product {
  id: number
  name: string
  price: string
  category_name: string
  main_image?: string
  is_in_stock: boolean
  stock_quantity: number
  average_rating: number
  review_count: number
}

export interface ProductDetail extends Product {
  description: string
  category: Category
  sku: string
  stock_quantity: number
  weight: string
  dimensions: string
  material: string
  print_time: number
  images: ProductImage[]
  reviews: ProductReview[]
  created_at: string
  updated_at: string
}

export interface ProductImage {
  id: number
  image: string
  alt_text: string
  is_main: boolean
  created_at: string
}

export interface ProductReview {
  id: number
  user_name: string
  rating: number
  review_text: string
  is_verified_purchase: boolean
  created_at: string
  updated_at: string
}

export interface CartItem {
  id: number
  product: Product
  quantity: number
  total_price: string
  total_weight: string
  created_at: string
  updated_at: string
}

export interface Cart {
  id: number
  items: CartItem[]
  total_items: number
  total_price: string
  total_weight: string
  created_at: string
  updated_at: string
}

export interface ApiResponse<T> {
  count?: number
  next?: string | null
  previous?: string | null
  results: T[]
}

export interface ApiError {
  message: string
  status?: number
  errors?: Record<string, string[]>
}

export interface WishlistItem {
  id: number
  product: Product
  added_at: string
}

export interface Wishlist {
  id: number
  items: WishlistItem[]
  total_items: number
  created_at: string
  updated_at: string
}

// Admin Types
export interface AdminUser extends User {
  is_staff: boolean
  is_superuser: boolean
  last_login?: string
}

export interface Order {
  id: number
  order_number: string
  user: User
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded'
  payment_method: string
  items: OrderItem[]
  shipping_address: Address
  billing_address: Address
  subtotal: string
  tax_amount: string
  shipping_cost: string
  total_amount: string
  tracking_number?: string
  goshippo_order_id?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface OrderItem {
  id: number
  product: Product
  quantity: number
  price: string
  total_price: string
}

export interface DashboardStats {
  total_revenue: number
  total_orders: number
  total_products: number
  total_users: number
  pending_orders: number
  low_stock_products: number
  revenue_change: number
  orders_change: number
  users_change: number
  products_change: number
}

export interface RevenueData {
  date: string
  revenue: number
  orders: number
}

export interface CategoryStats {
  name: string
  sales: number
  revenue: number
  percentage: number
}

export interface ProductStats {
  product: Product
  quantity_sold: number
  revenue: number
  stock_level: number
}

export interface UserActivity {
  date: string
  new_users: number
  active_users: number
  orders: number
}

export interface ReportFilters {
  start_date: string
  end_date: string
  category_id?: number
  product_id?: number
  status?: string
  payment_status?: string
}

// Removed unused types for unimplemented features:
// - Social authentication types (OAuth/Social Login not implemented)
// - Review types (Review system not implemented)
// - Referral types (Referral system not implemented)
// - Notification types (Notification system not implemented)
// - Social sharing types (Social sharing not implemented)