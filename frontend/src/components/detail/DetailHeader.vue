<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

interface Props {
  title: string
  subtitle?: string
  backTo?: string
  breadcrumb?: string[]
}

const props = defineProps<Props>()
const router = useRouter()

function handleBack() {
  if (props.backTo) {
    router.push(props.backTo)
  } else {
    router.back()
  }
}
</script>

<template>
  <div class="detail-header mb-6">
    <!-- Breadcrumb Navigation -->
    <div class="flex items-center gap-3 mb-4">
      <button 
        class="flex items-center gap-1 text-text-secondary hover:text-primary transition-colors group"
        @click="handleBack"
      >
        <ArrowLeft class="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span class="text-sm">返回列表</span>
      </button>
      
      <div v-if="breadcrumb && breadcrumb.length > 0" class="flex items-center gap-2">
        <div class="h-4 w-px bg-gray-200" />
        <div class="flex items-center gap-2 text-sm text-text-secondary">
          <span 
            v-for="(item, index) in breadcrumb" 
            :key="index"
            class="flex items-center gap-2"
          >
            <span>{{ item }}</span>
            <span v-if="index < breadcrumb.length - 1" class="text-gray-300">/</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Header Content -->
    <div class="bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl shadow-lg overflow-hidden">
      <div class="px-6 py-3 flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <h1 class="text-2xl font-bold text-white mb-2 truncate">
            {{ title }}
          </h1>
          <p v-if="subtitle" class="text-sm text-white/80">
            {{ subtitle }}
          </p>
        </div>
        
        <div class="flex items-center gap-2 flex-shrink-0">
          <slot name="actions" />
        </div>
      </div>
    </div>
  </div>
</template>
