<script setup lang="ts">
import { ref, type Component } from 'vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

interface Props {
  title?: string
  icon?: Component
  collapsible?: boolean
  defaultCollapsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  collapsible: false,
  defaultCollapsed: false
})

const isCollapsed = ref(props.defaultCollapsed)

function toggleCollapse() {
  if (props.collapsible) {
    isCollapsed.value = !isCollapsed.value
  }
}
</script>

<template>
  <div class="detail-card bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-200">
    <!-- Card Header -->
    <div 
      v-if="title" 
      :class="[
        'px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-gray-50 to-white',
        collapsible ? 'cursor-pointer select-none' : ''
      ]"
      @click="toggleCollapse"
    >
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <component 
            v-if="icon" 
            :is="icon" 
            class="w-4 h-4 text-white" 
          />
        </div>
        <h3 class="text-lg font-semibold text-text-primary">{{ title }}</h3>
      </div>
      <button v-if="collapsible" class="text-text-secondary hover:text-primary transition-colors">
        <ChevronDown v-if="!isCollapsed" class="w-5 h-5" />
        <ChevronUp v-else class="w-5 h-5" />
      </button>
    </div>

    <!-- Card Content -->
    <div 
      v-show="!isCollapsed"
      :class="[
        'p-6',
        !title && 'pt-6'
      ]"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.detail-card {
  transition: all 0.3s ease;
}

.detail-card:hover {
  transform: translateY(-2px);
}
</style>
