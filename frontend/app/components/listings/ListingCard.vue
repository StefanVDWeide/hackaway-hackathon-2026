<script setup lang="ts">
import type { ListingRead } from '~/types/api'

const props = defineProps<{
  listing: ListingRead
  score?: number
}>()

const conditionLabel: Record<string, string> = {
  new: 'New',
  like_new: 'Like New',
  good: 'Good',
  fair: 'Fair',
  poor: 'Poor',
}

const conditionVariant: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  new: 'default',
  like_new: 'default',
  good: 'secondary',
  fair: 'secondary',
  poor: 'outline',
}

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
</script>

<template>
  <NuxtLink :to="`/listings/${listing.id}`" class="block group">
    <Card class="overflow-hidden transition-shadow hover:shadow-md h-full flex flex-col">
      <!-- Image -->
      <div class="aspect-[4/3] bg-muted overflow-hidden">
        <img
          v-if="listing.image_url"
          :src="listing.image_url"
          :alt="listing.title"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        >
        <div v-else class="w-full h-full flex items-center justify-center text-muted-foreground">
          <svg class="h-12 w-12 opacity-30" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect width="18" height="18" x="3" y="3" rx="2" /><circle cx="9" cy="9" r="2" /><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
          </svg>
        </div>
      </div>

      <CardContent class="p-3 flex flex-col gap-1 flex-1">
        <div class="flex items-start justify-between gap-2">
          <p class="font-semibold text-sm line-clamp-2 leading-snug flex-1">{{ listing.title }}</p>
          <Badge :variant="conditionVariant[listing.condition]" class="shrink-0 text-xs">
            {{ conditionLabel[listing.condition] }}
          </Badge>
        </div>

        <p class="text-lg font-bold text-primary">{{ formatPrice(listing.price) }}</p>

        <div class="flex items-center justify-between mt-auto pt-1">
          <span class="text-xs text-muted-foreground">{{ listing.seller_display_name }}</span>
          <span class="text-xs text-muted-foreground">{{ timeAgo(listing.created_at) }}</span>
        </div>

        <!-- Categories -->
        <div v-if="listing.categories.length" class="flex flex-wrap gap-1">
          <Badge
            v-for="cat in listing.categories"
            :key="cat.id"
            variant="outline"
            class="text-xs px-1.5 py-0"
          >
            {{ cat.name }}
          </Badge>
        </div>
      </CardContent>
    </Card>
  </NuxtLink>
</template>
