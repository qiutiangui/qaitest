<script setup lang="ts">
interface Step {
  step_number: number
  description: string
  expected_result?: string
}

interface Props {
  steps: Step[]
}

defineProps<Props>()
</script>

<template>
  <div class="step-flow">
    <div 
      v-for="(step, index) in steps" 
      :key="step.step_number"
      class="step-item flex gap-4 mb-6 last:mb-0"
    >
      <!-- Step Number Badge -->
      <div class="flex-shrink-0">
        <div class="relative">
          <!-- Circle Badge -->
          <div 
            class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-md"
            :class="[
              index === 0 ? 'bg-gradient-to-br from-blue-500 to-blue-600' :
              index === steps.length - 1 ? 'bg-gradient-to-br from-green-500 to-green-600' :
              'bg-gradient-to-br from-cyan-500 to-cyan-600'
            ]"
          >
            {{ step.step_number }}
          </div>
          
          <!-- Connection Line -->
          <div 
            v-if="index < steps.length - 1"
            class="absolute top-10 left-1/2 -translate-x-1/2 w-0.5 h-6 bg-gradient-to-b from-gray-300 to-gray-200"
          />
        </div>
      </div>

      <!-- Step Content -->
      <div class="flex-1 min-w-0">
        <div class="bg-white rounded-lg border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow">
          <!-- Step Description -->
          <div class="text-text-primary font-medium mb-2">
            {{ step.description }}
          </div>
          
          <!-- Expected Result -->
          <div 
            v-if="step.expected_result"
            class="bg-blue-50 border-l-4 border-primary rounded px-3 py-2 mt-3"
          >
            <div class="flex items-start gap-2">
              <span class="text-xs font-semibold text-primary uppercase tracking-wide flex-shrink-0 mt-0.5">
                预期结果
              </span>
              <span class="text-sm text-text-secondary leading-relaxed">
                {{ step.expected_result }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div 
      v-if="!steps || steps.length === 0"
      class="text-center py-8 text-text-secondary"
    >
      暂无测试步骤
    </div>
  </div>
</template>

<style scoped>
.step-flow {
  position: relative;
}
</style>
