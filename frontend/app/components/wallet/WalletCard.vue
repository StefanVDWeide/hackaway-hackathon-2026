<script setup lang="ts">
import type { WalletRead } from '~/types/api'

defineProps<{ wallet: WalletRead }>()

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}
</script>

<template>
  <div class="grid grid-cols-2 gap-4">
    <Card>
      <CardHeader class="pb-2">
        <CardDescription>Available Balance</CardDescription>
      </CardHeader>
      <CardContent>
        <p class="text-3xl font-bold text-primary">{{ formatPrice(wallet.balance) }}</p>
      </CardContent>
    </Card>
    <Card>
      <CardHeader class="pb-2">
        <CardDescription>Held in Escrow</CardDescription>
      </CardHeader>
      <CardContent>
        <p class="text-3xl font-bold text-muted-foreground">{{ formatPrice(wallet.held_balance) }}</p>
      </CardContent>
    </Card>
  </div>
</template>
