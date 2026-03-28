// ─── Enums ────────────────────────────────────────────────────────────────────

export type Condition = 'new' | 'like_new' | 'good' | 'fair' | 'poor'
export type ListingStatus = 'draft' | 'active' | 'sold' | 'archived'
export type BidStatus = 'pending' | 'accepted' | 'rejected' | 'countered' | 'expired'
export type BidType = 'buyer' | 'seller'
export type ActorType = 'user' | 'agent'
export type TransactionStatus = 'pending_escrow' | 'escrowed' | 'released' | 'refunded' | 'disputed'

// ─── Users ────────────────────────────────────────────────────────────────────

export interface UserRead {
  id: string
  created_at: string
  updated_at: string
  email: string
  display_name: string
  latitude: number | null
  longitude: number | null
  is_active: boolean
  is_verified: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ─── Categories ───────────────────────────────────────────────────────────────

export interface CategoryRead {
  id: string
  created_at: string
  updated_at: string
  name: string
  slug: string
  parent_id: string | null
}

// ─── Listings ─────────────────────────────────────────────────────────────────

export interface ListingRead {
  id: string
  created_at: string
  updated_at: string
  seller_id: string
  seller_display_name: string
  title: string
  description: string
  price: number
  condition: Condition
  status: ListingStatus
  image_url: string | null
  categories: CategoryRead[]
}

export interface ListingSearchResult {
  listing: ListingRead
  score: number
}

export interface ListingCreate {
  title: string
  description: string
  price: number
  condition: Condition
  image_url?: string | null
  category_ids?: string[]
}

export interface ListingUpdate {
  title?: string
  description?: string
  price?: number
  condition?: Condition
  image_url?: string | null
  category_ids?: string[]
}

export interface ListingFilters {
  category_slug?: string
  condition?: Condition
  min_price?: number
  max_price?: number
  latitude?: number
  longitude?: number
  radius_km?: number
  offset?: number
  limit?: number
}

// ─── Negotiations ─────────────────────────────────────────────────────────────

export interface BidRead {
  id: string
  created_at: string
  updated_at: string
  listing_id: string
  bidder_id: string
  amount: number
  pickup_latitude: number
  pickup_longitude: number
  pickup_at: string
  status: BidStatus
  bid_type: BidType
  parent_bid_id: string | null
}

export interface BidCreate {
  listing_id: string
  amount: number
  pickup_latitude: number
  pickup_longitude: number
  pickup_at: string
}

export interface CounterBidCreate {
  amount: number
  pickup_latitude: number
  pickup_longitude: number
  pickup_at: string
}

export interface MessageRead {
  id: string
  created_at: string
  updated_at: string
  conversation_id: string
  actor_type: ActorType
  sender_id: string | null
  body: string
  bid_id: string | null
  bid: BidRead | null
}

export interface ConversationSummary {
  id: string
  created_at: string
  updated_at: string
  listing_id: string
  buyer_id: string
}

export interface ConversationRead {
  id: string
  created_at: string
  updated_at: string
  listing_id: string
  buyer_id: string
  messages: MessageRead[]
}

// ─── Transactions ─────────────────────────────────────────────────────────────

export interface TransactionRead {
  id: string
  created_at: string
  updated_at: string
  bid_id: string
  buyer_id: string
  seller_id: string
  amount: number
  pickup_latitude: number
  pickup_longitude: number
  pickup_at: string
  status: TransactionStatus
  escrowed_at: string | null
  released_at: string | null
  refunded_at: string | null
  picked_up_at: string | null
}

export interface WalletRead {
  id: string
  created_at: string
  updated_at: string
  user_id: string
  balance: number
  held_balance: number
}
