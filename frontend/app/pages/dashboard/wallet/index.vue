<script setup lang="ts">
import type { TransactionRead, WalletRead } from '~/types/api'

definePageMeta({ auth: true, layout: 'dashboard' })

const { apiFetch } = useApi()
const { data } = useAuth()

const wallet = ref<WalletRead | null>(null)
const transactions = ref<TransactionRead[]>([])
const loading = ref(true)

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('nl-NL', { dateStyle: 'medium' })
}

const statusColor: Record<string, string> = {
  pending_escrow: 'bg-yellow-100 text-yellow-800',
  escrowed: 'bg-blue-100 text-blue-800',
  released: 'bg-green-100 text-green-800',
  refunded: 'bg-gray-100 text-gray-600',
  disputed: 'bg-red-100 text-red-800',
}

onMounted(async () => {
  const [w, t] = await Promise.allSettled([
    apiFetch<WalletRead>('/api/transactions/wallet'),
    apiFetch<TransactionRead[]>('/api/transactions/?limit=50'),
  ])
  if (w.status === 'fulfilled') wallet.value = w.value
  if (t.status === 'fulfilled') transactions.value = t.value
  loading.value = false
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">Wallet</h1>

    <div v-if="loading">
      <Skeleton class="h-32 rounded-lg w-full" />
    </div>

    <template v-else>
      <!-- Balance cards -->
      <WalletWalletCard v-if="wallet" :wallet="wallet" />
      <Card v-else>
        <CardContent class="pt-6 text-muted-foreground text-sm">No wallet found</CardContent>
      </Card>

      <!-- Transaction history -->
      <div>
        <h2 class="text-lg font-semibold mb-4">Transaction History</h2>

        <div v-if="transactions.length === 0" class="text-center py-12 text-muted-foreground border rounded-lg">
          No transactions yet
        </div>

        <div v-else class="border rounded-lg overflow-hidden divide-y">
          <NuxtLink
            v-for="tx in transactions"
            :key="tx.id"
            :to="`/dashboard/transactions/${tx.id}`"
            class="flex items-center gap-4 px-4 py-4 hover:bg-muted/50 transition-colors"
          >
            <div class="flex-1 min-w-0">
              <p class="font-medium">{{ formatPrice(tx.amount) }}</p>
              <p class="text-xs text-muted-foreground mt-0.5">
                {{ tx.buyer_id === data?.id ? 'Purchase' : 'Sale' }} · {{ formatDate(tx.created_at) }}
              </p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="statusColor[tx.status]">
                {{ tx.status.replace('_', ' ') }}
              </span>
              <span class="text-muted-foreground text-xs">→</span>
            </div>
          </NuxtLink>
        </div>
      </div>
    </template>
  </div>
</template>
