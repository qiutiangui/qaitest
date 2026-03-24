import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import clickOutside from './directives/clickOutside'

import App from './App.vue'
import router from './router'
import './styles/index.css'

// 注册FontAwesome图标
import { library } from '@fortawesome/fontawesome-svg-core'
import { faGithub } from '@fortawesome/free-brands-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

library.add(faGithub)

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.component('font-awesome-icon', FontAwesomeIcon)

// 注册 click-outside 指令
app.directive('click-outside', clickOutside)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
