<script setup lang="ts">
import type { BidRead, ListingRead, WalletRead } from '~/types/api'

definePageMeta({ auth: true, layout: 'dashboard' })

const { apiFetch } = useApi()
const { data } = useAuth()

const wallet = ref<WalletRead | null>(null)
const myListings = ref<ListingRead[]>([])
const myBids = ref<BidRead[]>([])
const loading = ref(true)

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

onMounted(async () => {
  const [w, l, b] = await Promise.allSettled([
    apiFetch<WalletRead>('/api/transactions/wallet'),
    apiFetch<ListingRead[]>('/api/listings/me?limit=100'),
    apiFetch<BidRead[]>('/api/negotiations/me/bids?limit=100'),
  ])
  if (w.status === 'fulfilled') wallet.value = w.value
  if (l.status === 'fulfilled') myListings.value = l.value
  if (b.status === 'fulfilled') myBids.value = b.value
  loading.value = false
})

const activeListings = computed(() => myListings.value.filter(l => l.status === 'active').length)
const draftListings = computed(() => myListings.value.filter(l => l.status === 'draft').length)
const pendingBids = computed(() => myBids.value.filter(b => b.status === 'pending').length)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Welcome back, {{ data?.display_name }}</h1>
      <p class="text-muted-foreground text-sm mt-1">Here's what's happening with your marketplace activity</p>
    </div>

    <!-- Stat cards -->
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Skeleton v-for="i in 4" :key="i" class="h-28 rounded-lg" />
    </div>

    <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader class="pb-2">
          <CardDescription>Available Balance</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold text-primary">{{ wallet ? formatPrice(wallet.balance) : '—' }}</p>
          <p v-if="wallet?.held_balance" class="text-xs text-muted-foreground mt-1">
            {{ formatPrice(wallet.held_balance) }} in escrow
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader class="pb-2">
          <CardDescription>Active Listings</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold">{{ activeListings }}</p>
          <p class="text-xs text-muted-foreground mt-1">{{ draftListings }} drafts</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader class="pb-2">
          <CardDescription>Pending Bids</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold">{{ pendingBids }}</p>
          <p class="text-xs text-muted-foreground mt-1">{{ myBids.length }} total</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader class="pb-2">
          <CardDescription>Total Listings</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-2xl font-bold">{{ myListings.length }}</p>
        </CardContent>
      </Card>
    </div>

    <!-- Quick links -->
    <div class="grid md:grid-cols-3 gap-4">
      <NuxtLink to="/dashboard/listings/new" class="block group">
        <Card class="hover:shadow-md transition-shadow cursor-pointer h-full">
          <CardContent class="pt-6 flex flex-col items-center text-center gap-2">
            <div class="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl">+</div>
            <p class="font-semibold">Create Listing</p>
            <p class="text-xs text-muted-foreground">List an item for sale</p>
          </CardContent>
        </Card>
      </NuxtLink>
      <NuxtLink to="/dashboard/negotiations" class="block group">
        <Card class="hover:shadow-md transition-shadow cursor-pointer h-full">
          <CardContent class="pt-6 flex flex-col items-center text-center gap-2">
            <div class="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl">💬</div>
            <p class="font-semibold">Negotiations</p>
            <p class="text-xs text-muted-foreground">Manage conversations & bids</p>
          </CardContent>
        </Card>
      </NuxtLink>
      <NuxtLink to="/dashboard/wallet" class="block group">
        <Card class="hover:shadow-md transition-shadow cursor-pointer h-full">
          <CardContent class="pt-6 flex flex-col items-center text-center gap-2">
            <div class="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl">💳</div>
            <p class="font-semibold">Wallet</p>
            <p class="text-xs text-muted-foreground">Balance & transactions</p>
          </CardContent>
        </Card>
      </NuxtLink>
    </div>
  </div>
</template>
