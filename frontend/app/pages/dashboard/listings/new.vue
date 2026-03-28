<script setup lang="ts">
import type { CategoryRead, ListingCreate, ListingRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: true, layout: 'dashboard' })

const router = useRouter()
const { apiFetch } = useApi()
const categories = ref<CategoryRead[]>([])
const loading = ref(false)
const publishAfterCreate = ref(true)

onMounted(async () => {
  categories.value = await apiFetch<CategoryRead[]>('/api/categories/')
})

async function handleSubmit(data: ListingCreate) {
  loading.value = true
  try {
    const listing = await apiFetch<ListingRead>('/api/listings/', { method: 'POST', body: data })
    if (publishAfterCreate.value) {
      await apiFetch(`/api/listings/${listing.id}/publish`, { method: 'POST' })
      toast.success('Listing created and published!')
    }
    else {
      toast.success('Listing saved as draft')
    }
    router.push('/dashboard/listings')
  }
  catch (e: unknown) {
    const detail = (e as { data?: { detail?: string } })?.data?.detail
    toast.error(detail ?? 'Could not create listing')
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Create Listing</h1>
      <p class="text-muted-foreground text-sm mt-1">Fill in the details about your item</p>
    </div>

    <Card>
      <CardContent class="pt-6">
        <ListingsListingForm :categories="categories" :loading="loading" @submit="handleSubmit" />
      </CardContent>
    </Card>

    <!-- Publish toggle -->
    <div class="flex items-center gap-3 px-1">
      <button
        type="button"
        class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
        :class="publishAfterCreate ? 'bg-primary' : 'bg-muted'"
        @click="publishAfterCreate = !publishAfterCreate"
      >
        <span
          class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow"
          :class="publishAfterCreate ? 'translate-x-4' : 'translate-x-0.5'"
        />
      </button>
      <label class="text-sm cursor-pointer" @click="publishAfterCreate = !publishAfterCreate">
        Publish immediately after creating
      </label>
    </div>
  </div>
</template>
