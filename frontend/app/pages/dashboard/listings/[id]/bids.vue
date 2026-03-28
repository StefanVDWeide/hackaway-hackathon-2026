<script setup lang="ts">
import type { BidRead, CounterBidCreate, ListingRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: true, layout: 'dashboard' })

const route = useRoute()
const { apiFetch } = useApi()
const { data } = useAuth()

const listing = ref<ListingRead | null>(null)
const bids = ref<BidRead[]>([])
const loading = ref(true)

// Counter bid dialog
const showCounter = ref(false)
const counterBid = ref<BidRead | null>(null)
const counterAmount = ref('')
const counterLat = ref('')
const counterLng = ref('')
const counterAt = ref('')
const counterLoading = ref(false)

onMounted(async () => {
  await refresh()
})

async function refresh() {
  loading.value = true
  try {
    const [l, b] = await Promise.all([
      apiFetch<ListingRead>(`/api/listings/${route.params.id}`),
      apiFetch<BidRead[]>(`/api/negotiations/listings/${route.params.id}/bids`),
    ])
    listing.value = l
    bids.value = b
  }
  catch { toast.error('Could not load bids') }
  finally { loading.value = false }
}

function openCounter(bid: BidRead) {
  counterBid.value = bid
  counterAmount.value = String(bid.amount / 100)
  counterLat.value = String(bid.pickup_latitude)
  counterLng.value = String(bid.pickup_longitude)
  counterAt.value = bid.pickup_at.slice(0, 16)
  showCounter.value = true
}

async function submitCounter() {
  if (!counterBid.value) return
  counterLoading.value = true
  try {
    const body: CounterBidCreate = {
      amount: Math.round(parseFloat(counterAmount.value) * 100),
      pickup_latitude: parseFloat(counterLat.value),
      pickup_longitude: parseFloat(counterLng.value),
      pickup_at: new Date(counterAt.value).toISOString(),
    }
    await apiFetch(`/api/negotiations/bids/${counterBid.value.id}/counter`, { method: 'POST', body })
    toast.success('Counter offer sent!')
    showCounter.value = false
    await refresh()
  }
  catch { toast.error('Could not send counter offer') }
  finally { counterLoading.value = false }
}

const pendingBids = computed(() => bids.value.filter(b => b.status === 'pending'))
const otherBids = computed(() => bids.value.filter(b => b.status !== 'pending'))
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="sm" as-child>
        <NuxtLink to="/dashboard/listings">← Back</NuxtLink>
      </Button>
      <div>
        <h1 class="text-2xl font-bold">Bids</h1>
        <p v-if="listing" class="text-muted-foreground text-sm">{{ listing.title }}</p>
      </div>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 3" :key="i" class="h-28 rounded-lg" />
    </div>

    <div v-else class="space-y-6">
      <!-- Pending bids -->
      <div v-if="pendingBids.length">
        <h2 class="font-semibold mb-3">Pending ({{ pendingBids.length }})</h2>
        <div class="space-y-3">
          <NegotiationsBidCard
            v-for="bid in pendingBids"
            :key="bid.id"
            :bid="bid"
            :current-user-id="data?.id"
            :seller-id="data?.id"
            show-actions
            @accepted="refresh"
            @rejected="refresh"
            @countered="openCounter"
          />
        </div>
      </div>

      <!-- Other bids -->
      <div v-if="otherBids.length">
        <h2 class="font-semibold mb-3">History</h2>
        <div class="space-y-3">
          <NegotiationsBidCard
            v-for="bid in otherBids"
            :key="bid.id"
            :bid="bid"
          />
        </div>
      </div>

      <div v-if="bids.length === 0" class="text-center py-16 text-muted-foreground">
        No bids received yet
      </div>
    </div>

    <!-- Counter bid dialog -->
    <Dialog :open="showCounter" @update:open="showCounter = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send Counter Offer</DialogTitle>
          <DialogDescription>Propose new terms to the buyer</DialogDescription>
        </DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1.5">
            <Label>Counter amount (€)</Label>
            <Input v-model="counterAmount" type="number" min="0.01" step="0.01" />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="space-y-1.5">
              <Label>Pickup latitude</Label>
              <Input v-model="counterLat" type="number" step="any" />
            </div>
            <div class="space-y-1.5">
              <Label>Pickup longitude</Label>
              <Input v-model="counterLng" type="number" step="any" />
            </div>
          </div>
          <div class="space-y-1.5">
            <Label>Pickup date & time</Label>
            <Input v-model="counterAt" type="datetime-local" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showCounter = false">Cancel</Button>
          <Button :disabled="counterLoading" @click="submitCounter">
            {{ counterLoading ? 'Sending...' : 'Send Counter' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
