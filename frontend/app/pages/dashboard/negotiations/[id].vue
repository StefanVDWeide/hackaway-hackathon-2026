<script setup lang="ts">
import type { BidRead, ConversationRead, CounterBidCreate, ListingRead, MessageRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: true, layout: 'dashboard' })

const route = useRoute()
const router = useRouter()
const { apiFetch } = useApi()
const { data } = useAuth()

const conversation = ref<ConversationRead | null>(null)
const listing = ref<ListingRead | null>(null)
const loading = ref(true)

// Counter bid
const showCounter = ref(false)
const counterTargetBid = ref<BidRead | null>(null)
const counterAmount = ref('')
const counterLat = ref('')
const counterLng = ref('')
const counterAt = ref('')
const counterLoading = ref(false)

const sellerId = computed(() => listing.value?.seller_id)

onMounted(() => refresh())

async function refresh() {
  try {
    conversation.value = await apiFetch<ConversationRead>(`/api/negotiations/conversations/${route.params.id}`)
    listing.value = await apiFetch<ListingRead>(`/api/listings/${conversation.value.listing_id}`)
  }
  catch { toast.error('Could not load conversation') }
  finally { loading.value = false }
}

function handleMessageSent(msg: MessageRead) {
  conversation.value?.messages.push(msg)
}

function handleBidAction() {
  refresh()
}

function openCounter(bid: BidRead) {
  counterTargetBid.value = bid
  counterAmount.value = String(bid.amount / 100)
  counterLat.value = String(bid.pickup_latitude)
  counterLng.value = String(bid.pickup_longitude)
  counterAt.value = bid.pickup_at.slice(0, 16)
  showCounter.value = true
}

async function submitCounter() {
  if (!counterTargetBid.value) return
  counterLoading.value = true
  try {
    const body: CounterBidCreate = {
      amount: Math.round(parseFloat(counterAmount.value) * 100),
      pickup_latitude: parseFloat(counterLat.value),
      pickup_longitude: parseFloat(counterLng.value),
      pickup_at: new Date(counterAt.value).toISOString(),
    }
    await apiFetch(`/api/negotiations/bids/${counterTargetBid.value.id}/counter`, { method: 'POST', body })
    toast.success('Counter offer sent!')
    showCounter.value = false
    await refresh()
  }
  catch { toast.error('Could not send counter offer') }
  finally { counterLoading.value = false }
}

function handleAccepted(transactionId: string) {
  toast.success('Bid accepted! Redirecting to transaction...')
  router.push(`/dashboard/transactions/${transactionId}`)
}
</script>

<template>
  <div class="h-[calc(100vh-8rem)] flex flex-col space-y-0 -m-6">
    <!-- Header -->
    <div class="px-6 py-4 border-b flex items-center gap-4 shrink-0">
      <Button variant="ghost" size="sm" as-child>
        <NuxtLink to="/dashboard/negotiations">← Back</NuxtLink>
      </Button>
      <div v-if="listing" class="flex items-center gap-3 min-w-0">
        <div class="h-10 w-10 rounded-md bg-muted overflow-hidden shrink-0">
          <img
            v-if="listing.image_url"
            :src="listing.image_url"
            :alt="listing.title"
            class="w-full h-full object-cover"
          >
        </div>
        <div class="min-w-0">
          <p class="font-semibold text-sm line-clamp-1">{{ listing.title }}</p>
          <p class="text-xs text-muted-foreground">
            {{ conversation?.buyer_id === data?.id ? 'Buying from ' : 'Selling to ' }}
            {{ conversation?.buyer_id === data?.id ? listing.seller_display_name : 'buyer' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-muted-foreground">
      Loading conversation...
    </div>

    <!-- Thread -->
    <div v-else-if="conversation" class="flex-1 min-h-0">
      <NegotiationsMessageThread
        :conversation-id="conversation.id"
        :messages="conversation.messages"
        :current-user-id="data?.id"
        :seller-id="sellerId"
        @message-sent="handleMessageSent"
        @bid-action="handleBidAction"
      />
    </div>

    <!-- Counter bid dialog -->
    <Dialog :open="showCounter" @update:open="showCounter = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send Counter Offer</DialogTitle>
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
