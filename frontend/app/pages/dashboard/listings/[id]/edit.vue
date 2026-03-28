<script setup lang="ts">
import type { CategoryRead, ListingCreate, ListingRead } from '~/types/api'
import { toast } from 'vue-sonner'

definePageMeta({ auth: true, layout: 'dashboard' })

const route = useRoute()
const router = useRouter()
const { apiFetch } = useApi()

const listing = ref<ListingRead | null>(null)
const categories = ref<CategoryRead[]>([])
const loading = ref(true)
const saving = ref(false)

onMounted(async () => {
  const [l, c] = await Promise.all([
    apiFetch<ListingRead>(`/api/listings/${route.params.id}`),
    apiFetch<CategoryRead[]>('/api/categories/'),
  ])
  listing.value = l
  categories.value = c
  loading.value = false
})

async function handleSubmit(data: ListingCreate) {
  saving.value = true
  try {
    await apiFetch(`/api/listings/${route.params.id}`, { method: 'PATCH', body: data })
    toast.success('Listing updated!')
    router.push('/dashboard/listings')
  }
  catch {
    toast.error('Could not update listing')
  }
  finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl space-y-6">
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="sm" as-child>
        <NuxtLink to="/dashboard/listings">← Back</NuxtLink>
      </Button>
      <h1 class="text-2xl font-bold">Edit Listing</h1>
    </div>

    <div v-if="loading">
      <Skeleton class="h-96 rounded-lg w-full" />
    </div>

    <Card v-else-if="listing">
      <CardContent class="pt-6">
        <ListingsListingForm
          :listing="listing"
          :categories="categories"
          :loading="saving"
          @submit="handleSubmit"
        />
      </CardContent>
    </Card>
  </div>
</template>
