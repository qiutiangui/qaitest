import type { Directive, DirectiveBinding } from 'vue'

interface ClickOutsideElement extends HTMLElement {
  _clickOutsideHandler?: (event: MouseEvent) => void
}

const clickOutside: Directive = {
  beforeMount(el: ClickOutsideElement, binding: DirectiveBinding) {
    el._clickOutsideHandler = (event: MouseEvent) => {
      const target = event.target as Node
      if (!(el === target || el.contains(target))) {
        binding.value(event)
      }
    }
    document.addEventListener('click', el._clickOutsideHandler)
  },
  unmounted(el: ClickOutsideElement) {
    if (el._clickOutsideHandler) {
      document.removeEventListener('click', el._clickOutsideHandler)
      delete el._clickOutsideHandler
    }
  },
}

export default clickOutside
