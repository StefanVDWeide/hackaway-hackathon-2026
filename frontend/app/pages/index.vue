<script setup lang="ts">
import type { CategoryRead, ListingFilters, ListingRead } from '~/types/api'

definePageMeta({ auth: false, layout: 'default' })

const { apiFetch } = useApi()

const listings = ref<ListingRead[]>([])
const categories = ref<CategoryRead[]>([])
const loading = ref(true)
const filters = ref<ListingFilters>({})
const hasActiveFilters = computed(() =>
  !!(filters.value.category_slug || filters.value.condition || filters.value.min_price != null || filters.value.max_price != null || filters.value.latitude),
)

const { status } = useAuth()
const isAuthenticated = computed(() => status.value === 'authenticated')

async function fetchListings() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.category_slug) params.set('category_slug', filters.value.category_slug)
    if (filters.value.condition) params.set('condition', filters.value.condition)
    if (filters.value.min_price != null) params.set('min_price', String(filters.value.min_price))
    if (filters.value.max_price != null) params.set('max_price', String(filters.value.max_price))
    if (filters.value.latitude != null) params.set('latitude', String(filters.value.latitude))
    if (filters.value.longitude != null) params.set('longitude', String(filters.value.longitude))
    if (filters.value.radius_km != null) params.set('radius_km', String(filters.value.radius_km))

    listings.value = await apiFetch<ListingRead[]>(`/api/listings/?${params}`)
  }
  catch { /* ignore */ }
  finally { loading.value = false }
}

onMounted(async () => {
  categories.value = await apiFetch<CategoryRead[]>('/api/categories/')
  await fetchListings()
})

function handleFilterChange(newFilters: ListingFilters) {
  filters.value = newFilters
  fetchListings()
}
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex gap-8">
      <!-- Filter sidebar -->
      <aside class="w-56 shrink-0 hidden md:block">
        <ListingsListingFilters :categories="categories" @change="handleFilterChange" />
      </aside>

      <!-- Listing grid -->
      <div class="flex-1">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold">Browse Listings</h1>
          <span class="text-sm text-muted-foreground">{{ listings.length }} items</span>
        </div>

        <!-- Loading skeletons -->
        <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div v-for="i in 8" :key="i" class="space-y-2">
            <Skeleton class="aspect-[4/3] rounded-lg w-full" />
            <Skeleton class="h-4 w-3/4" />
            <Skeleton class="h-4 w-1/2" />
          </div>
        </div>

        <!-- Empty state: filters active -->
        <div v-else-if="listings.length === 0 && hasActiveFilters" class="text-center py-20 text-muted-foreground">
          <div class="text-5xl mb-4">🔍</div>
          <p class="text-lg font-semibold">No listings match your filters</p>
          <p class="text-sm mt-1">Try widening your search or resetting the filters</p>
        </div>

        <!-- Empty state: no listings at all -->
        <div v-else-if="listings.length === 0" class="flex flex-col items-center py-24 gap-6 text-center">
          <div class="text-7xl">🏪</div>
          <div>
            <p class="text-2xl font-bold">The marketplace is empty</p>
            <p class="text-muted-foreground mt-2">Be the first to list something for sale!</p>
          </div>
          <div class="flex gap-3">
            <Button v-if="isAuthenticated" as-child size="lg">
              <NuxtLink to="/dashboard/listings/new">List an item</NuxtLink>
            </Button>
            <template v-else>
              <Button as-child size="lg">
                <NuxtLink to="/register">Get started</NuxtLink>
              </Button>
              <Button variant="outline" size="lg" as-child>
                <NuxtLink to="/login">Sign in</NuxtLink>
              </Button>
            </template>
          </div>
        </div>

        <!-- Grid -->
        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <ListingsListingCard v-for="listing in listings" :key="listing.id" :listing="listing" />
        </div>
      </div>
    </div>
  </div>
</template>
