<template>
  <div class="rounded-2xl p-6 shadow-md flex flex-col gap-2" :class="bgColor">
    <div class="flex items-center gap-2">
      <span class="text-2xl">{{ icon }}</span>
      <span class="text-sm font-medium text-gray-500">{{ label }}</span>
    </div>
    <div class="text-4xl font-bold" :class="textColor">
      {{ value !== null ? `${value}${unit}` : '---' }}
    </div>
    <div class="text-xs text-gray-400">{{ timestamp || 'Chưa có dữ liệu' }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: Number,
  unit: String,
  icon: String,
  timestamp: String,
  bgColor: { type: String, default: 'bg-white' },
  textColor: { type: String, default: 'text-gray-800' }
})
</script>