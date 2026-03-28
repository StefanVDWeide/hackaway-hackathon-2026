<script setup lang="ts">
import type { BidCreate, ListingRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: false, layout: 'default' })

const route = useRoute()
const router = useRouter()
const { apiFetch } = useApi()
const { status, data } = useAuth()

const listing = ref<ListingRead | null>(null)
const loading = ref(true)
const notFound = ref(false)

// Bid form
const showBidForm = ref(false)
const bidAmount = ref('')
const bidLoading = ref(false)

const isAuthenticated = computed(() => status.value === 'authenticated')
const isOwner = computed(() => data.value?.id === listing.value?.seller_id)
const canBid = computed(() => isAuthenticated.value && !isOwner.value && listing.value?.status === 'active')

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('nl-NL', { dateStyle: 'long' })
}

const conditionLabel: Record<string, string> = {
  new: 'New', like_new: 'Like New', good: 'Good', fair: 'Fair', poor: 'Poor',
}

onMounted(async () => {
  try {
    listing.value = await apiFetch<ListingRead>(`/api/listings/${route.params.id}`)
  }
  catch {
    notFound.value = true
  }
  finally {
    loading.value = false
  }
})

async function submitBid() {
  if (!listing.value) return
  bidLoading.value = true
  try {
    const body: BidCreate = {
      listing_id: listing.value.id,
      amount: Math.round(parseFloat(bidAmount.value) * 100),
    }
    await apiFetch('/api/negotiations/bids', { method: 'POST', body })
    toast.success('Bid placed! Check your negotiations.')
    showBidForm.value = false
    router.push('/dashboard/negotiations')
  }
  catch (e: unknown) {
    const msg = (e as { data?: { detail?: string } })?.data?.detail ?? 'Could not place bid'
    toast.error(msg)
  }
  finally { bidLoading.value = false }
}
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Loading -->
    <div v-if="loading" class="space-y-4 max-w-4xl mx-auto">
      <Skeleton class="h-96 rounded-xl w-full" />
      <Skeleton class="h-8 w-1/2" />
      <Skeleton class="h-4 w-1/4" />
    </div>

    <!-- Not found -->
    <div v-else-if="notFound" class="text-center py-20">
      <p class="text-xl font-semibold">Listing not found</p>
      <Button class="mt-4" as-child><NuxtLink to="/">Back to browse</NuxtLink></Button>
    </div>

    <!-- Listing detail -->
    <div v-else-if="listing" class="max-w-4xl mx-auto">
      <div class="grid md:grid-cols-2 gap-8">
        <!-- Image -->
        <div class="aspect-square rounded-xl overflow-hidden bg-muted">
          <img
            v-if="listing.image_url"
            :src="listing.image_url"
            :alt="listing.title"
            class="w-full h-full object-cover"
          >
          <div v-else class="w-full h-full flex items-center justify-center text-muted-foreground">
            <svg class="h-20 w-20 opacity-20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect width="18" height="18" x="3" y="3" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
          </div>
        </div>

        <!-- Info -->
        <div class="flex flex-col gap-4">
          <div>
            <div class="flex items-start gap-2 justify-between">
              <h1 class="text-2xl font-bold leading-tight">{{ listing.title }}</h1>
              <Badge variant="outline">{{ conditionLabel[listing.condition] }}</Badge>
            </div>
            <p class="text-3xl font-bold text-primary mt-2">{{ formatPrice(listing.price) }}</p>
          </div>

          <!-- Meta -->
          <div class="text-sm text-muted-foreground space-y-1">
            <p>Seller: <span class="text-foreground font-medium">{{ listing.seller_display_name }}</span></p>
            <p>Listed: {{ formatDate(listing.created_at) }}</p>
            <p v-if="listing.status !== 'active'">
              Status: <Badge variant="secondary" class="capitalize">{{ listing.status }}</Badge>
            </p>
          </div>

          <!-- Categories -->
          <div v-if="listing.categories.length" class="flex flex-wrap gap-1.5">
            <Badge v-for="cat in listing.categories" :key="cat.id" variant="outline">{{ cat.name }}</Badge>
          </div>

          <Separator />

          <!-- Description -->
          <div>
            <h2 class="font-semibold mb-2">Description</h2>
            <p class="text-sm text-muted-foreground whitespace-pre-line leading-relaxed">{{ listing.description }}</p>
          </div>

          <!-- Actions -->
          <div class="mt-auto space-y-2">
            <!-- Owner actions -->
            <template v-if="isOwner">
              <div class="flex gap-2">
                <Button variant="outline" class="flex-1" as-child>
                  <NuxtLink :to="`/dashboard/listings/${listing.id}/edit`">Edit Listing</NuxtLink>
                </Button>
                <Button class="flex-1" as-child>
                  <NuxtLink :to="`/dashboard/listings/${listing.id}/bids`">View Bids</NuxtLink>
                </Button>
              </div>
            </template>

            <!-- Buyer actions -->
            <template v-else-if="canBid">
              <Button class="w-full" @click="showBidForm = !showBidForm">
                {{ showBidForm ? 'Cancel' : 'Make an Offer' }}
              </Button>
            </template>

            <template v-else-if="!isAuthenticated">
              <Button class="w-full" as-child>
                <NuxtLink to="/login">Sign in to Make an Offer</NuxtLink>
              </Button>
            </template>

            <template v-else-if="listing.status !== 'active'">
              <p class="text-sm text-muted-foreground text-center">This listing is no longer available</p>
            </template>
          </div>

          <!-- Bid form -->
          <div v-if="showBidForm" class="border rounded-lg p-4 space-y-3 bg-muted/50">
            <h3 class="font-semibold text-sm">Your Offer</h3>
            <div class="space-y-1.5">
              <Label>Offer amount (€)</Label>
              <Input v-model="bidAmount" type="number" min="0.01" step="0.01" placeholder="0.00" />
            </div>
            <Button class="w-full" :disabled="bidLoading" @click="submitBid">
              {{ bidLoading ? 'Placing offer...' : 'Submit Offer' }}
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
