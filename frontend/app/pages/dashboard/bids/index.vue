<script setup lang="ts">
import type { BidRead, ListingRead } from '~/types/api'

definePageMeta({ auth: true, layout: 'dashboard' })

const { apiFetch } = useApi()
const bids = ref<BidRead[]>([])
const listingMap = ref<Record<string, ListingRead>>({})
const loading = ref(true)

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('nl-NL', { dateStyle: 'medium' })
}

const statusColor: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  countered: 'bg-blue-100 text-blue-800',
  expired: 'bg-gray-100 text-gray-600',
}

onMounted(async () => {
  bids.value = await apiFetch<BidRead[]>('/api/negotiations/me/bids?limit=100')

  const ids = [...new Set(bids.value.map(b => b.listing_id))]
  await Promise.all(ids.map(async (id) => {
    try { listingMap.value[id] = await apiFetch<ListingRead>(`/api/listings/${id}`) }
    catch { /* ignore */ }
  }))
  loading.value = false
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">My Bids</h1>

    <div v-if="loading" class="space-y-2">
      <Skeleton v-for="i in 4" :key="i" class="h-20 rounded-lg" />
    </div>

    <div v-else-if="bids.length === 0" class="text-center py-16 text-muted-foreground">
      <p>No bids placed yet</p>
      <Button class="mt-4" as-child>
        <NuxtLink to="/">Browse listings</NuxtLink>
      </Button>
    </div>

    <div v-else class="border rounded-lg overflow-hidden divide-y">
      <div
        v-for="bid in bids"
        :key="bid.id"
        class="flex items-center gap-4 px-4 py-4"
      >
        <!-- Listing image -->
        <div class="h-12 w-12 rounded-md bg-muted overflow-hidden shrink-0">
          <img
            v-if="listingMap[bid.listing_id]?.image_url"
            :src="listingMap[bid.listing_id].image_url!"
            class="w-full h-full object-cover"
          >
        </div>

        <div class="flex-1 min-w-0">
          <NuxtLink :to="`/listings/${bid.listing_id}`" class="font-medium hover:text-primary line-clamp-1">
            {{ listingMap[bid.listing_id]?.title ?? 'Listing' }}
          </NuxtLink>
          <p class="text-sm text-muted-foreground">
            Offer: <span class="font-medium text-foreground">{{ formatPrice(bid.amount) }}</span>
            · Pickup: {{ formatDate(bid.pickup_at) }}
          </p>
        </div>

        <div class="flex flex-col items-end gap-1 shrink-0">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusColor[bid.status]">
            {{ bid.status }}
          </span>
          <span class="text-xs text-muted-foreground">{{ formatDate(bid.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
