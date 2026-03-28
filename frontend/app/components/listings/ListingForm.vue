<script setup lang="ts">
import type { CategoryRead, Condition, ListingCreate, ListingRead } from '~/types/api'
import { toast } from 'vue-sonner'

const props = defineProps<{
  listing?: ListingRead
  categories: CategoryRead[]
  loading?: boolean
}>()

const emit = defineEmits<{
  submit: [data: ListingCreate]
}>()

const conditions: { value: Condition; label: string }[] = [
  { value: 'new', label: 'New' },
  { value: 'like_new', label: 'Like New' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
]

const title = ref(props.listing?.title ?? '')
const description = ref(props.listing?.description ?? '')
const priceEuros = ref(props.listing ? String(props.listing.price / 100) : '')
const condition = ref<Condition>(props.listing?.condition ?? 'good')
const imageUrl = ref(props.listing?.image_url ?? '')
const selectedCategoryIds = ref<string[]>(props.listing?.categories.map(c => c.id) ?? [])

function toggleCategory(id: string) {
  const idx = selectedCategoryIds.value.indexOf(id)
  if (idx === -1) selectedCategoryIds.value.push(id)
  else selectedCategoryIds.value.splice(idx, 1)
}

function handleSubmit() {
  if (!title.value.trim() || !description.value.trim() || !priceEuros.value || !condition.value) {
    toast.error('Please fill in all required fields')
    return
  }
  const priceCents = Math.round(parseFloat(priceEuros.value) * 100)
  if (isNaN(priceCents) || priceCents <= 0) {
    toast.error('Please enter a valid price')
    return
  }
  emit('submit', {
    title: title.value.trim(),
    description: description.value.trim(),
    price: priceCents,
    condition: condition.value,
    image_url: imageUrl.value.trim() || null,
    category_ids: selectedCategoryIds.value,
  })
}
</script>

<template>
  <form class="space-y-5" @submit.prevent="handleSubmit">
    <!-- Title -->
    <div class="space-y-1.5">
      <Label for="title">Title <span class="text-destructive">*</span></Label>
      <Input id="title" v-model="title" placeholder="What are you selling?" maxlength="255" required />
    </div>

    <!-- Description -->
    <div class="space-y-1.5">
      <Label for="description">Description <span class="text-destructive">*</span></Label>
      <Textarea
        id="description"
        v-model="description"
        placeholder="Describe your item — condition details, history, dimensions..."
        rows="5"
        required
      />
    </div>

    <!-- Price + Condition -->
    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-1.5">
        <Label for="price">Price (€) <span class="text-destructive">*</span></Label>
        <Input
          id="price"
          v-model="priceEuros"
          type="number"
          min="0.01"
          step="0.01"
          placeholder="0.00"
          required
        />
      </div>
      <div class="space-y-1.5">
        <Label for="condition">Condition <span class="text-destructive">*</span></Label>
        <Select v-model="condition">
          <SelectTrigger id="condition">
            <SelectValue placeholder="Select condition" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="c in conditions" :key="c.value" :value="c.value">
              {{ c.label }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>

    <!-- Image URL -->
    <div class="space-y-1.5">
      <Label for="image">Image URL</Label>
      <Input id="image" v-model="imageUrl" type="url" placeholder="https://..." />
    </div>

    <!-- Categories -->
    <div class="space-y-1.5">
      <Label>Categories</Label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="cat in categories"
          :key="cat.id"
          type="button"
          class="px-3 py-1 rounded-full text-sm border transition-colors"
          :class="selectedCategoryIds.includes(cat.id)
            ? 'bg-primary text-primary-foreground border-primary'
            : 'border-border hover:bg-accent'"
          @click="toggleCategory(cat.id)"
        >
          {{ cat.name }}
        </button>
      </div>
    </div>

    <Button type="submit" :disabled="loading" class="w-full">
      {{ loading ? 'Saving...' : (listing ? 'Update Listing' : 'Create Listing') }}
    </Button>
  </form>
</template>
