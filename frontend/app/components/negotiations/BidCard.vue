<script setup lang="ts">
import type { BidRead } from '~/types/api'
import { toast } from 'vue-sonner'

const props = defineProps<{
  bid: BidRead
  currentUserId?: string
  sellerId?: string
  /** Show accept/reject/counter actions */
  showActions?: boolean
}>()

const emit = defineEmits<{
  accepted: [transactionId: string]
  rejected: []
  countered: [bid: BidRead]
}>()

const { apiFetch } = useApi()
const loading = ref<'accept' | 'reject' | null>(null)

const statusColor: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  countered: 'bg-blue-100 text-blue-800',
  expired: 'bg-gray-100 text-gray-600',
}

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('nl-NL', { dateStyle: 'medium', timeStyle: 'short' })
}

// Can the current user act on this bid?
const canAct = computed(() => {
  if (!props.showActions || props.bid.status !== 'pending') return false
  if (props.bid.bid_type === 'buyer') return props.currentUserId === props.sellerId
  if (props.bid.bid_type === 'seller') return props.currentUserId === props.bid.bidder_id
  return false
})

async function accept() {
  loading.value = 'accept'
  try {
    const tx = await apiFetch<{ id: string }>(`/api/negotiations/bids/${props.bid.id}/accept`, { method: 'POST' })
    toast.success('Bid accepted! Transaction created.')
    emit('accepted', tx.id)
  }
  catch {
    toast.error('Could not accept bid')
  }
  finally { loading.value = null }
}

async function reject() {
  loading.value = 'reject'
  try {
    await apiFetch(`/api/negotiations/bids/${props.bid.id}/reject`, { method: 'POST' })
    toast.success('Bid rejected')
    emit('rejected')
  }
  catch {
    toast.error('Could not reject bid')
  }
  finally { loading.value = null }
}
</script>

<template>
  <div class="rounded-lg border p-4 space-y-2 bg-card">
    <div class="flex items-center justify-between gap-2">
      <span class="font-semibold text-lg">{{ formatPrice(bid.amount) }}</span>
      <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusColor[bid.status]">
        {{ bid.status }}
      </span>
    </div>

    <div class="text-sm text-muted-foreground space-y-0.5">
      <p class="text-xs">{{ bid.bid_type === 'buyer' ? 'Buyer offer' : 'Seller counter' }} · {{ formatDate(bid.created_at) }}</p>
    </div>

    <div v-if="canAct" class="flex gap-2 pt-1">
      <Button size="sm" :disabled="!!loading" @click="accept">
        {{ loading === 'accept' ? 'Accepting...' : 'Accept' }}
      </Button>
      <Button variant="outline" size="sm" :disabled="!!loading" @click="emit('countered', bid)">
        Counter
      </Button>
      <Button variant="destructive" size="sm" :disabled="!!loading" @click="reject">
        {{ loading === 'reject' ? 'Rejecting...' : 'Reject' }}
      </Button>
    </div>
  </div>
</template>
