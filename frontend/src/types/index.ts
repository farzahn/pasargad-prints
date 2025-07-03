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

export interface Product {
  id: number
  name: string
  price: string
  category_name: string
  main_image?: string
  is_in_stock: boolean
  is_featured: boolean
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