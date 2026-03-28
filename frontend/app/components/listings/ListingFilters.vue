<script setup lang="ts">
import type { CategoryRead, Condition } from "~/types/api";

const props = defineProps<{
  categories: CategoryRead[];
}>();

const emit = defineEmits<{
  change: [
    filters: {
      category_slug?: string;
      condition?: Condition;
      min_price?: number;
      max_price?: number;
      latitude?: number;
      longitude?: number;
      radius_km?: number;
    },
  ];
}>();

const selectedCategory = ref("__all__");
const selectedCondition = ref("__all__");
const minPrice = ref("");
const maxPrice = ref("");
const useLocation = ref(false);
const latitude = ref<number | null>(null);
const longitude = ref<number | null>(null);
const radiusKm = ref("25");
const geoError = ref("");
const geoLoading = ref(false);

const conditions: { value: Condition; label: string }[] = [
  { value: "new", label: "New" },
  { value: "like_new", label: "Like New" },
  { value: "good", label: "Good" },
  { value: "fair", label: "Fair" },
  { value: "poor", label: "Poor" },
];

watch(useLocation, async (val) => {
  if (val && latitude.value === null) {
    geoLoading.value = true;
    geoError.value = "";
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });
      latitude.value = pos.coords.latitude;
      longitude.value = pos.coords.longitude;
    } catch {
      geoError.value = "Could not get location. Please allow access.";
      useLocation.value = false;
    } finally {
      geoLoading.value = false;
    }
  }
  emitChange();
});

function emitChange() {
  emit("change", {
    category_slug:
      selectedCategory.value === "__all__" ? undefined : selectedCategory.value,
    condition:
      selectedCondition.value === "__all__"
        ? undefined
        : (selectedCondition.value as Condition),
    min_price: minPrice.value
      ? Math.round(parseFloat(minPrice.value) * 100)
      : undefined,
    max_price: maxPrice.value
      ? Math.round(parseFloat(maxPrice.value) * 100)
      : undefined,
    latitude:
      useLocation.value && latitude.value !== null ? latitude.value : undefined,
    longitude:
      useLocation.value && longitude.value !== null
        ? longitude.value
        : undefined,
    radius_km: useLocation.value ? Number(radiusKm.value) : undefined,
  });
}

function reset() {
  selectedCategory.value = "__all__";
  selectedCondition.value = "__all__";
  minPrice.value = "";
  maxPrice.value = "";
  useLocation.value = false;
  radiusKm.value = "25";
  emitChange();
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-sm">Filters</h3>
      <Button variant="ghost" size="sm" class="h-7 text-xs" @click="reset"
        >Reset</Button
      >
    </div>

    <!-- Category -->
    <div class="space-y-1.5">
      <Label class="text-xs text-muted-foreground uppercase tracking-wider"
        >Category</Label
      >
      <Select v-model="selectedCategory" @update:model-value="emitChange">
        <SelectTrigger class="h-9">
          <SelectValue placeholder="All categories" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">All categories</SelectItem>
          <SelectItem v-for="cat in categories" :key="cat.id" :value="cat.slug">
            {{ cat.name }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Condition -->
    <div class="space-y-1.5">
      <Label class="text-xs text-muted-foreground uppercase tracking-wider"
        >Condition</Label
      >
      <Select v-model="selectedCondition" @update:model-value="emitChange">
        <SelectTrigger class="h-9">
          <SelectValue placeholder="Any condition" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__all__">Any condition</SelectItem>
          <SelectItem v-for="c in conditions" :key="c.value" :value="c.value">
            {{ c.label }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Price range -->
    <div class="space-y-1.5">
      <Label class="text-xs text-muted-foreground uppercase tracking-wider"
        >Price range (€)</Label
      >
      <div class="flex items-center gap-2">
        <Input
          v-model="minPrice"
          placeholder="Min"
          type="number"
          min="0"
          step="0.01"
          class="h-9"
          @change="emitChange"
        />
        <span class="text-muted-foreground text-sm">–</span>
        <Input
          v-model="maxPrice"
          placeholder="Max"
          type="number"
          min="0"
          step="0.01"
          class="h-9"
          @change="emitChange"
        />
      </div>
    </div>

    <Separator />
  </div>
</template>
