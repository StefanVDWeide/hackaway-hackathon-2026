<script setup lang="ts">
import type { ConversationSummary, ListingRead } from '~/types/api'

definePageMeta({ auth: true, layout: 'dashboard' })

const { apiFetch } = useApi()
const { data } = useAuth()

const conversations = ref<ConversationSummary[]>([])
const listingMap = ref<Record<string, ListingRead>>({})
const loading = ref(true)

onMounted(async () => {
  conversations.value = await apiFetch<ConversationSummary[]>('/api/negotiations/conversations?limit=100')

  // Fetch listing details for each conversation
  const ids = [...new Set(conversations.value.map(c => c.listing_id))]
  await Promise.all(ids.map(async (id) => {
    try {
      listingMap.value[id] = await apiFetch<ListingRead>(`/api/listings/${id}`)
    }
    catch { /* ignore */ }
  }))
  loading.value = false
})

function timeAgo(d: string) {
  const diff = Date.now() - new Date(d).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">Conversations</h1>

    <div v-if="loading" class="space-y-2">
      <Skeleton v-for="i in 4" :key="i" class="h-20 rounded-lg" />
    </div>

    <div v-else-if="conversations.length === 0" class="text-center py-16 text-muted-foreground">
      <p>No conversations yet</p>
      <p class="text-sm mt-1">Conversations start when someone makes an offer on your listing</p>
    </div>

    <div v-else class="border rounded-lg overflow-hidden divide-y">
      <NuxtLink
        v-for="conv in conversations"
        :key="conv.id"
        :to="`/dashboard/negotiations/${conv.id}`"
        class="flex items-center gap-4 px-4 py-4 hover:bg-muted/50 transition-colors"
      >
        <!-- Listing image -->
        <div class="h-12 w-12 rounded-md bg-muted overflow-hidden shrink-0">
          <img
            v-if="listingMap[conv.listing_id]?.image_url"
            :src="listingMap[conv.listing_id].image_url!"
            :alt="listingMap[conv.listing_id]?.title"
            class="w-full h-full object-cover"
          >
        </div>

        <div class="flex-1 min-w-0">
          <p class="font-medium line-clamp-1">
            {{ listingMap[conv.listing_id]?.title ?? 'Listing' }}
          </p>
          <p class="text-xs text-muted-foreground mt-0.5">
            {{ conv.buyer_id === data?.id ? 'You are the buyer' : 'You are the seller' }}
          </p>
        </div>

        <span class="text-xs text-muted-foreground shrink-0">{{ timeAgo(conv.created_at) }}</span>
      </NuxtLink>
    </div>
  </div>
</template>
