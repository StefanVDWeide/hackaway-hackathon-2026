<script setup lang="ts">
import type { TransactionRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: true, layout: 'dashboard' })

const route = useRoute()
const { apiFetch } = useApi()
const { data } = useAuth()

const tx = ref<TransactionRead | null>(null)
const loading = ref(true)
const actionLoading = ref<string | null>(null)

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleString('nl-NL', { dateStyle: 'medium', timeStyle: 'short' })
}

const statusSteps = ['pending_escrow', 'escrowed', 'released']

const currentStep = computed(() => {
  if (!tx.value) return 0
  const idx = statusSteps.indexOf(tx.value.status)
  return idx === -1 ? 0 : idx
})

const isBuyer = computed(() => data.value?.id === tx.value?.buyer_id)

onMounted(async () => {
  try {
    tx.value = await apiFetch<TransactionRead>(`/api/transactions/${route.params.id}`)
  }
  catch { toast.error('Transaction not found') }
  finally { loading.value = false }
})

async function doAction(action: 'escrow' | 'release' | 'dispute') {
  actionLoading.value = action
  try {
    tx.value = await apiFetch<TransactionRead>(`/api/transactions/${route.params.id}/${action}`, { method: 'POST' })
    toast.success(`Transaction ${action === 'escrow' ? 'funded' : action === 'release' ? 'completed' : 'disputed'}!`)
  }
  catch (e: unknown) {
    const detail = (e as { data?: { detail?: string } })?.data?.detail
    toast.error(detail ?? `Could not ${action}`)
  }
  finally { actionLoading.value = null }
}
</script>

<template>
  <div class="max-w-lg space-y-6">
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="sm" as-child>
        <NuxtLink to="/dashboard/wallet">← Wallet</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Transaction</h1>
    </div>

    <Skeleton v-if="loading" class="h-64 rounded-lg" />

    <template v-else-if="tx">
      <!-- Status stepper -->
      <Card>
        <CardContent class="pt-6">
          <div class="flex items-center gap-2">
            <template v-for="(step, i) in statusSteps" :key="step">
              <div
                class="flex flex-col items-center gap-1"
                :class="i <= currentStep ? 'text-primary' : 'text-muted-foreground'"
              >
                <div
                  class="h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold border-2"
                  :class="i <= currentStep ? 'border-primary bg-primary/10' : 'border-muted'"
                >
                  {{ i + 1 }}
                </div>
                <span class="text-xs capitalize hidden sm:block">{{ step.replace('_', ' ') }}</span>
              </div>
              <div v-if="i < statusSteps.length - 1" class="flex-1 h-0.5" :class="i < currentStep ? 'bg-primary' : 'bg-muted'" />
            </template>
          </div>

          <!-- Disputed / Refunded banner -->
          <div v-if="tx.status === 'disputed'" class="mt-4 rounded-md bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-800">
            This transaction is under dispute
          </div>
          <div v-if="tx.status === 'refunded'" class="mt-4 rounded-md bg-gray-50 border px-4 py-2 text-sm text-muted-foreground">
            This transaction was refunded
          </div>
        </CardContent>
      </Card>

      <!-- Details -->
      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Amount</span>
            <span class="font-semibold">{{ formatPrice(tx.amount) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Role</span>
            <span>{{ isBuyer ? 'Buyer' : 'Seller' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Pickup at</span>
            <span>{{ formatDate(tx.pickup_at) }}</span>
          </div>
          <Separator class="my-2" />
          <div class="flex justify-between">
            <span class="text-muted-foreground">Escrowed</span>
            <span>{{ formatDate(tx.escrowed_at) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Picked up</span>
            <span>{{ formatDate(tx.picked_up_at) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Released</span>
            <span>{{ formatDate(tx.released_at) }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Actions -->
      <div class="space-y-2">
        <!-- Buyer: fund escrow -->
        <Button
          v-if="isBuyer && tx.status === 'pending_escrow'"
          class="w-full"
          :disabled="!!actionLoading"
          @click="doAction('escrow')"
        >
          {{ actionLoading === 'escrow' ? 'Processing...' : `Fund Escrow (${formatPrice(tx.amount)})` }}
        </Button>

        <!-- Buyer: confirm pickup & release -->
        <Button
          v-if="isBuyer && tx.status === 'escrowed'"
          class="w-full"
          :disabled="!!actionLoading"
          @click="doAction('release')"
        >
          {{ actionLoading === 'release' ? 'Confirming...' : 'Confirm Pickup & Release Payment' }}
        </Button>

        <!-- Either: dispute -->
        <Button
          v-if="tx.status === 'escrowed'"
          variant="destructive"
          class="w-full"
          :disabled="!!actionLoading"
          @click="doAction('dispute')"
        >
          {{ actionLoading === 'dispute' ? 'Filing dispute...' : 'File Dispute' }}
        </Button>
      </div>
    </template>
  </div>
</template>
