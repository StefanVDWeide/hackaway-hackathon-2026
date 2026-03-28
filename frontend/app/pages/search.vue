<script setup lang="ts">
import type { ListingSearchResult } from '~/types/api'

definePageMeta({ auth: false, layout: 'default' })

const route = useRoute()
const router = useRouter()
const { apiFetch } = useApi()

const query = ref((route.query.query as string) ?? '')
const results = ref<ListingSearchResult[]>([])
const loading = ref(false)
const searched = ref(false)

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  searched.value = true
  router.replace({ query: { query: query.value } })
  try {
    results.value = await apiFetch<ListingSearchResult[]>(`/api/listings/search?query=${encodeURIComponent(query.value)}`)
  }
  catch { results.value = [] }
  finally { loading.value = false }
}

onMounted(() => {
  if (query.value) doSearch()
})

watch(() => route.query.query, (val) => {
  if (val && val !== query.value) {
    query.value = val as string
    doSearch()
  }
})
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Search bar -->
    <form class="max-w-2xl mb-8" @submit.prevent="doSearch">
      <div class="flex gap-2">
        <Input v-model="query" placeholder="Search listings..." class="flex-1" />
        <Button type="submit" :disabled="loading">Search</Button>
      </div>
    </form>

    <!-- Results heading -->
    <div v-if="searched" class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold">
        Results for <span class="text-primary">"{{ query }}"</span>
      </h1>
      <span class="text-sm text-muted-foreground">{{ results.length }} found</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div v-for="i in 6" :key="i" class="space-y-2">
        <Skeleton class="aspect-[4/3] rounded-lg w-full" />
        <Skeleton class="h-4 w-3/4" />
        <Skeleton class="h-4 w-1/2" />
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="searched && results.length === 0" class="text-center py-20 text-muted-foreground">
      <p class="text-lg">No results found</p>
      <p class="text-sm mt-1">Try different keywords</p>
    </div>

    <!-- Grid -->
    <div v-else-if="results.length" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <ListingsListingCard
        v-for="r in results"
        :key="r.listing.id"
        :listing="r.listing"
        :score="r.score"
      />
    </div>

    <!-- Prompt -->
    <div v-else class="text-center py-20 text-muted-foreground">
      <p>Enter a search term above</p>
    </div>
  </div>
</template>
