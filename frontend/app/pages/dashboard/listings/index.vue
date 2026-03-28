<script setup lang="ts">
import type { ListingRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: true, layout: 'dashboard' })

const { apiFetch } = useApi()
const listings = ref<ListingRead[]>([])
const loading = ref(true)
const actionLoading = ref<string | null>(null)

function formatPrice(cents: number) {
  return new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }).format(cents / 100)
}

const statusBadge: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  draft: 'outline',
  active: 'default',
  sold: 'secondary',
  archived: 'secondary',
}

onMounted(async () => {
  await refresh()
})

async function refresh() {
  loading.value = true
  try {
    listings.value = await apiFetch<ListingRead[]>('/api/listings/me?limit=100')
  }
  finally { loading.value = false }
}

async function publish(id: string) {
  actionLoading.value = id
  try {
    await apiFetch(`/api/listings/${id}/publish`, { method: 'POST' })
    toast.success('Listing published!')
    await refresh()
  }
  catch { toast.error('Could not publish') }
  finally { actionLoading.value = null }
}

async function archive(id: string) {
  actionLoading.value = id
  try {
    await apiFetch(`/api/listings/${id}/archive`, { method: 'POST' })
    toast.success('Listing archived')
    await refresh()
  }
  catch { toast.error('Could not archive') }
  finally { actionLoading.value = null }
}

async function deleteListing(id: string) {
  if (!confirm('Delete this draft listing?')) return
  actionLoading.value = id
  try {
    await apiFetch(`/api/listings/${id}`, { method: 'DELETE' })
    toast.success('Listing deleted')
    await refresh()
  }
  catch { toast.error('Could not delete') }
  finally { actionLoading.value = null }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">My Listings</h1>
      <Button as-child size="sm">
        <NuxtLink to="/dashboard/listings/new">+ New Listing</NuxtLink>
      </Button>
    </div>

    <div v-if="loading" class="space-y-2">
      <Skeleton v-for="i in 4" :key="i" class="h-16 rounded-lg" />
    </div>

    <div v-else-if="listings.length === 0" class="text-center py-16 text-muted-foreground">
      <p>No listings yet.</p>
      <Button class="mt-4" as-child>
        <NuxtLink to="/dashboard/listings/new">Create your first listing</NuxtLink>
      </Button>
    </div>

    <div v-else class="border rounded-lg overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-muted">
          <tr>
            <th class="text-left px-4 py-3 font-medium">Title</th>
            <th class="text-left px-4 py-3 font-medium hidden md:table-cell">Price</th>
            <th class="text-left px-4 py-3 font-medium">Status</th>
            <th class="text-right px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="listing in listings" :key="listing.id" class="hover:bg-muted/50 transition-colors">
            <td class="px-4 py-3">
              <NuxtLink :to="`/listings/${listing.id}`" class="font-medium hover:text-primary line-clamp-1">
                {{ listing.title }}
              </NuxtLink>
            </td>
            <td class="px-4 py-3 text-muted-foreground hidden md:table-cell">
              {{ formatPrice(listing.price) }}
            </td>
            <td class="px-4 py-3">
              <Badge :variant="statusBadge[listing.status]" class="capitalize">{{ listing.status }}</Badge>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <!-- Edit -->
                <Button variant="ghost" size="sm" as-child>
                  <NuxtLink :to="`/dashboard/listings/${listing.id}/edit`">Edit</NuxtLink>
                </Button>
                <!-- View bids (active only) -->
                <Button v-if="listing.status === 'active'" variant="ghost" size="sm" as-child>
                  <NuxtLink :to="`/dashboard/listings/${listing.id}/bids`">Bids</NuxtLink>
                </Button>
                <!-- Publish draft -->
                <Button
                  v-if="listing.status === 'draft'"
                  size="sm"
                  :disabled="actionLoading === listing.id"
                  @click="publish(listing.id)"
                >
                  Publish
                </Button>
                <!-- Archive active -->
                <Button
                  v-if="listing.status === 'active'"
                  variant="outline"
                  size="sm"
                  :disabled="actionLoading === listing.id"
                  @click="archive(listing.id)"
                >
                  Archive
                </Button>
                <!-- Delete draft -->
                <Button
                  v-if="listing.status === 'draft'"
                  variant="destructive"
                  size="sm"
                  :disabled="actionLoading === listing.id"
                  @click="deleteListing(listing.id)"
                >
                  Delete
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
